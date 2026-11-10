"""Tests for _fix_turn, one LLM fix turn of the check loop."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflows.implement.check_loop import (
    CheckOutcome,
    _build_fix_prompt,
    _fix_turn,
)

_PROJECT = Path("/test/project")
_CL = "mcp_coder.workflows.implement.check_loop"
_FRAGMENT = "Fix the check findings below."


def _make_llm_response(text: str = "LLM response") -> dict[str, object]:
    """Create a minimal LLMResponseDict-compatible dict for mocking."""
    return {
        "version": "1.0",
        "timestamp": "2025-10-01T10:30:00",
        "text": text,
        "session_id": "test-session-id",
        "provider": "claude",
        "raw_response": {},
    }


class _Mocks:
    """Patched collaborators of _fix_turn."""

    def __init__(self, **mocks: MagicMock) -> None:
        self.prompt_llm = mocks["prompt_llm"]
        self.store_session = mocks["store_session"]
        self.blocked = mocks["blocked"]
        self.perms = mocks["perms"]
        self.declares = mocks["declares"]
        self.slots = mocks["slots"]
        self.branch = mocks["branch"]


@pytest.fixture
def mocks() -> Iterator[_Mocks]:
    with (
        patch(f"{_CL}.prompt_llm") as prompt_llm,
        patch(f"{_CL}.store_session") as store_session,
        patch(f"{_CL}.read_and_clear_blocked", return_value=None) as blocked,
        patch(f"{_CL}.llm_permissions", return_value=["mcp__x__y"]) as perms,
        patch(f"{_CL}.toolkit_declares_bash_grants", return_value=False) as declares,
        patch(f"{_CL}.resolve_prompt_slots") as slots,
        patch(f"{_CL}.get_branch_name_for_logging", return_value="feat-1") as branch,
    ):
        prompt_llm.return_value = _make_llm_response("fixed")
        yield _Mocks(
            prompt_llm=prompt_llm,
            store_session=store_session,
            blocked=blocked,
            perms=perms,
            declares=declares,
            slots=slots,
            branch=branch,
        )


def _turn(turn: int = 1) -> CheckOutcome | None:
    return _fix_turn(
        _FRAGMENT, "a.py:1: error", _PROJECT, "claude", turn, 2, None, None, None
    )


class TestSuccess:
    def test_success_without_marker_returns_none(self, mocks: _Mocks) -> None:
        assert _turn() is None

        mocks.prompt_llm.assert_called_once()
        assert mocks.prompt_llm.call_args.args[0] == (
            f"{_FRAGMENT}\n\nCheck output:\na.py:1: error"
        )
        mocks.store_session.assert_called_once()
        mocks.blocked.assert_called_once_with(_PROJECT)

    def test_session_step_name_uses_turn(self, mocks: _Mocks) -> None:
        assert _turn(3) is None

        kwargs = mocks.store_session.call_args.kwargs
        assert kwargs["step_name"] == "step_2_mypy_3"
        assert "implement_sessions" in kwargs["store_path"]

    def test_success_with_marker_returns_blocked(self, mocks: _Mocks) -> None:
        mocks.blocked.return_value = "Need the API key"

        assert _turn() == CheckOutcome("blocked", "Need the API key")

    def test_store_session_failure_is_logged(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.store_session.side_effect = OSError("disk full")

        with caplog.at_level("WARNING"):
            assert _turn() is None
        assert "disk full" in caplog.text

    def test_branch_name_forwarded(self, mocks: _Mocks) -> None:
        _turn()

        mocks.branch.assert_called_once_with(str(_PROJECT))
        assert mocks.prompt_llm.call_args.kwargs["branch_name"] == "feat-1"
        assert mocks.store_session.call_args.kwargs["branch_name"] == "feat-1"

    def test_llm_params_forwarded(self, mocks: _Mocks) -> None:
        _fix_turn(
            _FRAGMENT,
            "x",
            _PROJECT,
            "claude",
            1,
            1,
            {"A": "1"},
            "mcp.json",
            "s.json",
        )

        kwargs = mocks.prompt_llm.call_args.kwargs
        assert kwargs["provider"] == "claude"
        assert kwargs["env_vars"] == {"A": "1"}
        assert kwargs["mcp_config"] == "mcp.json"
        assert kwargs["settings_file"] == "s.json"
        assert kwargs["project_dir"] == str(_PROJECT)


class TestBashGrants:
    def test_grants_and_check_instructions_reach_prompt(self, mocks: _Mocks) -> None:
        mocks.perms.return_value = ["Bash(npm run lint)", "mcp__x__y"]
        mocks.declares.return_value = True
        mocks.slots.return_value = {"check_instructions": "Run `npm run lint`."}

        assert _turn() is None

        mocks.perms.assert_called_once_with(_PROJECT, "claude")
        mocks.slots.assert_called_once_with(
            "[check_instructions]", _PROJECT, "claude", ["Bash(npm run lint)"]
        )
        assert mocks.prompt_llm.call_args.kwargs["bash_grants"] == [
            "Bash(npm run lint)"
        ]
        assert mocks.prompt_llm.call_args.args[0] == (
            f"{_FRAGMENT}\n\nCheck output:\na.py:1: error\n\nRun `npm run lint`."
        )

    def test_no_bash_grant_toolkit_has_no_instructions(self, mocks: _Mocks) -> None:
        assert _turn() is None

        mocks.slots.assert_not_called()
        assert mocks.prompt_llm.call_args.kwargs["bash_grants"] == []


class TestFailures:
    @pytest.mark.parametrize("text", ["", "   \n"])
    def test_empty_response_is_cap(self, mocks: _Mocks, text: str) -> None:
        mocks.prompt_llm.return_value = _make_llm_response(text)

        outcome = _turn()

        assert outcome is not None
        assert outcome.status == "cap"
        assert outcome.detail.startswith("Fix turn failed:")
        mocks.blocked.assert_called()

    def test_untyped_exception_is_cap(self, mocks: _Mocks) -> None:
        mocks.prompt_llm.side_effect = RuntimeError("cli crashed")

        outcome = _turn()

        assert outcome is not None
        assert outcome.status == "cap"
        assert "cli crashed" in outcome.detail

    def test_untyped_exception_with_marker_is_blocked(self, mocks: _Mocks) -> None:
        mocks.prompt_llm.side_effect = RuntimeError("cli crashed")
        mocks.blocked.return_value = "Stuck"

        assert _turn() == CheckOutcome("blocked", "Stuck")

    @pytest.mark.parametrize("target", ["perms", "declares", "slots"])
    def test_setup_raising_is_cap_without_llm_call(
        self, mocks: _Mocks, target: str
    ) -> None:
        mocks.declares.return_value = True
        getattr(mocks, target).side_effect = RuntimeError("setup broke")

        outcome = _turn()

        assert outcome is not None
        assert outcome.status == "cap"
        assert "setup broke" in outcome.detail
        mocks.prompt_llm.assert_not_called()

    def test_timeout(self, mocks: _Mocks) -> None:
        mocks.prompt_llm.side_effect = LLMTimeoutError("timed out")

        assert _turn() == CheckOutcome("timeout", "")

    def test_mcp_unavailable(self, mocks: _Mocks) -> None:
        mocks.prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable", {"mcp-tools-py": "failed"}
        )

        assert _turn() == CheckOutcome("mcp_unavailable", "")

    @pytest.mark.parametrize(
        ("exc", "status"),
        [
            (LLMTimeoutError("timed out"), "timeout"),
            (
                McpServersUnavailableError("down", {"mcp-tools-py": "failed"}),
                "mcp_unavailable",
            ),
        ],
    )
    def test_typed_failure_keeps_status_with_marker(
        self, mocks: _Mocks, exc: Exception, status: str
    ) -> None:
        mocks.prompt_llm.side_effect = exc
        mocks.blocked.return_value = "marker text"

        assert _turn() == CheckOutcome(status, "marker text")  # type: ignore[arg-type]


class TestBuildFixPrompt:
    def test_omits_empty_instructions(self) -> None:
        assert _build_fix_prompt("F", "out", "") == "F\n\nCheck output:\nout"

    def test_appends_instructions(self) -> None:
        assert _build_fix_prompt("F", "out", "I") == "F\n\nCheck output:\nout\n\nI"
