"""Tests for coordinator CLI command."""

import argparse
import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    DEFAULT_TEST_COMMAND,
    DEFAULT_TEST_COMMAND_WINDOWS,
    _filter_eligible_issues,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
    dispatch_workflow,
    execute_coordinator_run,
    execute_coordinator_test,
    format_job_output,
    get_cache_refresh_minutes,
    get_cached_eligible_issues,
    get_eligible_issues,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
from mcp_coder.utils.github_operations.issue_branch_manager import (
    IssueBranchManager,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.jenkins_operations.models import JobStatus


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_success(self, mock_get_config: MagicMock) -> None:
        """Test successful loading of repository configuration."""

        # Setup
        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                (
                    "coordinator.repos.mcp_coder",
                    "repo_url",
                ): "https://github.com/user/repo.git",
                (
                    "coordinator.repos.mcp_coder",
                    "executor_job_path",
                ): "Folder/job-name",
                ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
                ("coordinator.repos.mcp_coder", "executor_os"): None,
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify
        assert result is not None
        assert result["repo_url"] == "https://github.com/user/repo.git"
        assert result["executor_job_path"] == "Folder/job-name"
        assert result["github_credentials_id"] == "github-pat"
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_missing_repo(self, mock_get_config: MagicMock) -> None:
        """Test that missing repository returns dict with None values."""
        # Setup - return None for all keys
        mock_get_config.return_value = None

        # Execute
        result = load_repo_config("nonexistent_repo")

        # Verify - returns dict with None values
        assert result is not None
        assert result["repo_url"] is None
        assert result["executor_job_path"] is None
        assert result["github_credentials_id"] is None
        assert result["executor_os"] == "linux"  # Default

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_defaults_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os defaults to 'linux' when not specified."""

        # Setup
        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                (
                    "coordinator.repos.test_repo",
                    "repo_url",
                ): "https://github.com/test/repo.git",
                (
                    "coordinator.repos.test_repo",
                    "executor_job_path",
                ): "Tests/test",
                (
                    "coordinator.repos.test_repo",
                    "github_credentials_id",
                ): "cred-id",
                (
                    "coordinator.repos.test_repo",
                    "executor_os",
                ): None,  # Not in config
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "linux"

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_normalizes_executor_os(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test executor_os is normalized to lowercase."""

        # Setup
        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                (
                    "coordinator.repos.test_repo",
                    "repo_url",
                ): "https://github.com/test/repo.git",
                (
                    "coordinator.repos.test_repo",
                    "executor_job_path",
                ): "Tests/test",
                (
                    "coordinator.repos.test_repo",
                    "github_credentials_id",
                ): "cred-id",
                (
                    "coordinator.repos.test_repo",
                    "executor_os",
                ): "Windows",  # Mixed case
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

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

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_jenkins_credentials_from_config(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading credentials from config file."""
        # Setup - clear any env vars
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                ("jenkins", "server_url"): "https://jenkins.config.com",
                ("jenkins", "username"): "configuser",
                ("jenkins", "api_token"): "configtoken456",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute
        server_url, username, api_token = get_jenkins_credentials()

        # Verify
        assert server_url == "https://jenkins.config.com"
        assert username == "configuser"
        assert api_token == "configtoken456"


class TestFormatJobOutput:
    """Tests for format_job_output function."""

    def test_format_job_output_with_url(self) -> None:
        """Test formatting output when job URL is available."""
        # Execute
        result = format_job_output(
            "MCP_Coder/test-job",
            12345,
            "https://jenkins.example.com/job/MCP_Coder/job/test-job/42/",
        )

        # Verify
        assert "Job triggered: MCP_Coder/test-job - test - queue: 12345" in result
        assert "https://jenkins.example.com/job/MCP_Coder/job/test-job/42/" in result

    def test_format_job_output_without_url(self) -> None:
        """Test formatting output when job URL is not yet available."""
        # Execute
        result = format_job_output("MCP_Coder/test-job", 12345, None)

        # Verify
        assert "Job triggered: MCP_Coder/test-job - test - queue: 12345" in result
        assert "will be available once build starts" in result


class TestExecuteCoordinatorTest:
    """Tests for execute_coordinator_test command function."""

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_success(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful command execution."""
        # Setup
        args = argparse.Namespace(
            repo_name="mcp_coder", branch_name="feature-x", log_level="DEBUG"
        )

        # Config already exists
        mock_create_config.return_value = False

        # Repo config is valid
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_job_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
            "executor_os": "linux",
        }

        # Jenkins credentials available
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345

        # Mock job status with URL
        mock_client.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url="https://jenkins:8080/queue/item/12345/",
        )

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 0

        # Verify JenkinsClient created with credentials
        mock_jenkins_class.assert_called_once_with(
            "http://jenkins:8080", "user", "token"
        )

        # Verify job started with correct params
        mock_client.start_job.assert_called_once_with(
            "MCP/test-job",
            {
                "REPO_URL": "https://github.com/user/repo.git",
                "BRANCH_NAME": "feature-x",
                "COMMAND": DEFAULT_TEST_COMMAND.format(log_level="DEBUG"),
                "GITHUB_CREDENTIALS_ID": "github-pat",
            },
        )

        # Verify output printed
        captured = capsys.readouterr()
        assert "Job triggered: MCP/test-job - test - queue: 12345" in captured.out
        assert "https://jenkins:8080/queue/item/12345/" in captured.out


class TestGetEligibleIssues:
    """Tests for get_eligible_issues function."""

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
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

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
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


class TestExecuteCoordinatorRun:
    """Tests for execute_coordinator_run function."""

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_single_repo_success(
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
        """Test successful execution for single repository using cache."""
        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
            force_refresh=False,
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_job_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
            "executor_os": "linux",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock Jenkins client
        mock_jenkins = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins

        # Setup - Mock IssueManager and IssueBranchManager
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock 2 eligible issues from cache
        mock_get_cached_issues.return_value = [
            IssueData(
                number=124,
                title="Create PR for feature",
                body="Ready for PR",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/124",
                locked=False,
            ),
            IssueData(
                number=123,
                title="Implement feature",
                body="Plan ready",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/123",
                locked=False,
            ),
        ]

        # Setup - Mock dispatch_workflow succeeds (no exception)
        mock_dispatch_workflow.return_value = None

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - get_cached_eligible_issues was called with correct parameters
        mock_get_cached_issues.assert_called_once()
        call_args = mock_get_cached_issues.call_args[1]
        assert call_args["repo_full_name"] == "user/mcp_coder"
        assert call_args["issue_manager"] == mock_issue_mgr
        assert call_args["force_refresh"] == False

        # Verify - dispatch_workflow was called twice (once for each issue)
        assert mock_dispatch_workflow.call_count == 2

    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_creates_config_if_missing(
        self, mock_create_config: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test config file is auto-created on first run."""
        # Setup
        args = argparse.Namespace(repo="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = True  # Config was created

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1  # Exit to let user configure
        mock_create_config.assert_called_once()

        # Verify message printed
        captured = capsys.readouterr()
        assert "Created default config file" in captured.out


# ========================================
# NEW CACHING FUNCTIONALITY TESTS
# ========================================


class TestCacheFilePath:
    """Tests for _get_cache_file_path function."""

    def test_get_cache_file_path_basic(self) -> None:
        """Test basic cache file path generation."""
        repo_name = "owner/repo"
        path = _get_cache_file_path(repo_name)

        expected_dir = Path.home() / ".mcp_coder" / "coordinator_cache"
        expected_file = expected_dir / "owner_repo.issues.json"

        assert path == expected_file

    def test_get_cache_file_path_complex_names(self) -> None:
        """Test cache file path with complex repository names."""
        test_cases = [
            ("anthropics/claude-code", "anthropics_claude-code.issues.json"),
            ("user/repo-with-dashes", "user_repo-with-dashes.issues.json"),
            ("org/very.long.repo.name", "org_very.long.repo.name.issues.json"),
        ]

        for repo_name, expected_filename in test_cases:
            path = _get_cache_file_path(repo_name)
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
        sample_cache_data = {
            "last_checked": "2025-12-31T10:30:00Z",
            "issues": {"123": {"number": 123, "state": "open"}},
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
        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator")

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
        caplog.set_level(logging.INFO, logger="mcp_coder.cli.commands.coordinator")

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
    """Tests for get_cached_eligible_issues main function."""

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

    def test_get_cached_eligible_issues_first_run(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test first run with no existing cache."""
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {"last_checked": None, "issues": {}}
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False
            )
            mock_save.assert_called_once()

    def test_get_cached_eligible_issues_incremental_update(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test incremental update with recent cache."""
        # Cache checked 30 minutes ago (within 24-hour window)
        cache_time = datetime.now().astimezone() - timedelta(minutes=30)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": cache_time.isoformat(),
                "issues": {"123": sample_issue},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            # Should call with since parameter for incremental update
            mock_issue_manager.list_issues.assert_called_once_with(
                state="open", include_pull_requests=False, since=cache_time
            )

    def test_get_cached_eligible_issues_duplicate_protection(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test duplicate protection skips recent checks."""
        # Cache checked 30 seconds ago (within 1-minute window)
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": recent_time.isoformat(),
                "issues": {},
            }

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == []
            # Should not call issue_manager at all due to duplicate protection
            mock_issue_manager.list_issues.assert_not_called()

    def test_get_cached_eligible_issues_force_refresh(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test force refresh bypasses cache and duplicate protection."""
        # Cache checked 30 seconds ago, but force_refresh should bypass it
        recent_time = datetime.now().astimezone() - timedelta(seconds=30)
        mock_issue_manager.list_issues.return_value = [sample_issue]

        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch("mcp_coder.cli.commands.coordinator._load_cache_file") as mock_load,
            patch("mcp_coder.cli.commands.coordinator._save_cache_file") as mock_save,
            patch(
                "mcp_coder.cli.commands.coordinator._filter_eligible_issues"
            ) as mock_filter,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_load.return_value = {
                "last_checked": recent_time.isoformat(),
                "issues": {},
            }
            mock_save.return_value = True
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_issue_manager, force_refresh=True
            )

            assert result == [sample_issue]
            # Should call issue_manager despite recent check
            mock_issue_manager.list_issues.assert_called_once()

    def test_get_cached_eligible_issues_corrupted_cache(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test graceful fallback when cache operations fail."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator._get_cache_file_path"
            ) as mock_path,
            patch(
                "mcp_coder.cli.commands.coordinator._load_cache_file",
                side_effect=Exception("Cache error"),
            ),
            patch(
                "mcp_coder.cli.commands.coordinator.get_eligible_issues"
            ) as mock_fallback,
        ):

            mock_path.return_value = Path("/fake/cache.json")
            mock_fallback.return_value = []

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            # Should fall back to get_eligible_issues
            assert result == []
            mock_fallback.assert_called_once_with(mock_issue_manager)


class TestGetCacheRefreshMinutes:
    """Tests for get_cache_refresh_minutes function."""

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_cache_refresh_minutes_default(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test default value when config not set."""
        mock_get_config.return_value = None

        result = get_cache_refresh_minutes()
        assert result == 1440  # 24 hours

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_cache_refresh_minutes_custom_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test custom value from config."""
        mock_get_config.return_value = "720"

        result = get_cache_refresh_minutes()
        assert result == 720  # 12 hours

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_cache_refresh_minutes_invalid_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for invalid values."""
        mock_get_config.return_value = "invalid"

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_cache_refresh_minutes_negative_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for negative values."""
        mock_get_config.return_value = "-60"

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default


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
