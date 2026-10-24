"""Tests for zombie session display in the VSCode Claude status table."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
)


class TestZombieSessionDisplay:
    """Tests for zombie session display in status table.

    Zombie state: a session whose folder is missing on disk but whose VSCode
    process is still considered live. Surface this state so the user can
    diagnose blocked launches caused by phantom sessions.
    """

    def test_zombie_session_appears_with_running_zombie_qualifier(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue + missing folder + running process appears as zombie."""
        missing_folder = tmp_path / "zombie_folder"
        # Do NOT create the folder - it must not exist
        make_assessments = mock_status_checks(
            is_closed=True, is_running=True, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(missing_folder),
            "repo": "owner/repo",
            "issue_number": 188,
            "status": "status-07:code-review",
            "vscode_pid": 74544,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments=make_assessments(session),
            repo_filter=None,
        )

        captured = capsys.readouterr()
        # Zombie row appears
        assert "#188" in captured.out
        # Three column literals required by step_5.md
        assert "Running (zombie)" in captured.out
        assert "Missing" in captured.out
        assert "-> Investigate zombie" in captured.out
        # (Closed) prefix on Status column is preserved on the zombie row
        assert "(Closed)" in captured.out

    def test_closed_missing_folder_without_running_process_still_skipped(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Existing behavior preserved when no live process claims the slot."""
        missing_folder = tmp_path / "missing_folder"
        # Do NOT create the folder
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(missing_folder),
            "repo": "owner/repo",
            "issue_number": 777,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments=make_assessments(session),
            repo_filter=None,
        )

        captured = capsys.readouterr()
        # Row must NOT appear - nothing to show, nothing to clean up
        assert "#777" not in captured.out
        assert "Running (zombie)" not in captured.out
        assert "-> Investigate zombie" not in captured.out

    def test_live_session_with_existing_folder_not_marked_as_zombie(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Live session with present folder shows plain 'Running', not zombie."""
        existing_folder = tmp_path / "live_folder"
        existing_folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=True, is_dirty=False, is_stale=False
        )

        session: VSCodeClaudeSession = {
            "folder": str(existing_folder),
            "repo": "owner/repo",
            "issue_number": 949,
            "status": "status-07:code-review",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments=make_assessments(session),
            repo_filter=None,
        )

        captured = capsys.readouterr()
        # Live session appears with plain "Running" qualifier - not zombie
        assert "#949" in captured.out
        assert "Running" in captured.out
        assert "(zombie)" not in captured.out
        assert "-> Investigate zombie" not in captured.out
