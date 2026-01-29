"""Test status display functions for VSCode Claude."""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.vscodeclaude.status import (
    check_folder_dirty,
    display_status_table,
    get_issue_current_status,
    get_next_action,
    is_issue_closed,
    is_session_stale,
)
from mcp_coder.utils.vscodeclaude.types import VSCodeClaudeSession


class TestStatusDisplay:
    """Test status table and display functions."""

    def test_get_issue_current_status_returns_status(self) -> None:
        """Returns status label and open state when found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "open",
            "labels": ["status-07:code-review", "other-label"],
        }

        status, is_open = get_issue_current_status(mock_manager, 123)

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

        status, is_open = get_issue_current_status(mock_manager, 123)

        assert status == "status-07:code-review"
        assert is_open is False

    def test_get_issue_current_status_returns_none_no_status(self) -> None:
        """Returns None status when no status label found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "open",
            "labels": ["other-label"],
        }

        status, is_open = get_issue_current_status(mock_manager, 123)

        assert status is None
        assert is_open is True

    def test_get_issue_current_status_returns_none_on_error(self) -> None:
        """Returns None and False on API error."""
        mock_manager = Mock()
        mock_manager.get_issue.side_effect = Exception("API error")

        status, is_open = get_issue_current_status(mock_manager, 123)

        assert status is None
        assert is_open is False

    def test_get_issue_current_status_returns_none_issue_not_found(self) -> None:
        """Returns None and False when issue not found."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = None

        status, is_open = get_issue_current_status(mock_manager, 123)

        assert status is None
        assert is_open is False

    def test_is_session_stale_same_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False when status unchanged."""
        mock_issue = {"state": "open", "labels": ["status-07:code-review"]}
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
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

        assert is_session_stale(session) is False

    def test_is_session_stale_status_changed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when status changed."""
        mock_issue = {"state": "open", "labels": ["status-08:ready-pr"]}  # Changed
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
        )

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",  # Original
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        assert is_session_stale(session) is True

    def test_is_session_stale_no_status_label(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False when open issue has no status label (logs warning)."""
        mock_issue = {"state": "open", "labels": ["other-label"]}  # No status
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
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

        # Open issue without status label - should NOT be stale
        assert is_session_stale(session) is False

    def test_is_session_stale_returns_true_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when status cannot be retrieved."""
        mock_manager = Mock()
        mock_manager.get_issue.return_value = None  # Issue not found

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
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

        assert is_session_stale(session) is True

    def test_is_issue_closed_returns_true_when_closed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when issue is closed."""
        mock_issue = {"state": "closed", "labels": ["status-07:code-review"]}
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
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

        assert is_issue_closed(session) is True

    def test_is_issue_closed_returns_false_when_open(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False when issue is open."""
        mock_issue = {"state": "open", "labels": ["status-07:code-review"]}
        mock_manager = Mock()
        mock_manager.get_issue.return_value = mock_issue

        mock_coordinator = Mock()
        mock_coordinator.IssueManager.return_value = mock_manager

        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status._get_coordinator",
            lambda: mock_coordinator,
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

        assert is_issue_closed(session) is False

    def test_check_folder_dirty_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns False for clean git repo."""

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            result = Mock()
            result.stdout = ""  # Empty = clean
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert check_folder_dirty(tmp_path) is False

    def test_check_folder_dirty_with_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True when uncommitted changes exist."""

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            result = Mock()
            result.stdout = "M  file.py\n"  # Modified file
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        assert check_folder_dirty(tmp_path) is True

    def test_check_folder_dirty_returns_true_on_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns True (conservative) when git command fails."""

        def mock_run(cmd: list[str], **kwargs: Any) -> Mock:
            raise subprocess.CalledProcessError(1, cmd)

        monkeypatch.setattr("subprocess.run", mock_run)

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
            "mcp_coder.utils.vscodeclaude.status.is_issue_closed",
            lambda s: False,
        )

        # Mock check_vscode_running
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status.check_vscode_running",
            lambda pid: False,
        )

        # Mock check_folder_dirty
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status.check_folder_dirty",
            lambda path: False,
        )

        # Mock is_session_stale
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.status.is_session_stale",
            lambda s: False,
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
