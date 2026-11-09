from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.toolkit import ActionResult, Finding
from mcp_coder.workflows.implement.task_processing import (
    _fix_check_text,
    _run_check,
    check_and_fix_mypy,
)
from tests.workflows.implement.test_task_processing import _make_llm_response

_PROJECT = Path("/test/project")
_FIX_CHECK = "Fix the check findings below."
_TP = "mcp_coder.workflows.implement.task_processing"


def _findings(fix_text: str = "", summary: str = "1 error") -> ActionResult:
    return ActionResult(
        status="findings",
        summary=summary,
        findings=[Finding(key="k", message="m")],
        fix_text=fix_text,
    )


class TestRunCheck:
    """Test _run_check over a toolkit binding."""

    @pytest.fixture
    def mock_run_binding(self) -> Iterator[MagicMock]:
        with (
            patch("mcp_coder.workflows.implement.task_processing.load_toolkit"),
            patch(
                "mcp_coder.workflows.implement.task_processing.run_binding"
            ) as mock_run,
        ):
            yield mock_run

    def test_all_ok_returns_none(self, mock_run_binding: MagicMock) -> None:
        mock_run_binding.return_value = [
            ("check@quick", ActionResult(status="ok", summary="clean"))
        ]

        assert _run_check(_PROJECT, "implement_final") is None
        assert mock_run_binding.call_args.args[1:] == (_PROJECT, "implement_final")

    def test_skipped_returns_none_and_logs(
        self, mock_run_binding: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        mock_run_binding.return_value = [
            ("check@quick", ActionResult(status="skipped", summary="no files"))
        ]

        with caplog.at_level("INFO"):
            assert _run_check(_PROJECT, "implement_final") is None
        assert "check@quick skipped: no files" in caplog.text

    def test_findings_return_fix_text(self, mock_run_binding: MagicMock) -> None:
        mock_run_binding.return_value = [
            ("check@quick", _findings(fix_text="a.py:1: error ..."))
        ]

        assert _run_check(_PROJECT, "implement_final") == "a.py:1: error ..."

    def test_two_findings_joined_with_blank_line(
        self, mock_run_binding: MagicMock
    ) -> None:
        mock_run_binding.return_value = [
            ("check@quick", _findings(fix_text="first")),
            ("test@quick", _findings(fix_text="second")),
        ]

        assert _run_check(_PROJECT, "implement_final") == "first\n\nsecond"

    def test_empty_fix_text_falls_back_to_summary(
        self, mock_run_binding: MagicMock
    ) -> None:
        mock_run_binding.return_value = [
            ("check@quick", _findings(summary="3 type errors"))
        ]

        assert _run_check(_PROJECT, "implement_final") == "3 type errors"

    def test_error_result_raises(self, mock_run_binding: MagicMock) -> None:
        mock_run_binding.return_value = [
            ("check@quick", ActionResult(status="error", summary="mypy crashed"))
        ]

        with pytest.raises(RuntimeError, match="check@quick: mypy crashed"):
            _run_check(_PROJECT, "implement_final")

    def test_load_toolkit_error_raises_runtime_error(self) -> None:
        with patch(
            "mcp_coder.workflows.implement.task_processing.load_toolkit",
            side_effect=ValueError("bad config"),
        ):
            with pytest.raises(RuntimeError, match="bad config"):
                _run_check(_PROJECT, "implement_final")


class TestCheckAndFixMypy:
    """Test check_and_fix_mypy function."""

    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_no_errors(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check when no errors found."""
        mock_mypy_check.return_value = None  # No errors

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        mock_mypy_check.assert_called_once_with(
            Path("/test/project"), "implement_final"
        )

    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_forwards_entry(self, mock_check: MagicMock) -> None:
        """The binding entry reaches _run_check."""
        mock_check.return_value = None

        check_and_fix_mypy(Path("/test/project"), 1, "claude", entry="implement_task")

        mock_check.assert_called_once_with(Path("/test/project"), "implement_task")

    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_run_error_returns_false(
        self, mock_check: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A RuntimeError from _run_check is logged and becomes False."""
        mock_check.side_effect = RuntimeError("Failed to run checks: boom")

        with caplog.at_level("ERROR"):
            result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False
        assert "Failed to run checks: boom" in caplog.text

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing._fix_check_text")
    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_fixes_errors(
        self,
        mock_mypy_check: MagicMock,
        mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check fixes errors successfully."""
        # First call returns errors, second call returns None (fixed)
        mock_mypy_check.side_effect = ["mypy error output", None]
        mock_fix_check.return_value = _FIX_CHECK
        mock_prompt_llm.return_value = _make_llm_response("Fixed the errors")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is True
        assert mock_mypy_check.call_count == 2
        mock_fix_check.assert_called_once()
        mock_prompt_llm.assert_called_once()
        # Verify store_session called with correct step_name
        mock_store_session.assert_called_once()
        call_kwargs = mock_store_session.call_args
        assert call_kwargs.kwargs.get("step_name") == "step_1_mypy_1" or (
            len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "step_1_mypy_1"
        )
        assert "implement_sessions" in (
            call_kwargs.kwargs.get("store_path", "")
            or (call_kwargs.args[2] if len(call_kwargs.args) >= 3 else "")
        )

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing._fix_check_text")
    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_max_attempts(
        self,
        mock_mypy_check: MagicMock,
        mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
        mock_store_session: MagicMock,
    ) -> None:
        """Test mypy check stops after max identical attempts."""
        # Always return same error (identical outputs)
        mock_mypy_check.return_value = "same mypy error"
        mock_fix_check.return_value = _FIX_CHECK
        mock_prompt_llm.return_value = _make_llm_response("Attempted fix")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False
        # Should attempt fixes until max identical attempts reached
        assert mock_prompt_llm.call_count == 3  # max_identical_attempts
        # store_session should be called once per attempt
        assert mock_store_session.call_count == 3

    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_exception(self, mock_mypy_check: MagicMock) -> None:
        """Test mypy check handles exceptions."""
        mock_mypy_check.side_effect = Exception("Mypy error")

        result = check_and_fix_mypy(Path("/test/project"), 1, "claude")

        assert result is False

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing._fix_check_text")
    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_timeout_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """Fixes the pre-existing hole: a fix-up LLMTimeoutError must propagate.

        Previously the broad handler swallowed it into a False result, hiding the
        timeout from the caller. It must now reach the caller for categorization.
        """
        from mcp_coder.llm.interface import LLMTimeoutError

        mock_mypy_check.return_value = "mypy error output"
        mock_fix_check.return_value = _FIX_CHECK
        mock_prompt_llm.side_effect = LLMTimeoutError("timed out")

        with pytest.raises(LLMTimeoutError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")

    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing._fix_check_text")
    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    def test_check_and_fix_mypy_mcp_unavailable_propagates(
        self,
        mock_mypy_check: MagicMock,
        mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        """A fix-up McpServersUnavailableError must propagate, not become False."""
        from mcp_coder.llm.providers.claude.claude_code_cli import (
            McpServersUnavailableError,
        )

        mock_mypy_check.return_value = "mypy error output"
        mock_fix_check.return_value = _FIX_CHECK
        mock_prompt_llm.side_effect = McpServersUnavailableError(
            "MCP servers unavailable",
            {"mcp-tools-py": "failed"},
        )

        with pytest.raises(McpServersUnavailableError):
            check_and_fix_mypy(Path("/test/project"), 1, "claude")


class TestCheckAndFixMypyBashGrants:
    """The mypy fix call passes the toolkit's Bash grants."""

    @patch("mcp_coder.workflows.implement.task_processing.store_session")
    @patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
    @patch("mcp_coder.workflows.implement.task_processing._fix_check_text")
    @patch("mcp_coder.workflows.implement.task_processing._run_check")
    @patch(
        "mcp_coder.workflows.implement.task_processing.toolkit_declares_bash_grants",
        return_value=False,
    )
    @patch(
        "mcp_coder.workflows.implement.task_processing.llm_permissions",
        return_value=["Bash(npm run lint)", "mcp__x__y"],
    )
    def test_fix_call_passes_bash_grants(
        self,
        mock_perms: MagicMock,
        _mock_declares: MagicMock,
        mock_check: MagicMock,
        mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store_session: MagicMock,
    ) -> None:
        mock_check.side_effect = ["error output", None]
        mock_fix_check.return_value = _FIX_CHECK
        mock_prompt_llm.return_value = _make_llm_response("fixed")

        assert check_and_fix_mypy(_PROJECT, 1, "claude") is True

        mock_perms.assert_called_with(_PROJECT, "claude")
        assert mock_prompt_llm.call_args.kwargs["bash_grants"] == ["Bash(npm run lint)"]


class TestFixCheckText:
    """_fix_check_text reads the raw fix.check fragment."""

    def _toolkit(self, fragments: object) -> MagicMock:
        loaded = MagicMock()
        if isinstance(fragments, Exception):
            loaded.toolkit.prompt_fragments.side_effect = fragments
        else:
            loaded.toolkit.prompt_fragments.return_value = fragments
        return loaded

    def test_returns_fragment(self) -> None:
        with patch(
            f"{_TP}.load_toolkit", return_value=self._toolkit({"fix.check": "x"})
        ):
            assert _fix_check_text(_PROJECT) == "x"

    def test_missing_returns_none(self) -> None:
        with patch(f"{_TP}.load_toolkit", return_value=self._toolkit({})):
            assert _fix_check_text(_PROJECT) is None

    def test_prompt_fragments_raises_returns_none_and_warns(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with patch(
            f"{_TP}.load_toolkit", return_value=self._toolkit(RuntimeError("boom"))
        ):
            with caplog.at_level("WARNING"):
                assert _fix_check_text(_PROJECT) is None
        assert "boom" in caplog.text


class TestFixPrompt:
    """The fix prompt is built from the toolkit's fix.check fragment."""

    @patch(f"{_TP}._fix_check_text")
    @patch(f"{_TP}._run_check", return_value=None)
    def test_clean_check_loads_no_fragment(
        self, _mock_check: MagicMock, mock_fix_check: MagicMock
    ) -> None:
        assert check_and_fix_mypy(_PROJECT, 1, "claude") is True
        mock_fix_check.assert_not_called()

    @patch(f"{_TP}.store_session")
    @patch(f"{_TP}.prompt_llm")
    @patch(f"{_TP}._fix_check_text", return_value=_FIX_CHECK)
    @patch(f"{_TP}._run_check", side_effect=["a.py:1: error", None])
    @patch(f"{_TP}.toolkit_declares_bash_grants", return_value=False)
    @patch(f"{_TP}.llm_permissions", return_value=["mcp__tools-py__run_mypy_check"])
    def test_prompt_is_fragment_heading_and_fix_text(
        self,
        _mock_perms: MagicMock,
        _mock_declares: MagicMock,
        _mock_check: MagicMock,
        _mock_fix_check: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        mock_prompt_llm.return_value = _make_llm_response("fixed")

        assert check_and_fix_mypy(_PROJECT, 1, "claude") is True

        prompt = mock_prompt_llm.call_args.args[0]
        assert prompt == f"{_FIX_CHECK}\n\nCheck output:\na.py:1: error"
        assert "[mypy_output]" not in prompt

    @pytest.mark.parametrize("fragment", [None, ""])
    @patch(f"{_TP}.prompt_llm")
    @patch(f"{_TP}._run_check", return_value="a.py:1: error")
    def test_unusable_fragment_returns_false(
        self,
        _mock_check: MagicMock,
        mock_prompt_llm: MagicMock,
        fragment: str | None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with patch(f"{_TP}._fix_check_text", return_value=fragment):
            with caplog.at_level("WARNING"):
                assert check_and_fix_mypy(_PROJECT, 1, "claude") is False
        assert "fix.check" in caplog.text
        mock_prompt_llm.assert_not_called()

    @patch(f"{_TP}.prompt_llm")
    @patch(f"{_TP}._run_check", return_value="a.py:1: error")
    @patch(f"{_TP}.load_toolkit")
    def test_prompt_fragments_raises_returns_false(
        self,
        mock_load: MagicMock,
        _mock_check: MagicMock,
        mock_prompt_llm: MagicMock,
    ) -> None:
        mock_load.return_value.toolkit.prompt_fragments.side_effect = RuntimeError("x")

        assert check_and_fix_mypy(_PROJECT, 1, "claude") is False
        mock_prompt_llm.assert_not_called()

    @patch(f"{_TP}.store_session")
    @patch(f"{_TP}.prompt_llm")
    @patch(f"{_TP}.resolve_prompt_slots")
    @patch(f"{_TP}._fix_check_text", return_value=_FIX_CHECK)
    @patch(f"{_TP}._run_check", side_effect=["a.ts:1: error", None])
    @patch(f"{_TP}.toolkit_declares_bash_grants", return_value=True)
    @patch(f"{_TP}.llm_permissions", return_value=["Bash(npm run lint)"])
    def test_bash_grant_toolkit_appends_check_instructions(
        self,
        _mock_perms: MagicMock,
        _mock_declares: MagicMock,
        _mock_check: MagicMock,
        _mock_fix_check: MagicMock,
        mock_slots: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        mock_slots.return_value = {"check_instructions": "Run `npm run lint`."}
        mock_prompt_llm.return_value = _make_llm_response("fixed")

        assert check_and_fix_mypy(_PROJECT, 1, "claude") is True

        mock_slots.assert_called_once_with(
            "[check_instructions]", _PROJECT, "claude", ["Bash(npm run lint)"]
        )
        prompt = mock_prompt_llm.call_args.args[0]
        assert prompt == (
            f"{_FIX_CHECK}\n\nCheck output:\na.ts:1: error\n\nRun `npm run lint`."
        )

    @patch(f"{_TP}.store_session")
    @patch(f"{_TP}.prompt_llm")
    @patch(f"{_TP}.resolve_prompt_slots")
    @patch(f"{_TP}._fix_check_text", return_value=_FIX_CHECK)
    @patch(f"{_TP}._run_check", side_effect=["a.py:1: error", None])
    @patch(f"{_TP}.toolkit_declares_bash_grants", return_value=False)
    @patch(f"{_TP}.llm_permissions", return_value=["mcp__tools-py__run_mypy_check"])
    def test_toolkit_without_bash_grants_has_no_check_instructions(
        self,
        _mock_perms: MagicMock,
        _mock_declares: MagicMock,
        _mock_check: MagicMock,
        _mock_fix_check: MagicMock,
        mock_slots: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_store: MagicMock,
    ) -> None:
        mock_prompt_llm.return_value = _make_llm_response("fixed")

        assert check_and_fix_mypy(_PROJECT, 1, "claude") is True

        mock_slots.assert_not_called()
        assert mock_prompt_llm.call_args.args[0].endswith("a.py:1: error")
