"""Tests for coordinator CLI command."""

import argparse
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    DEFAULT_TEST_COMMAND,
    execute_coordinator_test,
    format_job_output,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
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
                    "executor_test_path",
                ): "Folder/job-name",
                ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify
        assert result is not None
        assert result["repo_url"] == "https://github.com/user/repo.git"
        assert result["executor_test_path"] == "Folder/job-name"
        assert result["github_credentials_id"] == "github-pat"

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
        assert result["executor_test_path"] is None
        assert result["github_credentials_id"] is None

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_handles_missing_config_file(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test graceful handling when config file doesn't exist."""
        # Setup - return None for all keys (simulating missing config)
        mock_get_config.return_value = None

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify - should return dict with None values, not raise exception
        assert result is not None
        assert result["repo_url"] is None
        assert result["executor_test_path"] is None
        assert result["github_credentials_id"] is None


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""

    def test_validate_repo_config_complete(self) -> None:
        """Test validation passes for complete configuration."""
        # Setup
        config: dict[str, Optional[str]] = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute - should not raise exception
        validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_repo_url(self) -> None:
        """Test validation fails when repo_url is missing."""
        # Setup
        config = {
            "repo_url": None,
            "executor_test_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Config file:.*value for field 'repo_url' missing"
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_executor_test_path(self) -> None:
        """Test validation fails when executor_test_path is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": None,
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'executor_test_path' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_github_credentials_id(self) -> None:
        """Test validation fails when github_credentials_id is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "Folder/job-name",
            "github_credentials_id": None,
        }

        # Execute & Verify
        with pytest.raises(
            ValueError,
            match="Config file:.*value for field 'github_credentials_id' missing",
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_multiple_missing_fields(self) -> None:
        """Test validation reports multiple missing fields."""
        # Setup
        config = {
            "repo_url": None,
            "executor_test_path": None,
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            validate_repo_config("mcp_coder", config)

        error_msg = str(exc_info.value)
        assert "Config file:" in error_msg
        assert "values for fields 'repo_url', 'executor_test_path' missing" in error_msg


class TestGetJenkinsCredentials:
    """Tests for get_jenkins_credentials function."""

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_jenkins_credentials_from_env(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
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

        # Verify config was not called (env vars take priority)
        mock_get_config.assert_not_called()

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

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_jenkins_credentials_missing_server_url(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error when server_url is missing."""
        # Setup
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                ("jenkins", "username"): "configuser",
                ("jenkins", "api_token"): "configtoken456",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Jenkins configuration incomplete.*server_url"
        ):
            get_jenkins_credentials()

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_jenkins_credentials_missing_username(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error when username is missing."""
        # Setup
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                ("jenkins", "server_url"): "https://jenkins.config.com",
                ("jenkins", "api_token"): "configtoken456",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Jenkins configuration incomplete.*username"
        ):
            get_jenkins_credentials()

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_get_jenkins_credentials_missing_api_token(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error when api_token is missing."""
        # Setup
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                ("jenkins", "server_url"): "https://jenkins.config.com",
                ("jenkins", "username"): "configuser",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute & Verify
        with pytest.raises(
            ValueError, match="Jenkins configuration incomplete.*api_token"
        ):
            get_jenkins_credentials()


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
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")

        # Config already exists
        mock_create_config.return_value = False

        # Repo config is valid
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
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
                "COMMAND": DEFAULT_TEST_COMMAND,
                "GITHUB_CREDENTIALS_ID": "github-pat",
            },
        )

        # Verify output printed
        captured = capsys.readouterr()
        assert "Job triggered: MCP/test-job - test - queue: 12345" in captured.out
        assert "https://jenkins:8080/queue/item/12345/" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_creates_config_if_missing(
        self, mock_create_config: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test config file is auto-created on first run."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = True  # Config was created

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1  # Exit to let user configure
        mock_create_config.assert_called_once()

        # Verify message printed
        captured = capsys.readouterr()
        assert "Created default config file" in captured.out
        assert (
            "config.toml" in captured.out
        )  # Check for filename, not specific path format

    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_repo_not_found(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error when repository not in config."""
        # Setup
        args = argparse.Namespace(repo_name="nonexistent", branch_name="feature-x")
        mock_create_config.return_value = False
        # Repo not found - all values None
        mock_load_repo.return_value = {
            "repo_url": None,
            "executor_test_path": None,
            "github_credentials_id": None,
        }

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Config file:" in captured.err
        assert "missing" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_incomplete_repo_config(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error when repository config incomplete."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        # Missing github_credentials_id
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": None,
        }

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Config file:" in captured.err
        assert "github_credentials_id" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_missing_jenkins_credentials(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error when Jenkins credentials missing."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.side_effect = ValueError("Jenkins configuration incomplete")

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Jenkins configuration incomplete" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_jenkins_api_error(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
    ) -> None:
        """Test handling of Jenkins API errors."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client that raises exception
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.side_effect = Exception("Jenkins API error")

        # Execute & Verify - should let exception bubble up
        with pytest.raises(Exception, match="Jenkins API error"):
            execute_coordinator_test(args)

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_prints_output(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that job information is printed to stdout."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 99999
        mock_client.get_job_status.return_value = JobStatus(
            status="queued", build_number=None, duration_ms=None, url=None
        )

        # Execute
        execute_coordinator_test(args)

        # Verify output contains queue ID
        captured = capsys.readouterr()
        assert "queue: 99999" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_with_job_url(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test output when job URL immediately available."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client with immediate URL
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345
        mock_client.get_job_status.return_value = JobStatus(
            status="running",
            build_number=42,
            duration_ms=None,
            url="https://jenkins:8080/job/MCP/job/test-job/42/",
        )

        # Execute
        execute_coordinator_test(args)

        # Verify URL in output
        captured = capsys.readouterr()
        assert "https://jenkins:8080/job/MCP/job/test-job/42/" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_without_job_url(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test output when job URL not yet available."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        # Mock Jenkins client - get_job_status fails
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345
        mock_client.get_job_status.side_effect = Exception("Not ready yet")

        # Execute
        execute_coordinator_test(args)

        # Verify fallback message in output
        captured = capsys.readouterr()
        assert "will be available once build starts" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_uses_default_test_command(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
    ) -> None:
        """Test that DEFAULT_TEST_COMMAND is used in job parameters."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="main")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP/test-job",
            "github_credentials_id": "github-pat",
        }
        mock_get_creds.return_value = ("http://jenkins:8080", "user", "token")

        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.start_job.return_value = 12345

        # Execute
        execute_coordinator_test(args)

        # Verify - check that start_job was called with comprehensive test command
        call_args = mock_client.start_job.call_args
        params = call_args[0][1]  # Second positional argument is params dict

        # Verify COMMAND parameter exists and contains comprehensive test
        assert "COMMAND" in params
        command = params["COMMAND"]

        # Verify comprehensive test script components
        assert "which mcp-coder" in command
        assert "which mcp-code-checker" in command
        assert "which mcp-server-filesystem" in command
        assert "mcp-coder verify" in command
        assert "export MCP_CODER_PROJECT_DIR" in command
        assert "uv sync --extra dev" in command
        assert "which claude" in command
        assert "claude mcp list" in command
        assert "source .venv/bin/activate" in command


class TestGetEligibleIssues:
    """Tests for get_eligible_issues function."""

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_get_eligible_issues_filters_by_bot_pickup_labels(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test filtering issues by bot_pickup labels.

        Issues should have exactly ONE bot_pickup label to be eligible.
        Issues without any bot_pickup labels or with multiple bot_pickup labels
        should be excluded.
        """
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
            # Issue with multiple bot_pickup labels - should be excluded
            IssueData(
                number=3,
                title="Issue 3",
                body="",
                state="open",
                labels=["status-02:awaiting-planning", "status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/3",
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
        from mcp_coder.cli.commands.coordinator import get_eligible_issues

        result = get_eligible_issues(mock_issue_manager)

        # Verify - only issues with exactly one bot_pickup label
        assert len(result) == 2
        assert result[0]["number"] == 4  # status-08 has highest priority
        assert result[1]["number"] == 1  # status-02 has lower priority

        # Verify IssueManager.list_issues was called with correct params
        mock_issue_manager.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )


@pytest.mark.jenkins_integration
class TestCoordinatorIntegration:
    """Integration tests for coordinator command with real Jenkins.

    These tests require:
    - Jenkins server configured
    - Jenkins credentials in config or environment
    - Test job configured in Jenkins

    Tests are skipped if Jenkins not configured.
    """

    @pytest.fixture
    def jenkins_available(self) -> bool:
        """Check if Jenkins configuration is available."""
        try:
            server_url, username, api_token = get_jenkins_credentials()
            print(f"\n[DEBUG] Jenkins credentials found:")
            print(f"  server_url: {server_url}")
            print(f"  username: {username}")
            print(f"  api_token: {'*' * len(api_token) if api_token else None}")
            return True
        except ValueError as e:
            print(f"\n[DEBUG] Jenkins credentials NOT available: {e}")
            return False

    def test_coordinator_test_end_to_end(
        self, jenkins_available: bool, tmp_path: Path
    ) -> None:
        """Test complete coordinator test flow with real Jenkins.

        This test actually triggers a Jenkins job.
        Only run if you have a test Jenkins environment.
        """
        if not jenkins_available:
            pytest.skip("Jenkins not configured")

        # Create minimal args for the test
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="main")

        # This would trigger an actual Jenkins job if Jenkins is configured
        # For safety, we skip this test by default unless Jenkins is explicitly configured
        # and the repository exists in the config
        try:
            print(f"\n[DEBUG] Loading repo config for 'mcp_coder'...")
            repo_config = load_repo_config("mcp_coder")
            print(f"[DEBUG] Repo config loaded: {repo_config}")

            # Validate repo config
            print(f"[DEBUG] Validating repo config...")
            validate_repo_config("mcp_coder", repo_config)

            # If we get here, Jenkins and repo are configured - actually trigger the job
            result = execute_coordinator_test(args)

            # Verify successful execution
            assert (
                result == 0
            ), "Job triggering should succeed when Jenkins is configured"

        except ValueError as e:
            pytest.skip(f"Configuration incomplete: {e}")

    def test_coordinator_test_with_invalid_job(self, jenkins_available: bool) -> None:
        """Test error handling with invalid job path.

        This test verifies proper error handling when attempting to
        trigger a job that doesn't exist in Jenkins.
        """
        if not jenkins_available:
            pytest.skip("Jenkins not configured")

        # Create args with a non-existent repository
        args = argparse.Namespace(
            repo_name="nonexistent_repo_12345", branch_name="main"
        )

        # This should fail with a helpful error message
        result = execute_coordinator_test(args)

        # Verify exit code indicates failure
        assert result == 1
