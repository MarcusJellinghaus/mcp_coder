"""Test status table and display functions for VSCode Claude."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    check_folder_dirty,
    display_status_table,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


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
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Handles empty sessions and issues."""
        display_status_table(sessions=[], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "No sessions" in captured.out or "Folder" in captured.out

    def test_display_status_table_with_session(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Displays session information."""

        # Mock is_issue_closed to return False (issue is open)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )

        # Mock check_vscode_running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        # Mock is_session_stale
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_session_stale",
            lambda s, cached_issues=None: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "test_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#123" in captured.out
        assert "owner/repo".split("/")[-1] in captured.out  # "repo"

    def test_display_status_table_with_eligible_issue(
        self,
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
            sessions=[], eligible_issues=eligible_issues, repo_filter=None
        )

        captured = capsys.readouterr()
        assert "#456" in captured.out
        assert "Create and start" in captured.out


class TestClosedIssuePrefixDisplay:
    """Test (Closed) prefix display for closed issues in status table."""

    def test_closed_issue_shows_closed_prefix_in_status(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with existing folder shows (Closed) prefix in status column."""
        # Create folder so it exists
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return True (issue is closed)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is clean
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Verify session is shown
        assert "#123" in captured.out
        # Verify "(Closed)" prefix appears in output
        assert "(Closed)" in captured.out

    def test_closed_issue_status_includes_original_status_label(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue status shows both (Closed) prefix and original status."""
        # Create folder so it exists
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return True
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is clean
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Should show both (Closed) prefix and status info
        assert "(Closed)" in captured.out
        assert "#456" in captured.out

    def test_closed_issue_shows_delete_action(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with clean folder shows Delete action."""
        # Create folder so it exists
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return True
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is clean
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Should show delete action for closed issue
        assert "Delete" in captured.out

    def test_closed_issue_dirty_folder_shows_manual_cleanup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with dirty folder shows Manual cleanup action."""
        # Create folder so it exists
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return True
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is DIRTY
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: True,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Should show (Closed) prefix
        assert "(Closed)" in captured.out
        # Should show Manual cleanup for dirty folder
        assert "Manual" in captured.out

    def test_closed_issue_missing_folder_is_skipped(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with missing folder is not shown in status table."""
        # Create a path that does NOT exist - session folder is missing
        missing_folder = tmp_path / "missing_folder"
        # Do NOT create the folder - it should not exist

        # Mock is_issue_closed to return True (issue is closed)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        # These mocks should NOT be called since session should be skipped
        # But we set them up anyway in case the implementation calls them
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(missing_folder),  # Folder does not exist
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Session with closed issue and missing folder should be SKIPPED
        # Nothing to clean up if folder doesn't exist
        assert "#789" not in captured.out
        assert "(Closed)" not in captured.out

    def test_closed_issue_existing_folder_is_shown(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closed issue with existing folder IS shown (contrast to missing folder)."""
        # Create folder so it exists
        existing_folder = tmp_path / "existing_folder"
        existing_folder.mkdir()

        # Mock is_issue_closed to return True (issue is closed)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(existing_folder),  # Folder EXISTS
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Session with closed issue and EXISTING folder should be shown
        # Needs cleanup since folder exists
        assert "#789" in captured.out
        assert "(Closed)" in captured.out

    def test_open_issue_does_not_show_closed_prefix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Open issue does not show (Closed) prefix."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return False (issue is open)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )

        # Mock check_vscode_running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        # Mock is_session_stale
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_session_stale",
            lambda s, cached_issues=None: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        # Should show the session
        assert "#123" in captured.out
        # Should NOT show (Closed) prefix
        assert "(Closed)" not in captured.out


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
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-02:awaiting-planning shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return False (issue is open)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is clean
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-02:awaiting-planning",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

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
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-05:awaiting-coding shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-05:awaiting-coding",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#456" in captured.out
        assert "Delete" in captured.out

    def test_bot_pickup_status_08_shows_delete_action(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-08:ready-pr shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-08:ready-pr",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#789" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_03_shows_delete_action(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-03:planning shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 101,
            "status": "status-03:planning",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#101" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_06_shows_delete_action(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-06:coding shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 202,
            "status": "status-06:coding",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#202" in captured.out
        assert "Delete" in captured.out

    def test_bot_busy_status_09_shows_delete_action(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-09:creating-pr shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 303,
            "status": "status-09:creating-pr",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#303" in captured.out
        assert "Delete" in captured.out

    def test_bot_stage_dirty_folder_shows_manual_cleanup(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Bot stage session with dirty folder shows Manual cleanup."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        # Folder is DIRTY
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: True,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 404,
            "status": "status-02:awaiting-planning",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#404" in captured.out
        # Dirty folder should show Manual cleanup
        assert "Manual" in captured.out

    def test_eligible_status_shows_restart_not_delete(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Eligible status (01, 04, 07) shows Restart, NOT Delete."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )
        # Status is the same as session (not stale from status change)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_session_stale",
            lambda s, cached_issues=None: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 505,
            "status": "status-07:code-review",  # Eligible status
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

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
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Session at status-10:pr-created shows Delete action."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Mock is_issue_closed to return False (issue is open)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )

        # Mock check_vscode_running - not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty - folder is clean
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-10:pr-created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

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
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with dirty folder shows Manual cleanup."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        # Folder is DIRTY
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: True,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-10:pr-created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#456" in captured.out
        # Dirty folder should show Manual cleanup
        assert "Manual" in captured.out

    def test_pr_created_with_vscode_running_shows_active(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with VSCode running shows (active)."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: False,
        )
        # VSCode IS running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-10:pr-created",
            "vscode_pid": 12345,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#789" in captured.out
        # Running VSCode should show (active)
        assert "(active)" in captured.out

    def test_pr_created_closed_issue_shows_closed_prefix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """PR-created session with closed issue shows (Closed) prefix and Delete."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        # Issue is closed
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.is_issue_closed",
            lambda s, cached_issues=None: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 999,
            "status": "status-10:pr-created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        display_status_table(sessions=[session], eligible_issues=[], repo_filter=None)

        captured = capsys.readouterr()
        assert "#999" in captured.out
        # Should show (Closed) prefix for closed issue
        assert "(Closed)" in captured.out
        # Should still show Delete action
        assert "Delete" in captured.out
