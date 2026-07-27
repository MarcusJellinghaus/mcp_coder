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
    FailureKey,
    _build_conflict_prompt,
    _build_regression_fix_prompt,
    _format_failure_keys,
    _prompt_in_session,
)

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
            execution_dir=None,
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
    """Regression prompt: placeholder replaced with the given failure text."""

    def test_placeholder_replaced_with_text(self) -> None:
        """[regression_output] is fully replaced by the regression text."""
        prompt = _build_regression_fix_prompt("pytest: tests/test_x.py::test_new")
        assert "pytest: tests/test_x.py::test_new" in prompt
        assert "[regression_output]" not in prompt


class TestFormatFailureKeys:
    """Deterministic sorted rendering (doubles as the stall-guard string)."""

    def test_sorted_one_per_line(self) -> None:
        """Keys render sorted, one per line, kind-prefixed."""
        keys: set[FailureKey] = {
            ("pytest", "tests/test_a.py::test_new"),
            ("pylint", "src/mod.py", "W0611", "Unused import os"),
            ("mypy", "src/mod.py", "arg-type", "Bad argument"),
        }
        assert _format_failure_keys(keys) == (
            "mypy: src/mod.py arg-type Bad argument\n"
            "pylint: src/mod.py W0611 Unused import os\n"
            "pytest: tests/test_a.py::test_new"
        )

    def test_stable_across_set_ordering(self) -> None:
        """Insertion order never changes the rendered string."""
        items: list[FailureKey] = [
            ("pytest", "tests/test_b.py::test_two"),
            ("mypy", "src/mod.py", "arg-type", "Bad argument"),
            ("pytest", "tests/test_a.py::test_one"),
        ]
        assert _format_failure_keys(set(items)) == _format_failure_keys(
            set(reversed(items))
        )

    def test_empty_set_returns_empty_string(self) -> None:
        """An empty key set renders as ""."""
        assert _format_failure_keys(set()) == ""
