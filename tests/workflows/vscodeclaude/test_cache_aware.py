"""Test cache-aware status functions for VSCode Claude."""

from unittest.mock import Mock

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    get_issue_current_status,
    is_issue_closed,
    is_session_stale,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


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
        import pytest

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
