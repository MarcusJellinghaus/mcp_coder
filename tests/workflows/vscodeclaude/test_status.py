"""Test status display functions for VSCode Claude."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    check_folder_dirty,
    display_status_table,
    get_folder_git_status,
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


class TestCacheAwareFunctions:
    """Test cache-aware status functions."""

    def test_get_issue_current_status_uses_cache(self) -> None:
        """Verify cache lookup works without API call."""
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test issue",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/123",
                "locked": False,
            }
        }

        status, is_open = get_issue_current_status(123, cached_issues=cached_issues)

        assert status == "status-07:code-review"
        assert is_open is True

    def test_get_issue_current_status_cache_miss_uses_api(self) -> None:
        """Verify fallback to API when issue not in cache."""
        cached_issues: dict[int, IssueData] = {}  # Empty cache
        mock_manager = Mock()
        mock_manager.get_issue.return_value = {
            "state": "open",
            "labels": ["status-07:code-review"],
        }

        status, is_open = get_issue_current_status(
            123, cached_issues=cached_issues, issue_manager=mock_manager
        )

        assert status == "status-07:code-review"
        assert is_open is True
        mock_manager.get_issue.assert_called_once_with(123)

    def test_get_issue_current_status_raises_without_manager_or_cache(self) -> None:
        """Verify ValueError raised when neither cache nor manager provided."""
        with pytest.raises(ValueError, match="Either cached_issues or issue_manager"):
            get_issue_current_status(123)  # No cache, no manager

    def test_is_session_stale_uses_cache(self) -> None:
        """Verify is_session_stale uses cache when provided."""
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test issue",
                "body": "",
                "state": "open",
                "labels": ["status-07:code-review"],  # Same as session
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/123",
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

        # Should NOT be stale since status matches
        result = is_session_stale(session, cached_issues=cached_issues)
        assert result is False

    def test_is_session_stale_with_cache_detects_change(self) -> None:
        """Verify is_session_stale detects status change from cache."""
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test issue",
                "body": "",
                "state": "open",
                "labels": ["status-08:ready-pr"],  # Different from session
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/123",
                "locked": False,
            }
        }

        session: VSCodeClaudeSession = {
            "folder": "/test",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",  # Different from cache
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Should BE stale since status differs
        result = is_session_stale(session, cached_issues=cached_issues)
        assert result is True

    def test_is_issue_closed_uses_cache(self) -> None:
        """Verify is_issue_closed uses cache when provided."""
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test issue",
                "body": "",
                "state": "closed",  # Closed issue
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/123",
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

        result = is_issue_closed(session, cached_issues=cached_issues)
        assert result is True

    def test_is_issue_closed_with_cache_open_issue(self) -> None:
        """Verify is_issue_closed returns False for open issue from cache."""
        cached_issues: dict[int, IssueData] = {
            123: {
                "number": 123,
                "title": "Test issue",
                "body": "",
                "state": "open",  # Open issue
                "labels": ["status-07:code-review"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "https://github.com/owner/repo/issues/123",
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

        result = is_issue_closed(session, cached_issues=cached_issues)
        assert result is False


class TestGetNextActionBlocked:
    """Tests for get_next_action with blocked_label parameter."""

    def test_blocked_clean_returns_blocked_message(self) -> None:
        """Blocked + clean folder shows Blocked message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "Blocked (blocked)"

    def test_blocked_with_wait_label(self) -> None:
        """Blocked with wait label shows correct message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="wait",
        )
        assert result == "Blocked (wait)"

    def test_blocked_dirty_returns_manual(self) -> None:
        """Blocked + dirty folder shows Manual message."""
        result = get_next_action(
            is_stale=False,
            is_dirty=True,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "!! Manual"

    def test_blocked_but_running_returns_active(self) -> None:
        """Running VSCode takes priority over blocked."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=True,
            blocked_label="blocked",
        )
        assert result == "(active)"

    def test_blocked_and_stale_blocked_takes_priority(self) -> None:
        """Blocked takes priority over stale when both true."""
        result = get_next_action(
            is_stale=True,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "Blocked (blocked)"

    def test_none_blocked_label_normal_behavior(self) -> None:
        """None blocked_label maintains normal behavior."""
        # Not stale, not dirty, not running -> Restart
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label=None,
        )
        assert "Restart" in result

    def test_default_parameter_backward_compatible(self) -> None:
        """Function works without blocked_label parameter."""
        # Call without the new parameter
        result = get_next_action(
            is_stale=False, is_dirty=False, is_vscode_running=False
        )
        assert "Restart" in result

    def test_preserves_label_case_in_output(self) -> None:
        """Output preserves the case of the label passed in."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="Blocked",  # Capital B
        )
        assert result == "Blocked (Blocked)"

    def test_blocked_dirty_and_stale_returns_manual(self) -> None:
        """Blocked + dirty + stale still shows Manual message."""
        result = get_next_action(
            is_stale=True,
            is_dirty=True,
            is_vscode_running=False,
            blocked_label="blocked",
        )
        assert result == "!! Manual"


class TestGetFolderGitStatus:
    """Tests for get_folder_git_status function."""

    def test_returns_missing_when_folder_not_exists(self, tmp_path: Path) -> None:
        """Returns 'Missing' when folder does not exist."""
        non_existent = tmp_path / "does_not_exist"

        result = get_folder_git_status(non_existent)

        assert result == "Missing"

    def test_returns_no_git_when_not_a_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'No Git' when folder exists but is not a git repo."""
        from mcp_coder.utils.subprocess_runner import CalledProcessError

        folder = tmp_path / "not_a_repo"
        folder.mkdir()

        def mock_execute(cmd: list[str], options: Any = None) -> None:
            # git rev-parse fails for non-git folders
            if "rev-parse" in cmd:
                raise CalledProcessError(128, cmd)
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(folder)

        assert result == "No Git"

    def test_returns_clean_when_no_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Clean' when git repo has no uncommitted changes."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status --porcelain returns empty (clean)
            if "status" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout="",  # Empty = clean
                    stderr="",
                    timed_out=False,
                )
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Clean"

    def test_returns_dirty_when_has_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Dirty' when git repo has uncommitted changes."""
        from mcp_coder.utils.subprocess_runner import CommandResult

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status --porcelain returns modified file
            if "status" in cmd:
                return CommandResult(
                    return_code=0,
                    stdout="M file.py\n",  # Modified file
                    stderr="",
                    timed_out=False,
                )
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Dirty"

    def test_returns_error_when_git_status_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns 'Error' when git status command fails after rev-parse succeeds."""
        from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult

        call_count = {"rev_parse": 0}

        def mock_execute(cmd: list[str], options: Any = None) -> CommandResult:
            # git rev-parse succeeds (is a git repo)
            if "rev-parse" in cmd:
                call_count["rev_parse"] += 1
                return CommandResult(
                    return_code=0,
                    stdout=".git",
                    stderr="",
                    timed_out=False,
                )
            # git status fails
            if "status" in cmd:
                raise CalledProcessError(1, cmd)
            return CommandResult(return_code=0, stdout="", stderr="", timed_out=False)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.status.execute_subprocess",
            mock_execute,
        )

        result = get_folder_git_status(tmp_path)

        assert result == "Error"
        assert call_count["rev_parse"] == 1  # Verify rev-parse was called
