"""Tests for commit_changes on a clean or unreadable working tree."""

import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.commit import FALLBACK_COMMIT_MESSAGE, commit_changes

STATUS = "mcp_coder.workflow_steps.commit.get_working_tree_status"
GENERATE = "mcp_coder.workflow_steps.commit.generate_commit_message_with_llm"
COMMIT = "mcp_coder.workflow_steps.commit.commit_all_changes"


def _status(success: bool = True, clean: bool = False) -> dict[str, object]:
    """Build a StatusResult-shaped dict."""
    if not success:
        return {
            "success": False,
            "error": "git status failed (exit 128)",
            "returncode": 128,
            "stderr": "fatal: error",
            "clean": False,
            "staged": [],
            "modified": [],
            "untracked": [],
        }
    return {
        "success": True,
        "error": None,
        "returncode": 0,
        "stderr": "",
        "clean": clean,
        "staged": [],
        "modified": [] if clean else ["a.py"],
        "untracked": [],
    }


@patch(COMMIT)
@patch(GENERATE)
@patch(STATUS)
def test_clean_tree_skips_commit(
    mock_status: MagicMock,
    mock_generate: MagicMock,
    mock_commit: MagicMock,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A clean tree returns True without generating a message or committing.

    Nothing is logged at WARNING or above, so Jenkins does not mark the
    build unstable for a round that changed no files.
    """
    caplog.set_level(logging.INFO)
    mock_status.return_value = _status(clean=True)

    assert commit_changes(tmp_path) is True

    mock_generate.assert_not_called()
    mock_commit.assert_not_called()
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert "No changes to commit - skipping commit" in caplog.text


@patch(COMMIT)
@patch(GENERATE)
@patch(STATUS)
def test_clean_tree_with_prepared_message_deletes_file(
    mock_status: MagicMock,
    mock_generate: MagicMock,
    mock_commit: MagicMock,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The prepared message file is deleted even when there is nothing to commit.

    The status check runs after the deletion, so the untracked message file
    cannot make the tree read dirty, and no stale message is left behind.
    """
    caplog.set_level(logging.INFO)
    pr_info = tmp_path / "pr_info"
    pr_info.mkdir()
    commit_file = pr_info / ".commit_message.txt"
    commit_file.write_text("feat: x", encoding="utf-8")
    mock_status.return_value = _status(clean=True)

    assert commit_changes(tmp_path) is True

    assert not commit_file.exists()
    mock_generate.assert_not_called()
    mock_commit.assert_not_called()


@pytest.mark.parametrize(
    "status_kwargs",
    [
        pytest.param({"return_value": _status(success=False)}, id="success_false"),
        pytest.param({"side_effect": RuntimeError("boom")}, id="raises"),
    ],
)
@patch(COMMIT)
@patch(GENERATE)
@patch(STATUS)
def test_status_read_failure_proceeds_as_dirty(
    mock_status: MagicMock,
    mock_generate: MagicMock,
    mock_commit: MagicMock,
    status_kwargs: dict[str, Any],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unreadable status counts as dirty, so a real commit is never skipped.

    The failure is reported once as a WARNING and never as an ERROR.
    """
    caplog.set_level(logging.INFO)
    mock_status.configure_mock(**status_kwargs)
    mock_generate.return_value = (True, "feat: m", None)
    mock_commit.return_value = {"success": True, "commit_hash": "abc123", "error": None}

    assert commit_changes(tmp_path) is True

    mock_generate.assert_called_once()
    mock_commit.assert_called_once()
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 1
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


@patch(COMMIT)
@patch(GENERATE)
@patch(STATUS)
def test_dirty_status_nothing_staged_flows_through_fallback(
    mock_status: MagicMock,
    mock_generate: MagicMock,
    mock_commit: MagicMock,
    tmp_path: Path,
) -> None:
    """A dirty status with nothing to stage still succeeds via the fallback.

    Stat-only line-ending dirt reads as dirty while the diff is empty:
    generation fails, the fallback message is used, and the commit no-ops.
    """
    mock_status.return_value = _status(clean=False)
    mock_generate.return_value = (False, "", "No changes to commit")
    mock_commit.return_value = {"success": True, "commit_hash": None, "error": None}

    assert commit_changes(tmp_path) is True

    mock_commit.assert_called_once_with(FALLBACK_COMMIT_MESSAGE, tmp_path)
