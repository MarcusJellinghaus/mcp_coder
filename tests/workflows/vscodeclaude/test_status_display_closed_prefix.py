"""Tests for the (Closed) prefix display of closed issues in the status table."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
)
from tests.workflows.vscodeclaude.conftest import _build_assessment


class TestClosedIssuePrefixDisplay:
    """Test (Closed) prefix display for closed issues in status table."""

    def test_closed_issue_shows_closed_prefix_in_status(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with existing folder shows (Closed) prefix in status column."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
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
        # Verify session is shown
        assert "#123" in captured.out
        # Verify "(Closed)" prefix appears in output
        assert "(Closed)" in captured.out

    def test_closed_issue_status_includes_original_status_label(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue status shows both (Closed) prefix and original status."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
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
        # Should show both (Closed) prefix and status info
        assert "(Closed)" in captured.out
        assert "#456" in captured.out

    def test_closed_issue_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with clean folder shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
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
        # Should show delete action for closed issue
        assert "Delete" in captured.out

    def test_closed_issue_dirty_folder_shows_manual_cleanup(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with dirty folder is held back with a dirty skip."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=True, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
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
        # Should show (Closed) prefix
        assert "(Closed)" in captured.out
        # Dirty folder is never auto-deleted: surfaced as a dirty skip
        assert "!! dirty" in captured.out

    def test_closed_issue_missing_folder_is_skipped(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with missing folder is not shown in status table."""
        missing_folder = tmp_path / "missing_folder"
        # Do NOT create the folder - it should not exist
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(missing_folder),  # Folder does not exist
            "repo": "owner/repo",
            "issue_number": 789,
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
        # Session with closed issue and missing folder should be SKIPPED
        # Nothing to clean up if folder doesn't exist
        assert "#789" not in captured.out
        assert "(Closed)" not in captured.out

    def test_closed_issue_existing_folder_is_shown(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with existing folder IS shown (contrast to missing folder)."""
        existing_folder = tmp_path / "existing_folder"
        existing_folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(existing_folder),  # Folder EXISTS
            "repo": "owner/repo",
            "issue_number": 789,
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
        # Session with closed issue and EXISTING folder should be shown
        # Needs cleanup since folder exists
        assert "#789" in captured.out
        assert "(Closed)" in captured.out

    def test_open_issue_does_not_show_closed_prefix(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Open issue does not show (Closed) prefix."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=False
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
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
        # Should show the session
        assert "#123" in captured.out
        # Should NOT show (Closed) prefix
        assert "(Closed)" not in captured.out

    def test_stale_session_shows_current_github_status(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Stale session shows current GitHub status (not stored session status).

        Regression test: when issue status changes from status-04:plan-review
        to status-06:implementing, the display should show
        '-> status-06:implementing' not '-> status-04:plan-review'. The current
        status now travels in the assessment's ``issue_state.stale_target``.
        """
        folder = tmp_path / "test_folder"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 458,
            "status": "status-04:plan-review",  # Stored (old) status
            "vscode_pid": None,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Assessment: open + stale, current GitHub status carried in stale_target.
        assessments = {
            session["folder"]: _build_assessment(
                session,
                is_closed=False,
                is_running=False,
                is_dirty=False,
                is_stale=True,
                stale_target="status-06:implementing",
            )
        }

        display_status_table(
            sessions=[session],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments=assessments,
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "#458" in captured.out
        # Should show the CURRENT status (from GitHub), not the stored status
        assert "status-06:implementing" in captured.out
        assert "-> status-06:implementing" in captured.out
        # Should NOT show the old stored status
        assert "status-04:plan-review" not in captured.out
