"""End-to-end integration tests for coordinator module.

This module contains integration tests for:
- Coordinator run with caching (TestCoordinatorRunCacheIntegration)
- Cache update integration (TestCacheUpdateIntegration)
"""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    execute_coordinator_run,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData


class TestCoordinatorRunCacheIntegration:
    """Integration tests for coordinator run with caching."""

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_with_force_refresh(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
    ) -> None:
        """Test execute_coordinator_run with force_refresh flag."""
        # Setup - Mock args with force_refresh enabled
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=True,  # Force refresh enabled
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock eligible issues from cache (force refresh scenario)
        mock_get_cached_issues.return_value = [
            {
                "number": 456,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "title": "Force refresh test",
                "body": "Test",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/456",
                "locked": False,
            }
        ]

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - get_cached_eligible_issues was called with force_refresh=True
        mock_get_cached_issues.assert_called_once()
        call_args = mock_get_cached_issues.call_args[1]
        assert call_args["force_refresh"] is True
        assert call_args["repo_full_name"] == "user/test_repo"

        # Verify - dispatch_workflow was called for the issue
        mock_dispatch_workflow.assert_called_once()

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_cache_fallback(
        self,
        mock_create_config: MagicMock,
        mock_get_eligible_issues: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test execute_coordinator_run falls back when cache fails."""
        # Setup - Mock args
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config exists
        mock_create_config.return_value = False

        # Setup - Valid repo config
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Cache fails, fallback succeeds
        mock_get_cached_issues.side_effect = Exception("Cache error")
        mock_get_eligible_issues.return_value = []

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success despite cache failure)
        assert result == 0

        # Verify - Cache was attempted
        mock_get_cached_issues.assert_called_once()

        # Verify - Fallback was called
        mock_get_eligible_issues.assert_called_once_with(mock_issue_mgr)

        # Verify - Warning was logged
        assert "Cache failed" in caplog.text or "using direct fetch" in caplog.text

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_continues_processing_after_dispatch_failure(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that coordinator fails fast when dispatch_workflow raises an exception."""
        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Multiple eligible issues
        mock_get_cached_issues.return_value = [
            {
                "number": 156,
                "state": "open",
                "labels": ["status-08:ready-pr"],
                "title": "First issue - will fail",
                "body": "This will cause dispatch to fail",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/156",
                "locked": False,
            },
            {
                "number": 157,
                "state": "open",
                "labels": ["status-05:plan-ready"],
                "title": "Second issue - would succeed",
                "body": "This should not be processed due to fail-fast",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/157",
                "locked": False,
            },
        ]

        # Setup - First dispatch fails with ValueError (missing branch)
        mock_dispatch_workflow.side_effect = ValueError(
            "No linked branch found for issue #156"
        )

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (failure due to fail-fast)
        assert result == 1

        # Verify - dispatch_workflow was called only once (fail-fast behavior)
        assert mock_dispatch_workflow.call_count == 1

        # Verify - Error was logged
        assert "Failed processing issue #156" in caplog.text
        assert "No linked branch found for issue #156" in caplog.text


class TestCacheUpdateIntegration:
    """End-to-end tests for cache update integration in execute_coordinator_run."""

    @patch("mcp_coder.cli.commands.coordinator._update_issue_labels_in_cache")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_updates_cache_after_successful_dispatch(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_update_cache: MagicMock,
    ) -> None:
        """Test that successful dispatch updates cache labels."""
        # Setup - Mock args
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config exists
        mock_create_config.return_value = False

        # Setup - Valid repo config
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock issue with status-02:awaiting-planning
        test_issue = {
            "number": 123,
            "state": "open",
            "labels": ["status-02:awaiting-planning", "enhancement"],
            "title": "Test issue",
            "body": "Test",
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "updated_at": "2025-12-31T09:00:00Z",
            "url": "https://github.com/user/test_repo/issues/123",
            "locked": False,
        }
        mock_get_cached_issues.return_value = [test_issue]

        # Setup - dispatch_workflow succeeds (no exception)
        mock_dispatch_workflow.return_value = None

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - dispatch_workflow was called
        mock_dispatch_workflow.assert_called_once()

        # Verify - cache update was called with correct parameters
        mock_update_cache.assert_called_once_with(
            repo_full_name="user/test_repo",
            issue_number=123,
            old_label="status-02:awaiting-planning",
            new_label="status-03:planning",
        )

    @patch("mcp_coder.cli.commands.coordinator._update_issue_labels_in_cache")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_cache_update_failure_does_not_break_dispatch(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_update_cache: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that cache update errors don't affect dispatch success."""
        # Setup - Mock args
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config exists
        mock_create_config.return_value = False

        # Setup - Valid repo config
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock issue
        test_issue = {
            "number": 456,
            "state": "open",
            "labels": ["status-05:plan-ready"],
            "title": "Test issue",
            "body": "Test",
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "updated_at": "2025-12-31T09:00:00Z",
            "url": "https://github.com/user/test_repo/issues/456",
            "locked": False,
        }
        mock_get_cached_issues.return_value = [test_issue]

        # Setup - dispatch_workflow succeeds, but cache update fails
        mock_dispatch_workflow.return_value = None
        mock_update_cache.side_effect = Exception("Cache update error")

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success despite cache update failure)
        assert result == 0

        # Verify - dispatch_workflow was still called
        mock_dispatch_workflow.assert_called_once()

        # Verify - cache update was attempted
        mock_update_cache.assert_called_once_with(
            repo_full_name="user/test_repo",
            issue_number=456,
            old_label="status-05:plan-ready",
            new_label="status-06:implementing",
        )

        # Note: Cache update error is handled within _update_issue_labels_in_cache
        # itself and logged as warning, so no exception propagates to coordinator

    @patch("mcp_coder.cli.commands.coordinator._update_issue_labels_in_cache")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_multiple_dispatches_keep_cache_synchronized(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_cached_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_update_cache: MagicMock,
    ) -> None:
        """Test processing multiple issues keeps cache in sync."""
        # Setup - Mock args
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="test_repo",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config exists
        mock_create_config.return_value = False

        # Setup - Valid repo config
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/test_repo.git",
            "executor_job_path": "Test/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials
        mock_get_creds.return_value = ("https://jenkins.com", "user", "token")

        # Setup - Mock clients
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Multiple issues with different priority labels (sorted by priority)
        test_issues = [
            {
                "number": 101,
                "state": "open",
                "labels": ["status-08:ready-pr"],  # Highest priority
                "title": "PR ready issue",
                "body": "Test",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/101",
                "locked": False,
            },
            {
                "number": 102,
                "state": "open",
                "labels": ["status-05:plan-ready"],  # Medium priority
                "title": "Plan ready issue",
                "body": "Test",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/102",
                "locked": False,
            },
            {
                "number": 103,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],  # Lower priority
                "title": "Planning needed issue",
                "body": "Test",
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "updated_at": "2025-12-31T09:00:00Z",
                "url": "https://github.com/user/test_repo/issues/103",
                "locked": False,
            },
        ]
        mock_get_cached_issues.return_value = test_issues

        # Setup - All dispatches succeed
        mock_dispatch_workflow.return_value = None

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - dispatch_workflow was called for each issue (3 times)
        assert mock_dispatch_workflow.call_count == 3

        # Verify - cache update was called for each issue with correct mappings
        expected_cache_calls = [
            # Issue 101: status-08:ready-pr -> status-09:pr-creating
            ("user/test_repo", 101, "status-08:ready-pr", "status-09:pr-creating"),
            # Issue 102: status-05:plan-ready -> status-06:implementing
            ("user/test_repo", 102, "status-05:plan-ready", "status-06:implementing"),
            # Issue 103: status-02:awaiting-planning -> status-03:planning
            (
                "user/test_repo",
                103,
                "status-02:awaiting-planning",
                "status-03:planning",
            ),
        ]

        assert mock_update_cache.call_count == 3
        actual_calls = [
            (
                call[1]["repo_full_name"],
                call[1]["issue_number"],
                call[1]["old_label"],
                call[1]["new_label"],
            )
            for call in mock_update_cache.call_args_list
        ]

        assert actual_calls == expected_cache_calls
