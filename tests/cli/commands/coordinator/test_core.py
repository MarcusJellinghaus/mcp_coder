"""Tests for coordinator core.py functions.

This module contains tests for:
- Configuration management functions (load_repo_config, validate_repo_config, get_jenkins_credentials)
- Cache refresh settings (get_cache_refresh_minutes - moved to utils.user_config)
- Issue filtering functions (get_eligible_issues)
- Workflow dispatch function (dispatch_workflow)
- Cache file operations (_get_cache_file_path, _load_cache_file, _save_cache_file)
- Cache staleness logging (_log_stale_cache_entries)
- Cached issue retrieval (get_cached_eligible_issues)
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    dispatch_workflow,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
from mcp_coder.utils.github_operations.issues import (
    CacheData,
    IssueData,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
)
from mcp_coder.utils.user_config import get_cache_refresh_minutes


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_success(self, mock_get_config: MagicMock) -> None:
        """Test successful loading of repository configuration."""
        # Setup - return batch config values dict
        mock_get_config.return_value = {
            (
                "coordinator.repos.mcp_coder",
                "repo_url",
            ): "https://github.com/user/repo.git",
            ("coordinator.repos.mcp_coder", "executor_job_path"): "Folder/job-name",
            ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
            ("coordinator.repos.mcp_coder", "executor_os"): None,
        }

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify
        assert result is not None
        assert result["repo_url"] == "https://github.com/user/repo.git"
        assert result["executor_job_path"] == "Folder/job-name"
        assert result["github_credentials_id"] == "github-pat"
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_missing_repo(self, mock_get_config: MagicMock) -> None:
        """Test that missing repository returns dict with None values."""
        # Setup - return dict with None values for all keys
        mock_get_config.return_value = {
            ("coordinator.repos.nonexistent_repo", "repo_url"): None,
            ("coordinator.repos.nonexistent_repo", "executor_job_path"): None,
            ("coordinator.repos.nonexistent_repo", "github_credentials_id"): None,
            ("coordinator.repos.nonexistent_repo", "executor_os"): None,
        }

        # Execute
        result = load_repo_config("nonexistent_repo")

        # Verify - returns dict with None values
        assert result is not None
        assert result["repo_url"] is None
        assert result["executor_job_path"] is None
        assert result["github_credentials_id"] is None
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_defaults_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os defaults to 'linux' when not specified."""
        # Setup - return batch config values dict with executor_os as None
        mock_get_config.return_value = {
            (
                "coordinator.repos.test_repo",
                "repo_url",
            ): "https://github.com/test/repo.git",
            ("coordinator.repos.test_repo", "executor_job_path"): "Tests/test",
            ("coordinator.repos.test_repo", "github_credentials_id"): "cred-id",
            ("coordinator.repos.test_repo", "executor_os"): None,  # Not in config
        }

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "linux"

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_normalizes_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os is normalized to lowercase."""
        # Setup - return batch config values dict with mixed case executor_os
        mock_get_config.return_value = {
            (
                "coordinator.repos.test_repo",
                "repo_url",
            ): "https://github.com/test/repo.git",
            ("coordinator.repos.test_repo", "executor_job_path"): "Tests/test",
            ("coordinator.repos.test_repo", "github_credentials_id"): "cred-id",
            ("coordinator.repos.test_repo", "executor_os"): "Windows",  # Mixed case
        }

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "windows"  # Normalized to lowercase


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""

    def test_validate_repo_config_complete(self) -> None:
        """Test validation passes for complete configuration."""
        # Setup
        config: dict[str, Optional[str]] = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Execute - should not raise exception
        validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_repo_url(self) -> None:
        """Test validation fails when repo_url is missing."""
        # Setup
        config = {
            "repo_url": None,
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Config file:.*value for field 'repo_url' missing"
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_executor_job_path(self) -> None:
        """Test validation fails when executor_job_path is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": None,
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'executor_job_path' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_github_credentials_id(self) -> None:
        """Test validation fails when github_credentials_id is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "Folder/job-name",
            "github_credentials_id": None,
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'github_credentials_id' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_invalid_executor_os(self) -> None:
        """Test validation fails for invalid executor_os values."""
        # Setup
        config: dict[str, Optional[str]] = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/test",
            "github_credentials_id": "cred-id",
            "executor_os": "macos",  # Invalid value (already normalized to lowercase)
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match=r"executor_os.*invalid.*got.*macos.*windows.*linux.*case-insensitive",
        ):
            validate_repo_config("test_repo", config)

    def test_validate_repo_config_valid_executor_os(self) -> None:
        """Test validation passes for valid executor_os values (case-insensitive)."""
        # Test both lowercase (normalized) values
        for os_value in ["windows", "linux"]:
            # Setup
            config: dict[str, Optional[str]] = {
                "repo_url": "https://github.com/test/repo.git",
                "executor_job_path": "Tests/test",
                "github_credentials_id": "cred-id",
                "executor_os": os_value,  # Already normalized to lowercase by load_repo_config
            }

            # Execute & Verify - Should not raise
            validate_repo_config("test_repo", config)


class TestGetJenkinsCredentials:
    """Tests for get_jenkins_credentials function."""

    def test_get_jenkins_credentials_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading credentials from environment variables."""
        # Setup
        monkeypatch.setenv("JENKINS_URL", "https://jenkins.example.com")
        monkeypatch.setenv("JENKINS_USER", "testuser")
        monkeypatch.setenv("JENKINS_TOKEN", "testtoken123")

        # Execute
        server_url, username, api_token = get_jenkins_credentials()

        # Verify
        assert server_url == "https://jenkins.example.com"
        assert username == "testuser"
        assert api_token == "testtoken123"

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_get_jenkins_credentials_from_config(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading credentials from config file."""
        # Setup - clear any env vars
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        # Setup - return batch config values dict
        mock_get_config.return_value = {
            ("jenkins", "server_url"): "https://jenkins.config.com",
            ("jenkins", "username"): "configuser",
            ("jenkins", "api_token"): "configtoken456",
        }

        # Execute
        server_url, username, api_token = get_jenkins_credentials()

        # Verify
        assert server_url == "https://jenkins.config.com"
        assert username == "configuser"
        assert api_token == "configtoken456"


class TestGetCacheRefreshMinutes:
    """Tests for get_cache_refresh_minutes function.

    Note: This function has been moved to utils.user_config module.
    These tests patch the new location.
    """

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_default(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test default value when config not set."""
        # Setup - return batch config values dict with None value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): None,
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # 24 hours

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_custom_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test custom value from config."""
        # Setup - return batch config values dict with custom value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): "720",
        }

        result = get_cache_refresh_minutes()
        assert result == 720  # 12 hours

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_invalid_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for invalid values."""
        # Setup - return batch config values dict with invalid value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): "invalid",
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_negative_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for negative values."""
        # Setup - return batch config values dict with negative value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): "-60",
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default


class TestGetEligibleIssues:
    """Tests for get_eligible_issues function."""

    @patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
    def test_get_eligible_issues_filters_by_bot_pickup_labels(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test filtering issues by bot_pickup labels."""
        # Setup - Mock label configuration
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Mock IssueManager instance
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Mock issue list with mixed labels
        mock_issue_manager.list_issues.return_value = [
            # Issue with valid bot_pickup label - should be included
            IssueData(
                number=1,
                title="Issue 1",
                body="",
                state="open",
                labels=["status-02:awaiting-planning", "enhancement"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/1",
                locked=False,
            ),
            # Issue with no bot_pickup label - should be excluded
            IssueData(
                number=2,
                title="Issue 2",
                body="",
                state="open",
                labels=["status-01:created", "bug"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/2",
                locked=False,
            ),
            # Another valid issue with bot_pickup label - should be included
            IssueData(
                number=4,
                title="Issue 4",
                body="",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/4",
                locked=False,
            ),
        ]

        # Execute
        result = get_eligible_issues(mock_issue_manager)

        # Verify - only issues with exactly one bot_pickup label
        assert len(result) == 2
        assert result[0]["number"] == 4  # status-08 has highest priority
        assert result[1]["number"] == 1  # status-02 has lower priority

        # Verify IssueManager.list_issues was called with correct params
        mock_issue_manager.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )


class TestDispatchWorkflow:
    """Tests for dispatch_workflow function."""

    @patch("mcp_coder.cli.commands.coordinator.core.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.core.JenkinsClient")
    def test_dispatch_workflow_create_plan(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test dispatching create-plan workflow."""
        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-02:awaiting-planning label
        issue = IssueData(
            number=123,
            title="Add feature X",
            body="Description of feature",
            state="open",
            labels=["status-02:awaiting-planning", "enhancement"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/123",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Mock Jenkins responses
        mock_jenkins.start_job.return_value = 98765  # Queue ID
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued")

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="create-plan",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify - Jenkins job started with correct parameters
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        executor_path = call_args[0][0]
        params = call_args[0][1]

        # Verify executor path
        assert executor_path == "MCP_Coder/executor-test"

        # Verify job parameters
        assert params["REPO_URL"] == "https://github.com/user/repo.git"
        assert params["BRANCH_NAME"] == "main"  # create-plan uses main branch
        assert params["GITHUB_CREDENTIALS_ID"] == "github-pat-123"

        # Verify COMMAND contains expected elements for create-plan
        command = params["COMMAND"]
        assert "git checkout main" in command
        assert "git pull" in command
        assert "mcp-coder --log-level INFO create-plan 123" in command

    def test_dispatch_workflow_handles_missing_branch_gracefully(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that dispatch_workflow logs warning and returns early when no branch found."""
        # Setup - Mock issue with status-08:ready-pr label (requires branch)
        issue: IssueData = {
            "number": 156,
            "title": "Create PR for feature",
            "body": "Feature ready for PR",
            "state": "open",
            "labels": ["status-08:ready-pr"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "updated_at": "2025-12-31T09:00:00Z",
            "url": "https://github.com/test/repo/issues/156",
            "locked": False,
        }

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Mock get_linked_branches to return empty list (missing branch scenario)
        mock_branch_mgr.get_linked_branches.return_value = []

        # Set up logging capture
        caplog.set_level(logging.WARNING, logger="mcp_coder.cli.commands.coordinator")

        # Execute - should complete gracefully without raising exception
        dispatch_workflow(
            issue=issue,
            workflow_name="create-pr",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify branch manager was called with correct issue number
        mock_branch_mgr.get_linked_branches.assert_called_once_with(156)

        # Verify warning was logged with correct message
        assert (
            "No linked branch found for issue #156, skipping workflow dispatch"
            in caplog.text
        )

        # Verify no Jenkins job was triggered (should return early)
        mock_jenkins.start_job.assert_not_called()

        # Verify no label updates occurred (should return early)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    def test_dispatch_workflow_preserves_existing_behavior_with_valid_branch(
        self,
    ) -> None:
        """Test that existing functionality works unchanged when branch exists."""
        # Setup - Mock issue with status-05:plan-ready label (requires branch)
        issue: IssueData = {
            "number": 123,
            "title": "Implement feature",
            "body": "Plan is ready for implementation",
            "state": "open",
            "labels": ["status-05:plan-ready"],
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "updated_at": "2025-12-31T09:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "locked": False,
        }

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/test/repo.git",
            "executor_job_path": "Tests/executor",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Mock get_linked_branches to return valid branch
        mock_branch_mgr.get_linked_branches.return_value = ["feature/issue-123"]

        # Mock Jenkins responses
        mock_jenkins.start_job.return_value = 98765
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued", url=None)
        mock_jenkins._client.server = "https://jenkins.test.com"

        # Execute - should complete successfully
        dispatch_workflow(
            issue=issue,
            workflow_name="implement",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify branch manager was called
        mock_branch_mgr.get_linked_branches.assert_called_once_with(123)

        # Verify Jenkins job was triggered with correct branch
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        params = call_args[0][1]
        assert params["BRANCH_NAME"] == "feature/issue-123"

        # Verify label updates occurred
        mock_issue_mgr.remove_labels.assert_called_once_with(
            123, "status-05:plan-ready"
        )
        mock_issue_mgr.add_labels.assert_called_once_with(123, "status-06:implementing")


class TestCacheFilePath:
    """Tests for _get_cache_file_path function."""

    def test_get_cache_file_path_basic(self) -> None:
        """Test basic cache file path generation."""
        from mcp_coder.utils.github_operations.github_utils import RepoIdentifier

        repo_identifier = RepoIdentifier.from_full_name("owner/repo")
        path = _get_cache_file_path(repo_identifier)

        expected_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
        expected_file = expected_dir / "owner_repo.issues.json"

        assert path == expected_file

    def test_get_cache_file_path_complex_names(self) -> None:
        """Test cache file path with complex repository names."""
        from mcp_coder.utils.github_operations.github_utils import RepoIdentifier

        test_cases = [
            ("anthropics/claude-code", "anthropics_claude-code.issues.json"),
            ("user/repo-with-dashes", "user_repo-with-dashes.issues.json"),
            ("org/very.long.repo.name", "org_very.long.repo.name.issues.json"),
        ]

        for full_name, expected_filename in test_cases:
            repo_identifier = RepoIdentifier.from_full_name(full_name)
            path = _get_cache_file_path(repo_identifier)
            assert path.name == expected_filename


class TestCacheFileOperations:
    """Tests for cache file load/save operations."""

    def test_load_cache_file_nonexistent(self) -> None:
        """Test loading non-existent cache file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "nonexistent.json"
            result = _load_cache_file(cache_path)

            assert result == {"last_checked": None, "issues": {}}

    def test_load_cache_file_valid(self) -> None:
        """Test loading valid cache file."""
        sample_cache_data = {
            "last_checked": "2025-12-31T10:30:00Z",
            "issues": {
                "123": {
                    "number": 123,
                    "state": "open",
                    "labels": ["status-02:awaiting-planning"],
                    "updated_at": "2025-12-31T09:00:00Z",
                    "url": "https://github.com/test/repo/issues/123",
                    "title": "Test issue",
                    "body": "Test issue body",
                    "assignees": [],
                    "user": "testuser",
                    "created_at": "2025-12-31T08:00:00Z",
                    "locked": False,
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            cache_path.write_text(json.dumps(sample_cache_data))

            result = _load_cache_file(cache_path)
            assert result == sample_cache_data

    def test_load_cache_file_invalid_json(self) -> None:
        """Test loading corrupted JSON file returns empty structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "invalid.json"
            cache_path.write_text("invalid json content")

            result = _load_cache_file(cache_path)
            assert result == {"last_checked": None, "issues": {}}

    def test_save_cache_file_success(self) -> None:
        """Test successful cache file save with atomic write."""
        sample_cache_data: CacheData = {
            "last_checked": "2025-12-31T10:30:00Z",
            "issues": {
                "123": {
                    "number": 123,
                    "state": "open",
                    "labels": ["bug"],
                    "title": "Test issue",
                    "body": "Test issue body",
                    "assignees": [],
                    "user": "testuser",
                    "created_at": "2025-12-31T08:00:00Z",
                    "updated_at": "2025-12-31T09:00:00Z",
                    "url": "https://github.com/test/repo/issues/123",
                    "locked": False,
                }
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "subdir" / "cache.json"

            result = _save_cache_file(cache_path, sample_cache_data)
            assert result is True

            # Verify file was created and data is correct
            assert cache_path.exists()
            saved_data = json.loads(cache_path.read_text())
            assert saved_data == sample_cache_data


class TestStalenessLogging:
    """Tests for _log_stale_cache_entries function."""

    def test_log_stale_cache_entries_state_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue state changes."""
        caplog.set_level(
            logging.INFO, logger="mcp_coder.utils.github_operations.issues.cache"
        )

        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "closed",
                "labels": ["bug"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }

        _log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached state 'open' != actual 'closed'" in caplog.text

    def test_log_stale_cache_entries_label_change(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test logging when issue labels change."""
        caplog.set_level(
            logging.INFO, logger="mcp_coder.utils.github_operations.issues.cache"
        )

        cached_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }
        fresh_issues: Dict[str, IssueData] = {
            "123": {
                "number": 123,
                "state": "open",
                "labels": ["status-03:planning"],
                "assignees": [],
                "user": "testuser",
                "created_at": "2025-12-31T08:00:00Z",
                "locked": False,
                "title": "Test",
                "body": "Test",
                "url": "http://test.com",
                "updated_at": "2025-12-31T08:00:00Z",
            }
        }

        _log_stale_cache_entries(cached_issues, fresh_issues)

        assert "Issue #123: cached labels" in caplog.text
        assert "status-02:awaiting-planning" in caplog.text
        assert "status-03:planning" in caplog.text


class TestGetCachedEligibleIssues:
    """Tests for get_cached_eligible_issues wrapper function.

    Note: get_cached_eligible_issues is now a thin wrapper that:
    1. Calls get_all_cached_issues() from issues.cache module
    2. Filters results using _filter_eligible_issues()
    3. Falls back to get_eligible_issues() on errors

    These tests verify the wrapper behavior, not the underlying cache operations
    (which are tested in tests/utils/github_operations/test_issues.cache.py).
    """

    @pytest.fixture
    def sample_issue(self) -> IssueData:
        """Sample issue data for testing."""
        return {
            "number": 123,
            "state": "open",
            "labels": ["status-02:awaiting-planning"],
            "updated_at": "2025-12-31T09:00:00Z",
            "url": "https://github.com/test/repo/issues/123",
            "title": "Test issue",
            "body": "Test issue body",
            "assignees": [],
            "user": "testuser",
            "created_at": "2025-12-31T08:00:00Z",
            "locked": False,
        }

    @pytest.fixture
    def mock_issue_manager(self) -> Mock:
        """Mock IssueManager for testing."""
        manager = Mock()
        manager.list_issues.return_value = []
        return manager

    def test_get_cached_eligible_issues_calls_get_all_cached_issues(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that wrapper calls get_all_cached_issues and filters results."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                repo_full_name="owner/repo",
                issue_manager=mock_issue_manager,
                force_refresh=False,
                cache_refresh_minutes=1440,
            )
            mock_filter.assert_called_once_with([sample_issue])

    def test_get_cached_eligible_issues_passes_force_refresh(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that force_refresh parameter is passed through."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_issue_manager, force_refresh=True
            )

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                repo_full_name="owner/repo",
                issue_manager=mock_issue_manager,
                force_refresh=True,
                cache_refresh_minutes=1440,
            )

    def test_get_cached_eligible_issues_passes_cache_refresh_minutes(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that cache_refresh_minutes parameter is passed through."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_issue_manager, cache_refresh_minutes=720
            )

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                repo_full_name="owner/repo",
                issue_manager=mock_issue_manager,
                force_refresh=False,
                cache_refresh_minutes=720,
            )

    def test_get_cached_eligible_issues_fallback_on_error(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test graceful fallback when cache operations fail."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues",
                side_effect=ValueError("Cache error"),
            ),
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_eligible_issues"
            ) as mock_fallback,
        ):
            mock_fallback.return_value = []

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            # Should fall back to get_eligible_issues
            assert result == []
            mock_fallback.assert_called_once_with(mock_issue_manager)
