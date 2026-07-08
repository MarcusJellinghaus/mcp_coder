"""Test status table and display functions for VSCode Claude."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    check_folder_dirty,
    display_status_table,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
)


class TestStatusDisplay:
    """Test status table and display functions."""

    def test_get_issue_current_status_returns_status(self) -> None:
        """Returns status label and open state when found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "open",
            "labels": ["status-07:code-review", "other-label"],
        }

        status, is_open = get_issue_current_status(123, issue_manager=mock_manager)

        assert status == "status-07:code-review"
        assert is_open is True
        mock_manager.get_issue.assert_called_once_with(123)

    def test_get_issue_current_status_returns_closed_state(self) -> None:
        """Returns correct closed state."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "closed",
            "labels": ["status-07:code-review"],
        }

        status, is_open = get_issue_current_status(123, issue_manager=mock_manager)

        assert status == "status-07:code-review"
        assert is_open is False

    def test_get_issue_current_status_returns_none_no_status(self) -> None:
        """Returns None status when no status label found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "open",
            "labels": ["other-label"],
        }

        status, is_open = get_issue_current_status(123, issue_manager=mock_manager)

        assert status is None
        assert is_open is True

    def test_get_issue_current_status_returns_none_on_error(self) -> None:
        """Returns None and False on API error."""
        mock_manager = Mock()
        mock_manager.get_issue.side_effect = Exception("API error")

        status, is_open = get_issue_current_status(123, issue_manager=mock_manager)

        assert status is None
        assert is_open is False

    def test_get_issue_current_status_returns_none_issue_not_found(self) -> None:
        """Returns None and False when issue not found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = None

        status, is_open = get_issue_current_status(123, issue_manager=mock_manager)

        assert status is None
        assert is_open is False

    def test_is_session_stale_same_status(self) -> None:
        """Returns False when status unchanged."""
        # Use cached_issues instead of mocking _get_coordinator
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "...",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
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

        assert is_session_stale(session, cached_issues=cached_issues) is False

    def test_is_session_stale_status_changed(self) -> None:
        """Returns True when status changed."""
        # Use cached_issues instead of mocking _get_coordinator
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test",
                "body": "",
                "state": "open",
                "labels": ["status-08:ready-pr"],  # Changed from session
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "...",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",  # Original
            "vscode_pid": None,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        assert is_session_stale(session, cached_issues=cached_issues) is True

    def test_is_session_stale_no_status_label(self) -> None:
        """Returns False when open issue has no status label (logs warning)."""
        # Use cached_issues instead of mocking _get_coordinator
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test",
                "body": "",
                "state": "open",
                "labels": ["other-label"],  # No status label
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "...",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
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

        # Open issue without status label - should NOT be stale
        assert is_session_stale(session, cached_issues=cached_issues) is False

    def test_is_session_stale_returns_true_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when status cannot be retrieved."""
        # Mock IssueManager to return None (issue not found)
        mock_manager = Mock()
        mock_manager.get_issue.return_value = None

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.IssueManager",
            lambda repo_url: mock_manager,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test",
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

        # Without cached_issues, falls back to IssueManager which returns None
        assert is_session_stale(session) is True

    def test_is_issue_closed_returns_true_when_closed(self) -> None:
        """Returns True when issue is closed."""
        # Use cached_issues instead of mocking _get_coordinator
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test",
                "body": "",
                "state": "closed",
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "...",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
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

        assert is_issue_closed(session, cached_issues=cached_issues) is True

    def test_is_issue_closed_returns_false_when_open(self) -> None:
        """Returns False when issue is open."""
        # Use cached_issues instead of mocking _get_coordinator
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "...",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
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

        assert is_issue_closed(session, cached_issues=cached_issues) is False

    def test_check_folder_dirty_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False for clean git repo."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            return CommandResult(
                return_code=0,
                stdout="",  # Empty = clean
                stderr="",
                timed_out=False,
            )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        assert check_folder_dirty(tmp_path) is False

    def test_check_folder_dirty_with_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when uncommitted changes exist."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            return CommandResult(
                return_code=0,
                stdout="M  file.py\n",  # Modified file
                stderr="",
                timed_out=False,
            )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        assert check_folder_dirty(tmp_path) is True

    def test_check_folder_dirty_returns_true_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when git command fails."""
        from mcp_coder.utils.subprocess_runner import CalledProcessError

        def mock_execute(cmd: list[str], options: Any = None) -> None:
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        assert check_folder_dirty(tmp_path) is True

    def test_get_next_action_active(self) -> None:
        """Returns (active) when VSCode running."""
        action = get_next_action(is_stale=False, is_dirty=False, is_vscode_running=True)
        assert action == "(active)"

    def test_get_next_action_restart(self) -> None:
        """Returns Restart when closed but not stale."""
        action = get_next_action(
            is_stale=False, is_dirty=False, is_vscode_running=False
        )
        assert "Restart" in action

    def test_get_next_action_delete(self) -> None:
        """Returns Delete when stale and clean."""
        action = get_next_action(is_stale=True, is_dirty=False, is_vscode_running=False)
        assert "Delete" in action

    def test_get_next_action_manual(self) -> None:
        """Returns Manual cleanup when stale and dirty."""
        action = get_next_action(is_stale=True, is_dirty=True, is_vscode_running=False)
        assert "Manual" in action

    def test_display_status_table_empty(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Handles empty sessions and issues."""
        display_status_table(
            sessions=[],
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={},
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "No sessions" in captured.out or "Folder" in captured.out

    def test_display_status_table_with_session(
        self,
        tmp_path: Path,
        mock_status_checks: Any,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Displays session information."""
        make_assessments = mock_status_checks(
            is_closed=False, is_running=False, is_dirty=False, is_stale=False
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_folder"),
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
        assert "#123" in captured.out
        assert "owner/repo".split("/")[-1] in captured.out  # "repo"

    def test_display_status_table_with_eligible_issue(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Displays eligible issues not yet in sessions."""
        issue: IssueData = {
            "number": 456,
            "title": "New issue",
            "body": "",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/456",
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("myrepo", issue)]

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "#456" in captured.out
        assert "Create and start" in captured.out

    def test_pr_created_eligible_issue_shows_awaiting_merge(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Eligible issue with status-10:pr-created shows (awaiting merge) action."""
        issue: IssueData = {
            "number": 435,
            "title": "PR created issue",
            "body": "",
            "state": "open",
            "labels": ["status-10:pr-created"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "https://github.com/owner/repo/issues/435",
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", issue)]

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            repo_filter=None,
        )

        captured = capsys.readouterr()
        assert "(awaiting merge)" in captured.out
        assert "-> Create and start" not in captured.out


class TestScenarioACrossModule:
    """Composition test — display consistency after Scenario A cleanup.

    Pair of ``test_orphan_workspace_file_end_to_end`` in
    ``test_cleanup.py``. Runs the same Scenario A setup, executes the
    cleanup pass, then asserts ``display_status_table`` no longer renders
    the removed session.
    """

    def test_display_status_table_omits_cleaned_up_session(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """After Scenario A cleanup, the status table omits the cleaned session."""
        from mcp_coder.utils.folder_deletion import DeletionResult
        from mcp_coder.workflows.vscodeclaude.cleanup import cleanup_stale_sessions
        from mcp_coder.workflows.vscodeclaude.helpers import TO_BE_DELETED_FILENAME
        from mcp_coder.workflows.vscodeclaude.sessions import load_sessions
        from mcp_coder.workflows.vscodeclaude.types import (
            Decision,
            DetectionSignals,
            IssueState,
            LivenessRule,
            LivenessVerdict,
            SessionAction,
            SessionAssessment,
            Transition,
        )

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        folder_name = "mcp_coder_188"
        folder = tmp_path / folder_name
        # Folder absent on disk.

        orphan_workspace = tmp_path / f"{folder_name}.code-workspace"
        orphan_workspace.write_text("{}")

        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
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
        sessions_file.write_text(
            json.dumps({"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"})
        )

        closed_issue: IssueData = {
            "number": 188,
            "title": "Closed issue",
            "body": "",
            "state": "closed",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        cached_issues_by_repo: dict[str, dict[int, IssueData]] = {
            "owner/repo": {188: closed_issue}
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            lambda path: DeletionResult(success=True),
        )

        # The closed issue's folder is gone -> the upstream assessment resolves
        # to REMOVE_MISSING; cleanup consumes that decision directly.
        assessments = {
            str(folder): SessionAssessment(
                folder=str(folder),
                signals=DetectionSignals(
                    folder_exists=False,
                    title_match=False,
                    cmdline_match=False,
                    pid_alive=False,
                    found_pid=None,
                    age_seconds=0.0,
                    within_grace=False,
                    directory_empty=True,
                ),
                verdict=LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS),
                issue_state=IssueState(
                    is_open=False,
                    is_stale=False,
                    is_blocked=False,
                    is_unassigned=False,
                    is_eligible=False,
                ),
                transition=Transition(flipped_to_inactive=False),
                decision=Decision(
                    action=SessionAction.REMOVE_MISSING,
                    reason="folder missing",
                    destructive=False,
                ),
                pid_needs_refresh=False,
                found_pid=None,
            )
        }

        cleanup_stale_sessions(
            workspace_base=str(tmp_path),
            assessments=assessments,
            dry_run=False,
        )

        post_cleanup_sessions = load_sessions()["sessions"]
        # Discard captured stdout from cleanup so the assertions only inspect
        # what display_status_table renders.
        capsys.readouterr()

        display_status_table(
            sessions=post_cleanup_sessions,
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={},
            repo_filter=None,
            cached_issues_by_repo=cached_issues_by_repo,
        )

        captured = capsys.readouterr()
        assert "#188" not in captured.out
        assert folder_name not in captured.out
