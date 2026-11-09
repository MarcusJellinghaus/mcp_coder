"""Unit tests for the rebase LLM session helper and prompt builders.

Pure unit tests — ``prompt_llm``, ``store_session``,
``get_branch_name_for_logging`` and ``_show_stage`` are mocked; only
``get_prompt`` runs for real against the packaged ``prompts.md``.
"""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.constants import LLM_INACTIVITY_TIMEOUT_SECONDS
from mcp_coder.workflows.rebase import (
    _build_conflict_prompt,
    _build_regression_fix_prompt,
    _check_tool_texts,
    _format_failure_keys,
    _marker_filter_text,
    _prompt_in_session,
)
from mcp_coder.workflows.rebase_checks import FailureKey

_ABSENT_NOTE = "(absent — file does not exist on this side)"


def _response(text: str = "done", session_id: str | None = "sid-new") -> dict[str, Any]:
    """Minimal ``prompt_llm`` response dict."""
    return {"text": text, "session_id": session_id}


def _call_prompt_in_session(
    project_dir: Path,
    *,
    session_id: str | None = None,
    response: dict[str, Any] | None = None,
    store_side_effect: Exception | None = None,
) -> tuple[tuple[str, str | None], MagicMock, MagicMock]:
    """Invoke ``_prompt_in_session`` with mocks.

    Returns:
        ``(result, prompt_llm_mock, store_session_mock)``.
    """
    with (
        patch(
            "mcp_coder.workflows.rebase.prompt_llm",
            return_value=response if response is not None else _response(),
        ) as mock_prompt,
        patch(
            "mcp_coder.workflows.rebase.store_session",
            side_effect=store_side_effect,
        ) as mock_store,
        patch(
            "mcp_coder.workflows.rebase.get_branch_name_for_logging",
            return_value="feature-branch",
        ),
    ):
        result = _prompt_in_session(
            "fix it",
            session_id,
            project_dir=project_dir,
            provider="claude",
            env_vars={"KEY": "value"},
            mcp_config="mcp.json",
            settings_file=None,
            step_name="conflict_1",
        )
    return result, mock_prompt, mock_store


class TestPromptInSession:
    """One resumable session call: prompt_llm shape + best-effort persistence."""

    def test_first_call_uses_none_session_and_inactivity_timeout(
        self, tmp_path: Path
    ) -> None:
        """First call passes session_id=None and the shared inactivity budget."""
        _, mock_prompt, _ = _call_prompt_in_session(tmp_path, session_id=None)
        kwargs = mock_prompt.call_args.kwargs
        assert kwargs["session_id"] is None
        assert kwargs["timeout"] == LLM_INACTIVITY_TIMEOUT_SECONDS
        assert kwargs["provider"] == "claude"
        assert kwargs["env_vars"] == {"KEY": "value"}
        assert kwargs["mcp_config"] == "mcp.json"
        assert kwargs["branch_name"] == "feature-branch"

    def test_bash_grants_default_none_and_forwarded(self, tmp_path: Path) -> None:
        """No grants by default; given grants reach prompt_llm unchanged."""
        _, mock_prompt, _ = _call_prompt_in_session(tmp_path)
        assert mock_prompt.call_args.kwargs["bash_grants"] is None

        with (
            patch(
                "mcp_coder.workflows.rebase.prompt_llm", return_value=_response()
            ) as granted,
            patch("mcp_coder.workflows.rebase.store_session"),
            patch(
                "mcp_coder.workflows.rebase.get_branch_name_for_logging",
                return_value="b",
            ),
        ):
            _prompt_in_session(
                "fix it",
                None,
                project_dir=tmp_path,
                provider="claude",
                env_vars={},
                mcp_config=None,
                settings_file=None,
                step_name="fix_1",
                bash_grants=["Bash(npm test)"],
            )
        assert granted.call_args.kwargs["bash_grants"] == ["Bash(npm test)"]

    def test_resume_passes_given_session_id(self, tmp_path: Path) -> None:
        """A resume threads the provided session id into prompt_llm."""
        _, mock_prompt, _ = _call_prompt_in_session(tmp_path, session_id="sid-old")
        assert mock_prompt.call_args.kwargs["session_id"] == "sid-old"

    def test_returns_text_and_new_session_id(self, tmp_path: Path) -> None:
        """The returned tuple carries the response text and new session id."""
        result, _, _ = _call_prompt_in_session(
            tmp_path, response=_response(text="resolved", session_id="sid-9")
        )
        assert result == ("resolved", "sid-9")

    def test_missing_text_returns_empty_string(self, tmp_path: Path) -> None:
        """A response without text yields "" (never None)."""
        result, _, _ = _call_prompt_in_session(
            tmp_path, response={"session_id": "sid-9"}
        )
        assert result == ("", "sid-9")

    def test_missing_session_id_keeps_the_threaded_id(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A turn that reports no session id never clears the resumed one.

        Overwriting it with None would make the next step start a fresh,
        context-free conversation instead of the rebase session.
        """
        with caplog.at_level(logging.WARNING, logger="mcp_coder.workflows.rebase"):
            result, _, _ = _call_prompt_in_session(
                tmp_path,
                session_id="sid-old",
                response=_response(session_id=None),
            )
        assert result == ("done", "sid-old")
        assert any("no resumable session id" in r.message for r in caplog.records)

    def test_missing_session_id_on_first_call_stays_none(self, tmp_path: Path) -> None:
        """With nothing to keep, no id is invented for the next step."""
        result, _, _ = _call_prompt_in_session(
            tmp_path, session_id=None, response=_response(session_id=None)
        )
        assert result == ("done", None)

    def test_store_session_receives_rebase_store_path(self, tmp_path: Path) -> None:
        """The exchange is persisted under .mcp-coder/rebase_sessions."""
        _, _, mock_store = _call_prompt_in_session(tmp_path)
        kwargs = mock_store.call_args.kwargs
        assert Path(kwargs["store_path"]).parts[-2:] == (
            ".mcp-coder",
            "rebase_sessions",
        )
        assert kwargs["prompt"] == "fix it"
        assert kwargs["step_name"] == "conflict_1"
        assert kwargs["branch_name"] == "feature-branch"
        assert kwargs["response_data"] == _response()

    def test_store_session_failure_only_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A store_session failure is logged as a warning, never raised."""
        with caplog.at_level(logging.WARNING, logger="mcp_coder.workflows.rebase"):
            result, _, _ = _call_prompt_in_session(
                tmp_path, store_side_effect=OSError("disk full")
            )
        assert result == ("done", "sid-new")
        assert any("disk full" in record.message for record in caplog.records)


class TestBuildConflictPrompt:
    """Conflict prompt: three-stage content inlined per file."""

    def test_includes_path_and_all_three_versions(self, tmp_path: Path) -> None:
        """File path and ancestor/ours/theirs contents all appear."""
        with patch(
            "mcp_coder.workflows.rebase._show_stage",
            side_effect=lambda _dir, stage, file: f"content-{stage}-{file}",
        ):
            prompt = _build_conflict_prompt(tmp_path, ["src/a.py"])
        assert "src/a.py" in prompt
        for stage in (1, 2, 3):
            assert f"content-{stage}-src/a.py" in prompt
        assert "[conflict_context]" not in prompt

    def test_absent_side_renders_absence_note(self, tmp_path: Path) -> None:
        """A missing side (delete/modify) renders the absence note."""
        with patch(
            "mcp_coder.workflows.rebase._show_stage",
            side_effect=lambda _dir, stage, file: (
                None if stage == 3 else f"content-{stage}"
            ),
        ):
            prompt = _build_conflict_prompt(tmp_path, ["src/gone.py"])
        assert _ABSENT_NOTE in prompt
        assert "content-1" in prompt
        assert "content-2" in prompt
        assert "content-3" not in prompt

    def test_multiple_files_each_get_a_block(self, tmp_path: Path) -> None:
        """Every conflicted file appears in the built prompt."""
        with patch(
            "mcp_coder.workflows.rebase._show_stage",
            side_effect=lambda _dir, stage, file: f"{file}@{stage}",
        ):
            prompt = _build_conflict_prompt(tmp_path, ["src/a.py", "src/b.py"])
        assert "src/a.py" in prompt
        assert "src/b.py" in prompt


class TestBuildRegressionFixPrompt:
    """Regression prompt: placeholders replaced with the given texts."""

    _KEY = "test: tests/test_x.py::test_new"

    def test_placeholder_replaced_with_text(self) -> None:
        """[regression_output] is fully replaced by the regression text."""
        prompt = _build_regression_fix_prompt({"regression_output": self._KEY})
        assert self._KEY in prompt
        assert "[regression_output]" not in prompt

    def test_filter_text_replaces_placeholder(self) -> None:
        """The filter text takes the placeholder's place."""
        prompt = _build_regression_fix_prompt(
            {"regression_output": self._KEY, "pytest_marker_filter": "FILTER"}
        )
        assert "[pytest_marker_filter]" not in prompt
        assert "FILTER" in prompt

    def test_missing_names_remove_placeholders(self) -> None:
        """Placeholders without a replacement render as empty text."""
        prompt = _build_regression_fix_prompt({"regression_output": self._KEY})
        for name in ("check_tools", "pytest_marker_filter", "fix_text", "shell_ban"):
            assert f"[{name}]" not in prompt
        assert "markers=" not in prompt

    def test_inlined_output_is_not_substituted_again(self) -> None:
        """A placeholder-like string inside the check output stays verbatim."""
        prompt = _build_regression_fix_prompt(
            {"fix_text": "log mentions [shell_ban]", "shell_ban": "BAN; "}
        )
        assert "log mentions [shell_ban]" in prompt
        assert "**Prohibited:** BAN; no staging" in prompt


class TestCheckToolTexts:
    """The check-tool sentence and shell ban follow the permissions."""

    def test_mcp_tools_only(self) -> None:
        """MCP tools are named; the shell ban stays."""
        sentence, ban = _check_tool_texts(["mcp__a", "mcp__b"])
        assert "granted MCP check tools (`mcp__a`, `mcp__b`)" in sentence
        assert ban == "no shell commands of any kind; "

    def test_bash_grants_listed_as_commands(self) -> None:
        """Bash grants render as the exact commands; no shell ban."""
        sentence, ban = _check_tool_texts(["Bash(npm run lint)", "Bash(npm test)"])
        assert "exactly as written: `npm run lint`, `npm test`." in sentence
        assert "MCP" not in sentence
        assert ban == ""

    def test_no_permissions(self) -> None:
        """Nothing granted: use the inlined output; the shell ban stays."""
        sentence, ban = _check_tool_texts([])
        assert sentence == "You cannot re-run the checks; use the output below."
        assert ban == "no shell commands of any kind; "


class TestMarkerFilterText:
    """The unattended filter instruction comes from the toolkit's fragment."""

    def test_not_automated_is_empty(self, tmp_path: Path) -> None:
        """Interactive runs add no filter text and never load the toolkit."""
        with patch("mcp_coder.workflows.rebase.load_toolkit") as mock_load:
            assert _marker_filter_text(tmp_path, False, []) == ""
        mock_load.assert_not_called()

    def test_automated_returns_unattended_fragment(self, tmp_path: Path) -> None:
        """Automated runs use the ``check_instructions.unattended`` fragment."""
        loaded = MagicMock()
        with (
            patch("mcp_coder.workflows.rebase.llm_permissions", return_value=["mcp"]),
            patch(
                "mcp_coder.workflows.rebase.load_toolkit", return_value=loaded
            ) as mock_load,
            patch(
                "mcp_coder.workflows.rebase.get_fragment", return_value="FRAGMENT"
            ) as mock_fragment,
        ):
            assert _marker_filter_text(tmp_path, True, ["mcp"]) == "FRAGMENT"
        mock_load.assert_called_once_with(tmp_path)
        mock_fragment.assert_called_once_with(loaded, "check_instructions.unattended")

    def test_automated_with_bash_grants_returns_fragment(self, tmp_path: Path) -> None:
        """Granted Bash commands keep the filter instruction."""
        grants = ["Bash(npm test)"]
        with (
            patch("mcp_coder.workflows.rebase.llm_permissions", return_value=grants),
            patch("mcp_coder.workflows.rebase.load_toolkit"),
            patch("mcp_coder.workflows.rebase.get_fragment", return_value="FRAGMENT"),
        ):
            assert _marker_filter_text(tmp_path, True, grants) == "FRAGMENT"

    def test_dropped_bash_grants_are_empty(self, tmp_path: Path) -> None:
        """Copilot: the toolkit declares Bash grants but the session has none."""
        with (
            patch(
                "mcp_coder.workflows.rebase.llm_permissions",
                return_value=["Bash(npm test)"],
            ) as mock_perms,
            patch("mcp_coder.workflows.rebase.get_fragment") as mock_fragment,
        ):
            assert _marker_filter_text(tmp_path, True, []) == ""
        mock_perms.assert_called_once_with(tmp_path, "claude", "rebase_automated")
        mock_fragment.assert_not_called()


class TestFormatFailureKeys:
    """Deterministic sorted rendering (doubles as the stall-guard string)."""

    def test_sorted_one_per_line(self) -> None:
        """Keys render sorted, one per line."""
        keys: set[FailureKey] = {
            "test: tests/test_a.py::test_new",
            "check: src/mod.py|W0611|Unused import os",
            "check: src/mod.py|arg-type|Bad argument",
        }
        assert _format_failure_keys(keys) == (
            "check: src/mod.py|W0611|Unused import os\n"
            "check: src/mod.py|arg-type|Bad argument\n"
            "test: tests/test_a.py::test_new"
        )

    def test_stable_across_set_ordering(self) -> None:
        """Insertion order never changes the rendered string."""
        items: list[FailureKey] = [
            "test: tests/test_b.py::test_two",
            "check: src/mod.py|arg-type|Bad argument",
            "test: tests/test_a.py::test_one",
        ]
        reordered = [items[2], items[0], items[1]]
        assert _format_failure_keys(set(items)) == _format_failure_keys(set(reordered))

    def test_empty_set_returns_empty_string(self) -> None:
        """An empty key set renders as ""."""
        assert _format_failure_keys(set()) == ""
