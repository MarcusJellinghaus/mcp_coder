"""Tests for formatting the task tracker commit and committing the formatter's changes."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps import commit
from mcp_coder.workflow_steps.commit import FormatterConfigError
from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflows.implement import task_tracker_prep as prep
from mcp_coder.workflows.implement.task_tracker_prep import (
    TrackerPrepError,
    prepare_task_tracker,
)

PREP = "mcp_coder.workflows.implement.task_tracker_prep"
TRACKER = "pr_info/TASK_TRACKER.md"

POPULATED = (
    "# Task Status Tracker\n\n"
    "## Tasks\n\n"
    "### Step 1: Setup\n"
    "- [ ] Implementation\n"
    "- [ ] Quality checks\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)

TRACKER_ONLY: dict[str, list[str]] = {
    "staged": [],
    "modified": [TRACKER],
    "untracked": [],
}

FORMATTED: dict[str, list[str]] = {
    "staged": [],
    "modified": [TRACKER, "src/a.py"],
    "untracked": [".mcp-coder/implement_sessions/s.json"],
}


def _llm_response() -> dict[str, Any]:
    return {
        "text": "done",
        "session_id": "session-1",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


@dataclass
class FormatMocks:
    """Patched collaborators of prepare_task_tracker."""

    tracker: Path
    get_full_status: MagicMock
    commit_paths: MagicMock
    reset_hard: MagicMock


@pytest.fixture
def mocks(tmp_path: Path) -> Iterator[FormatMocks]:
    """EMPTY tracker; the LLM writes POPULATED; the formatter changes nothing."""
    (tmp_path / "pr_info" / "steps").mkdir(parents=True)
    tracker = tmp_path / "pr_info" / "TASK_TRACKER.md"
    tracker.write_text(TASK_TRACKER_TEMPLATE, encoding="utf-8")

    def populate(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        tracker.write_text(POPULATED, encoding="utf-8")
        return _llm_response()

    with (
        patch(f"{PREP}.prepare_llm_environment", return_value={}),
        patch(f"{PREP}.get_prompt", return_value="prompt"),
        patch(f"{PREP}.get_branch_name_for_logging", return_value="branch"),
        patch(f"{PREP}.prompt_llm", side_effect=populate),
        patch(f"{PREP}.store_session"),
        patch(
            f"{PREP}.get_full_status", side_effect=[TRACKER_ONLY, TRACKER_ONLY]
        ) as get_full_status,
        patch(
            f"{PREP}.commit_paths",
            return_value={"success": True, "commit_hash": "abc123"},
        ) as commit_paths,
        patch(
            f"{PREP}.reset_hard",
            return_value={
                "success": True,
                "error": None,
                "returncode": 0,
                "stderr": "",
            },
        ) as reset_hard,
    ):
        yield FormatMocks(tracker, get_full_status, commit_paths, reset_hard)


class TestFormatBeforeCommit:
    """format_best_effort runs before the commit, whose paths include its changes."""

    def test_formats_before_commit(
        self,
        tmp_path: Path,
        mocks: FormatMocks,
        formatter_mocks: SimpleNamespace,
    ) -> None:
        order: list[str] = []

        def fake_format(*_args: Any) -> None:
            order.append("format")

        def fake_commit(*_args: Any) -> dict[str, Any]:
            order.append("commit")
            return {"success": True, "commit_hash": "abc123"}

        formatter_mocks.format_best_effort.side_effect = fake_format
        mocks.commit_paths.side_effect = fake_commit

        prepare_task_tracker(tmp_path, "claude")

        formatter_mocks.format_best_effort.assert_called_once()
        assert formatter_mocks.format_best_effort.call_args.args[0] == tmp_path
        assert order == ["format", "commit"]

    def test_commits_formatter_files_without_mcp_coder(
        self, tmp_path: Path, mocks: FormatMocks
    ) -> None:
        mocks.get_full_status.side_effect = [TRACKER_ONLY, FORMATTED]

        prepare_task_tracker(tmp_path, "claude")

        mocks.commit_paths.assert_called_once()
        assert mocks.commit_paths.call_args.args[1] == [
            mocks.tracker,
            tmp_path / "src/a.py",
        ]
        mocks.reset_hard.assert_not_called()

    @pytest.mark.parametrize(
        "formatter_kwargs",
        [
            {"side_effect": FormatterConfigError("bad toolkit")},
            {"return_value": False},
        ],
        ids=["raises", "returns_false"],
    )
    def test_failed_formatting_warns_and_still_commits(
        self,
        formatter_kwargs: dict[str, object],
        tmp_path: Path,
        mocks: FormatMocks,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        run_formatters = MagicMock(**formatter_kwargs)
        monkeypatch.setattr(prep, "format_best_effort", commit.format_best_effort)
        monkeypatch.setattr(commit, "run_formatters", run_formatters)

        with caplog.at_level(logging.WARNING):
            prepare_task_tracker(tmp_path, "claude")

        run_formatters.assert_called_once_with(tmp_path)
        warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING
            and "Formatting failed before task tracker commit" in r.getMessage()
        ]
        assert len(warnings) == 1
        mocks.commit_paths.assert_called_once()


class TestRestoreOnCommitFailure:
    """A failed commit restores the tracker and resets the formatter's files."""

    def test_resets_when_formatter_changed_files(
        self, tmp_path: Path, mocks: FormatMocks
    ) -> None:
        original = mocks.tracker.read_bytes()
        mocks.get_full_status.side_effect = [TRACKER_ONLY, FORMATTED]
        mocks.commit_paths.return_value = {"success": False, "error": "x"}

        with pytest.raises(TrackerPrepError):
            prepare_task_tracker(tmp_path, "claude")

        mocks.reset_hard.assert_called_once_with(tmp_path, "HEAD")
        assert mocks.tracker.read_bytes() == original

    def test_no_reset_when_formatter_changed_nothing(
        self, tmp_path: Path, mocks: FormatMocks
    ) -> None:
        original = mocks.tracker.read_bytes()
        mocks.commit_paths.return_value = {"success": False, "error": "x"}

        with pytest.raises(TrackerPrepError):
            prepare_task_tracker(tmp_path, "claude")

        mocks.reset_hard.assert_not_called()
        assert mocks.tracker.read_bytes() == original

    def test_failed_reset_logs_error(
        self,
        tmp_path: Path,
        mocks: FormatMocks,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mocks.get_full_status.side_effect = [TRACKER_ONLY, FORMATTED]
        mocks.commit_paths.return_value = {"success": False, "error": "x"}
        mocks.reset_hard.return_value = {
            "success": False,
            "error": "git reset --hard failed (exit 128)",
            "returncode": 128,
            "stderr": "fatal",
        }

        with caplog.at_level(logging.ERROR), pytest.raises(TrackerPrepError):
            prepare_task_tracker(tmp_path, "claude")

        assert any(
            r.levelno == logging.ERROR
            and "git reset --hard failed (exit 128)" in r.getMessage()
            for r in caplog.records
        )
