"""Tests for orchestrator cache functionality.

Tests the _build_cached_issues_by_repo() helper function and
restart_closed_sessions() integration with the cache.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


class TestBuildCachedIssuesByRepo:
    """Tests for _build_cached_issues_by_repo helper function."""

    def test_build_cache_groups_by_repo(self) -> None:
        """Test that sessions are grouped by repo and cache is built correctly.

        Given: Sessions for issues #414, #408 in "owner/repo"
               Session for issue #123 in "other/repo"
        When: Call _build_cached_issues_by_repo(sessions)
        Then:
        - Two cache fetch calls (one per repo)
        - First call: additional_issues=[414, 408]
        - Second call: additional_issues=[123]
        """
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            _build_cached_issues_by_repo,
        )

        # Create mock sessions
        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": "/path/to/owner-repo-414",
                "repo": "owner/repo",
                "issue_number": 414,
                "status": "status-04:plan-review",
                "vscode_pid": 1234,
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": "/path/to/owner-repo-408",
                "repo": "owner/repo",
                "issue_number": 408,
                "status": "status-04:plan-review",
                "vscode_pid": 1235,
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": "/path/to/other-repo-123",
                "repo": "other/repo",
                "issue_number": 123,
                "status": "status-01:created",
                "vscode_pid": 1236,
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            },
        ]

        # Mock issue data
        issue_414: IssueData = {
            "number": 414,
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 414",
            "body": "Body 414",
            "url": "http://test.com/414",
            "updated_at": "2025-12-31T08:00:00Z",
        }
        issue_408: IssueData = {
            "number": 408,
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 408",
            "body": "Body 408",
            "url": "http://test.com/408",
            "updated_at": "2025-12-31T08:00:00Z",
        }
        issue_100: IssueData = {
            "number": 100,
            "state": "open",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 100",
            "body": "Body 100",
            "url": "http://test.com/100",
            "updated_at": "2025-12-31T08:00:00Z",
        }
        issue_123: IssueData = {
            "number": 123,
            "state": "open",
            "labels": ["enhancement"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 123",
            "body": "Body 123",
            "url": "http://test.com/123",
            "updated_at": "2025-12-31T08:00:00Z",
        }

        with (
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.IssueManager"
            ) as mock_issue_manager_class,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues"
            ) as mock_get_cache,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.get_cache_refresh_minutes"
            ) as mock_refresh_minutes,
        ):
            # Mock IssueManager instantiation
            mock_issue_manager_class.return_value = Mock()

            # Mock get_cache_refresh_minutes
            mock_refresh_minutes.return_value = 60

            # Mock get_all_cached_issues to return different issues for different repos
            def get_cache_side_effect(
                repo_full_name: str,
                issue_manager: Mock,
                force_refresh: bool,
                cache_refresh_minutes: int,
                additional_issues: list[int],
            ) -> list[IssueData]:
                if repo_full_name == "owner/repo":
                    # Return both session issues (414, 408) and an open issue (100)
                    return [issue_414, issue_408, issue_100]
                elif repo_full_name == "other/repo":
                    # Return session issue (123)
                    return [issue_123]
                return []

            mock_get_cache.side_effect = get_cache_side_effect

            # Call the function
            result = _build_cached_issues_by_repo(sessions)

            # Verify get_all_cached_issues was called twice (once per repo)
            assert mock_get_cache.call_count == 2

            # Verify calls contain correct additional_issues
            calls = mock_get_cache.call_args_list

            # First call should be for "owner/repo" with additional_issues=[414, 408]
            owner_repo_call = next(
                (c for c in calls if c.kwargs["repo_full_name"] == "owner/repo"), None
            )
            assert owner_repo_call is not None
            assert set(owner_repo_call.kwargs["additional_issues"]) == {414, 408}

            # Second call should be for "other/repo" with additional_issues=[123]
            other_repo_call = next(
                (c for c in calls if c.kwargs["repo_full_name"] == "other/repo"), None
            )
            assert other_repo_call is not None
            assert other_repo_call.kwargs["additional_issues"] == [123]

            # Verify result structure
            assert "owner/repo" in result
            assert "other/repo" in result

            # Verify owner/repo has all issues (414, 408, 100)
            assert 414 in result["owner/repo"]
            assert 408 in result["owner/repo"]
            assert 100 in result["owner/repo"]

            # Verify other/repo has issue 123
            assert 123 in result["other/repo"]

    def test_build_cache_empty_sessions(self) -> None:
        """Test that empty sessions list returns empty dict.

        Given: No sessions exist
        When: Call _build_cached_issues_by_repo([])
        Then:
        - Empty dict returned
        - No cache fetches
        - No errors
        """
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            _build_cached_issues_by_repo,
        )

        with patch(
            "mcp_coder.workflows.vscodeclaude.orchestrator.get_all_cached_issues"
        ) as mock_get_cache:
            result = _build_cached_issues_by_repo([])

            # Verify no cache fetches
            assert mock_get_cache.call_count == 0

            # Verify empty dict
            assert result == {}


class TestRestartClosedSessions:
    """Tests for restart_closed_sessions() cache integration."""

    def test_restart_builds_cache_with_session_issues(self) -> None:
        """Test that restart builds cache with session issue numbers.

        Given:
        - No cached_issues_by_repo provided
        - Sessions exist for issues #414 (closed) and #100 (open)
        When: Call restart_closed_sessions()
        Then:
        - Cache is built with additional_issues=[414, 100]
        - Issue #414 is in cache (closed issue from session)
        - Issue #100 is in cache (open issue from session)
        """
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            restart_closed_sessions,
        )

        # Mock sessions
        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": "/path/to/owner-repo-414",
                "repo": "owner/repo",
                "issue_number": 414,
                "status": "status-04:plan-review",
                "vscode_pid": 9999,  # Non-existent PID
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            },
            {
                "folder": "/path/to/owner-repo-100",
                "repo": "owner/repo",
                "issue_number": 100,
                "status": "status-01:created",
                "vscode_pid": 9998,  # Non-existent PID
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            },
        ]

        # Mock issue data
        issue_414: IssueData = {
            "number": 414,
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 414",
            "body": "Body 414",
            "url": "http://test.com/414",
            "updated_at": "2025-12-31T08:00:00Z",
        }
        issue_100: IssueData = {
            "number": 100,
            "state": "open",
            "labels": ["bug", "status-01:created"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 100",
            "body": "Body 100",
            "url": "http://test.com/100",
            "updated_at": "2025-12-31T08:00:00Z",
        }

        with (
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions"
            ) as mock_load,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running"
            ) as mock_running,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder"
            ) as mock_window,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder"
            ) as mock_folder,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos"
            ) as mock_repos,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._build_cached_issues_by_repo"
            ) as mock_build_cache,
        ):
            # Setup mocks
            mock_load.return_value = {"sessions": sessions}
            mock_running.return_value = False  # VSCode not running
            mock_window.return_value = False  # No window open
            mock_folder.return_value = (False, None)  # Not open
            mock_repos.return_value = {"owner/repo"}

            # Mock _build_cached_issues_by_repo to return cache with both issues
            mock_build_cache.return_value = {
                "owner/repo": {414: issue_414, 100: issue_100}
            }

            # Call restart_closed_sessions without providing cache
            restart_closed_sessions()

            # Verify _build_cached_issues_by_repo was called with sessions
            mock_build_cache.assert_called_once_with(sessions)

    def test_restart_uses_provided_cache(self) -> None:
        """Test that provided cache is used instead of building new one.

        Given:
        - cached_issues_by_repo provided with issues
        - Sessions exist
        When: Call restart_closed_sessions(cached_issues_by_repo=...)
        Then:
        - Provided cache is used (not rebuilt)
        - No additional cache fetch calls
        """
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            restart_closed_sessions,
        )

        # Mock session
        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": "/path/to/owner-repo-414",
                "repo": "owner/repo",
                "issue_number": 414,
                "status": "status-04:plan-review",
                "vscode_pid": 9999,
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            }
        ]

        # Provided cache
        issue_414: IssueData = {
            "number": 414,
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 414",
            "body": "Body 414",
            "url": "http://test.com/414",
            "updated_at": "2025-12-31T08:00:00Z",
        }
        provided_cache = {"owner/repo": {414: issue_414}}

        with (
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions"
            ) as mock_load,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running"
            ) as mock_running,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder"
            ) as mock_window,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder"
            ) as mock_folder,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos"
            ) as mock_repos,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._build_cached_issues_by_repo"
            ) as mock_build_cache,
        ):
            # Setup mocks
            mock_load.return_value = {"sessions": sessions}
            mock_running.return_value = False
            mock_window.return_value = False
            mock_folder.return_value = (False, None)
            mock_repos.return_value = {"owner/repo"}

            # Call with provided cache
            restart_closed_sessions(cached_issues_by_repo=provided_cache)

            # Verify _build_cached_issues_by_repo was NOT called
            mock_build_cache.assert_not_called()

    def test_restart_skips_closed_issues(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that closed issues are detected and skipped.

        Given: Session exists for issue #414 (closed)
        When: Call restart_closed_sessions()
        Then:
        - Issue #414 is in cache (via additional_issues)
        - Issue #414 is detected as closed
        - Issue #414 is skipped (logged "Skipping closed issue")
        - No VSCode restart attempted
        """
        import logging

        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            restart_closed_sessions,
        )

        caplog.set_level(
            logging.INFO, logger="mcp_coder.workflows.vscodeclaude.orchestrator"
        )

        # Mock session
        sessions: list[VSCodeClaudeSession] = [
            {
                "folder": str(Path("/path/to/owner-repo-414")),
                "repo": "owner/repo",
                "issue_number": 414,
                "status": "status-04:plan-review",
                "vscode_pid": 9999,
                "started_at": "2025-01-01T00:00:00Z",
                "is_intervention": False,
            }
        ]

        # Mock closed issue
        issue_414: IssueData = {
            "number": 414,
            "state": "closed",
            "labels": ["bug"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
            "title": "Issue 414",
            "body": "Body 414",
            "url": "http://test.com/414",
            "updated_at": "2025-12-31T08:00:00Z",
        }

        with (
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions"
            ) as mock_load,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.check_vscode_running"
            ) as mock_running,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_window_open_for_folder"
            ) as mock_window,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.is_vscode_open_for_folder"
            ) as mock_folder,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._get_configured_repos"
            ) as mock_repos,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._build_cached_issues_by_repo"
            ) as mock_build_cache,
            patch("pathlib.Path.exists") as mock_exists,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.launch_vscode"
            ) as mock_launch,
        ):
            # Setup mocks
            mock_load.return_value = {"sessions": sessions}
            mock_running.return_value = False
            mock_window.return_value = False
            mock_folder.return_value = (False, None)
            mock_repos.return_value = {"owner/repo"}
            mock_build_cache.return_value = {"owner/repo": {414: issue_414}}
            mock_exists.return_value = True  # Folder exists

            # Call restart
            result = restart_closed_sessions()

            # Verify closed issue was skipped
            assert "Skipping closed issue #414" in caplog.text

            # Verify no VSCode launch
            mock_launch.assert_not_called()

            # Verify no sessions restarted
            assert len(result) == 0

    def test_restart_with_no_sessions(self) -> None:
        """Test restart with no sessions returns empty list.

        Given: No sessions exist
        When: Call restart_closed_sessions()
        Then:
        - Empty list returned
        - No cache fetches
        - No errors
        """
        from mcp_coder.workflows.vscodeclaude.orchestrator import (
            restart_closed_sessions,
        )

        with (
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator.load_sessions"
            ) as mock_load,
            patch(
                "mcp_coder.workflows.vscodeclaude.orchestrator._build_cached_issues_by_repo"
            ) as mock_build_cache,
        ):
            # No sessions
            mock_load.return_value = {"sessions": []}

            # Call restart
            result = restart_closed_sessions()

            # Verify no cache built
            mock_build_cache.assert_not_called()

            # Verify empty result
            assert result == []
