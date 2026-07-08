"""Tests for delete-action display in the VSCode Claude status table."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
)


class TestBotStageSessionsDeleteAction:
    """Test bot stage sessions show simple delete action.

    Bot stage sessions are those at statuses where the bot is working:
    - bot_pickup: 02, 05, 08 (bot picks up work)
    - bot_busy: 03, 06, 09 (bot is actively working)

    These sessions should show "Delete" action since they don't need VSCodeClaude.
    """

    def test_bot_pickup_status_02_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-02:awaiting-planning shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-02:awaiting-planning",
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
        # Should show Delete action for bot stage status
        assert "Delete" in captured.out
        # Should NOT show (Closed) since issue is open
        assert "(Closed)" not in captured.out

    def test_bot_pickup_status_05_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-05:plan-ready shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-05:plan-ready",
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
        assert "#456" in captured.out
        assert "Delete" in captured.out

    def test_bot_pickup_status_08_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-08:ready-pr shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-08:ready-pr",
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
        assert "#789" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_03_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-03:planning shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 101,
            "status": "status-03:planning",
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
        assert "#101" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_06_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-06:implementing shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 202,
            "status": "status-06:implementing",
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
        assert "#202" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_09_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-09:pr-creating shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 303,
            "status": "status-09:pr-creating",
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
        assert "#303" in captured.out
        assert "Delete" in captured.out

    def test_bot_stage_dirty_folder_shows_manual_cleanup(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Bot stage session with dirty folder is held back with a dirty skip."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=True, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 404,
            "status": "status-02:awaiting-planning",
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
        assert "#404" in captured.out
        # Dirty folder is never auto-deleted: surfaced as a dirty skip
        assert "!! dirty" in captured.out

    def test_eligible_status_shows_restart_not_delete(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Eligible status (01, 04, 07) shows Restart, NOT Delete."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        # Status is the same as session (not stale from status change)
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=False
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 505,
            "status": "status-07:code-review",  # Eligible status
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
        assert "#505" in captured.out
        # Eligible status should show Restart, NOT Delete
        assert "Restart" in captured.out
        assert "Delete" not in captured.out


class TestPrCreatedSessionsDeleteAction:
    """Test pr-created sessions show simple delete action.

    Sessions at status-10:pr-created represent completed workflow.
    These sessions should show "Delete" action since:
    - The PR has been created, workflow is complete
    - No VSCodeClaude intervention is needed
    - Session should be cleaned up
    """

    def test_pr_created_status_10_shows_delete_action(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-10:pr-created shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-10:pr-created",
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
        # Should show Delete action for pr-created status
        assert "Delete" in captured.out
        # Should NOT show (Closed) since issue is open
        assert "(Closed)" not in captured.out

    def test_pr_created_dirty_folder_shows_manual_cleanup(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with dirty folder is held back with a dirty skip."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=True, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-10:pr-created",
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
        assert "#456" in captured.out
        # Dirty folder is never auto-deleted: surfaced as a dirty skip
        assert "!! dirty" in captured.out

    def test_pr_created_with_vscode_running_shows_active(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with VSCode running shows (active)."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=False, is_running=True, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-10:pr-created",
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
        assert "#789" in captured.out
        # Running VSCode should show (active)
        assert "(active)" in captured.out

    def test_pr_created_closed_issue_shows_closed_prefix(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with closed issue shows (Closed) prefix and Delete."""
        folder = tmp_path / "test_folder"
        folder.mkdir()
        make_assessments = mock_status_checks(
            is_closed=True, is_running=False, is_dirty=False, is_stale=True
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 999,
            "status": "status-10:pr-created",
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
        assert "#999" in captured.out
        # Should show (Closed) prefix for closed issue
        assert "(Closed)" in captured.out
        # Should still show Delete action
        assert "Delete" in captured.out


class TestDisplayStatusTableSoftDelete:
    """Tests for soft-delete filtering in display_status_table."""

    def test_display_status_table_hides_soft_deleted_sessions(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session with folder in .to_be_deleted is not shown in output."""
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        folder = tmp_path / "deleted_folder"
        folder.mkdir()

        # Add folder to .to_be_deleted registry
        to_be_deleted_file = tmp_path / ".to_be_deleted"
        to_be_deleted_file.write_text("deleted_folder\n")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-04:implementation",
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
        assert "#42" not in captured.out
        assert "deleted_folder" not in captured.out

    def test_display_status_table_shows_non_deleted_sessions(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session with folder NOT in .to_be_deleted is still shown."""
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=True
        )

        folder = tmp_path / "active_folder"
        folder.mkdir()

        # Add a DIFFERENT folder to .to_be_deleted registry
        to_be_deleted_file = tmp_path / ".to_be_deleted"
        to_be_deleted_file.write_text("other_folder\n")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 99,
            "status": "status-04:implementation",
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
        assert "#99" in captured.out
        assert "active_folder" in captured.out
