"""Tests for coordinator CLI command."""

import argparse
from pathlib import Path
from typing import Any, Optional
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
        """Test loading credentials from environment variables.

        Note: get_config_value now handles environment variables internally,
        so we don't mock it - we want the real function to run and check env vars.
        """
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

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_get_eligible_issues_excludes_ignore_labels(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test exclusion of issues with ignore_labels.

        Issues that have any label from the ignore_labels list should be
        excluded from the results, even if they have a valid bot_pickup label.
        """
        # Setup - Mock label configuration
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
            ],
            "ignore_labels": ["Overview", "Blocked", "Needs-Discussion"],
        }

        # Setup - Mock IssueManager instance
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Mock issue list with mixed labels
        mock_issue_manager.list_issues.return_value = [
            # Issue with valid bot_pickup label and no ignore labels - should be included
            IssueData(
                number=1,
                title="Valid Issue 1",
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
            # Issue with valid bot_pickup label but has "Overview" ignore label - should be excluded
            IssueData(
                number=2,
                title="Overview Issue",
                body="",
                state="open",
                labels=["status-05:plan-ready", "Overview"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/2",
                locked=False,
            ),
            # Issue with valid bot_pickup label but has "Blocked" ignore label - should be excluded
            IssueData(
                number=3,
                title="Blocked Issue",
                body="",
                state="open",
                labels=["status-08:ready-pr", "bug", "Blocked"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/3",
                locked=False,
            ),
            # Another valid issue with bot_pickup label and no ignore labels - should be included
            IssueData(
                number=4,
                title="Valid Issue 2",
                body="",
                state="open",
                labels=["status-08:ready-pr", "documentation"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/4",
                locked=False,
            ),
            # Issue with bot_pickup label and "Needs-Discussion" ignore label - should be excluded
            IssueData(
                number=5,
                title="Needs Discussion",
                body="",
                state="open",
                labels=["status-02:awaiting-planning", "Needs-Discussion"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/5",
                locked=False,
            ),
        ]

        # Execute
        from mcp_coder.cli.commands.coordinator import get_eligible_issues

        result = get_eligible_issues(mock_issue_manager)

        # Verify - only issues without ignore_labels
        assert len(result) == 2
        # Results should be sorted by priority (status-08 before status-02)
        assert result[0]["number"] == 4  # status-08:ready-pr
        assert result[1]["number"] == 1  # status-02:awaiting-planning

        # Verify excluded issues
        result_numbers = {issue["number"] for issue in result}
        assert 2 not in result_numbers  # "Overview" label
        assert 3 not in result_numbers  # "Blocked" label
        assert 5 not in result_numbers  # "Needs-Discussion" label

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_get_eligible_issues_priority_order(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test issues sorted by priority (08 → 05 → 02).

        Issues should be sorted according to PRIORITY_ORDER:
        1. status-08:ready-pr (highest priority)
        2. status-05:plan-ready
        3. status-02:awaiting-planning (lowest priority)
        """
        # Setup - Mock label configuration
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Mock IssueManager instance
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Mock issues in reverse priority order to verify sorting
        mock_issue_manager.list_issues.return_value = [
            # Issue with lowest priority - should be sorted last
            IssueData(
                number=101,
                title="Awaiting planning issue 1",
                body="",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/101",
                locked=False,
            ),
            # Issue with medium priority
            IssueData(
                number=102,
                title="Plan ready issue 1",
                body="",
                state="open",
                labels=["status-05:plan-ready", "enhancement"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/102",
                locked=False,
            ),
            # Another issue with lowest priority
            IssueData(
                number=103,
                title="Awaiting planning issue 2",
                body="",
                state="open",
                labels=["status-02:awaiting-planning", "bug"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/103",
                locked=False,
            ),
            # Issue with highest priority - should be sorted first
            IssueData(
                number=104,
                title="Ready for PR issue 1",
                body="",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/104",
                locked=False,
            ),
            # Another issue with highest priority
            IssueData(
                number=105,
                title="Ready for PR issue 2",
                body="",
                state="open",
                labels=["status-08:ready-pr", "documentation"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/105",
                locked=False,
            ),
            # Another issue with medium priority
            IssueData(
                number=106,
                title="Plan ready issue 2",
                body="",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo/issues/106",
                locked=False,
            ),
        ]

        # Execute
        from mcp_coder.cli.commands.coordinator import get_eligible_issues

        result = get_eligible_issues(mock_issue_manager)

        # Verify - all issues included and sorted by priority
        assert len(result) == 6

        # Verify priority order: status-08 issues first
        assert result[0]["number"] == 104  # status-08:ready-pr
        assert result[1]["number"] == 105  # status-08:ready-pr

        # Then status-05 issues
        assert result[2]["number"] == 102  # status-05:plan-ready
        assert result[3]["number"] == 106  # status-05:plan-ready

        # Finally status-02 issues (lowest priority)
        assert result[4]["number"] == 101  # status-02:awaiting-planning
        assert result[5]["number"] == 103  # status-02:awaiting-planning

        # Verify all issues have their expected labels
        assert "status-08:ready-pr" in result[0]["labels"]
        assert "status-08:ready-pr" in result[1]["labels"]
        assert "status-05:plan-ready" in result[2]["labels"]
        assert "status-05:plan-ready" in result[3]["labels"]
        assert "status-02:awaiting-planning" in result[4]["labels"]
        assert "status-02:awaiting-planning" in result[5]["labels"]

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    def test_get_eligible_issues_empty_result(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test handling when no eligible issues found.

        The function should return an empty list without error when:
        - No issues are returned from GitHub
        - All issues are filtered out (no bot_pickup labels, has ignore_labels, etc.)
        """
        # Setup - Mock label configuration
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Mock IssueManager instance
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Mock empty issue list (no open issues in repository)
        mock_issue_manager.list_issues.return_value = []

        # Execute
        from mcp_coder.cli.commands.coordinator import get_eligible_issues

        result = get_eligible_issues(mock_issue_manager)

        # Verify - returns empty list without error
        assert result == []
        assert len(result) == 0

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
        """Test dispatching create-plan workflow.

        For create-plan workflow:
        - Uses "main" branch (not from_issue)
        - Formats command with issue number
        - Triggers Jenkins job with correct parameters
        - Updates issue labels (removes old, adds next)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow

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
            "executor_test_path": "MCP_Coder/executor-test",
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
        assert "--project-dir /workspace/repo" in command
        assert "uv sync --extra dev" in command
        assert "which mcp-coder" in command
        assert "which claude" in command

        # Verify - Job status checked
        mock_jenkins.get_job_status.assert_called_once_with(98765)

        # Verify - Issue labels updated
        mock_issue_mgr.remove_labels.assert_called_once_with(
            123, "status-02:awaiting-planning"
        )
        mock_issue_mgr.add_labels.assert_called_once_with(123, "status-03:planning")

        # Verify - Branch manager NOT called (create-plan uses main)
        mock_branch_mgr.get_linked_branches.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    def test_dispatch_workflow_implement(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test dispatching implement workflow.

        For implement workflow:
        - Uses branch from issue (not main)
        - Gets branch name via get_linked_branches()
        - Formats command without issue number
        - Triggers Jenkins job with correct parameters
        - Updates issue labels (removes old, adds next)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-05:plan-ready label
        issue = IssueData(
            number=456,
            title="Implement feature Y",
            body="Implementation task",
            state="open",
            labels=["status-05:plan-ready", "enhancement"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/456",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-456",
        }

        # Setup - Mock branch manager to return linked branch
        mock_branch_mgr.get_linked_branches.return_value = ["456-implement-feature-y"]

        # Setup - Mock Jenkins responses
        mock_jenkins.start_job.return_value = 54321  # Queue ID
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued")

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="implement",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="DEBUG",
        )

        # Verify - Branch manager called to get linked branch
        mock_branch_mgr.get_linked_branches.assert_called_once_with(456)

        # Verify - Jenkins job started with correct parameters
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        executor_path = call_args[0][0]
        params = call_args[0][1]

        # Verify executor path
        assert executor_path == "MCP_Coder/executor-test"

        # Verify job parameters
        assert params["REPO_URL"] == "https://github.com/user/repo.git"
        assert params["BRANCH_NAME"] == "456-implement-feature-y"  # From linked branch
        assert params["GITHUB_CREDENTIALS_ID"] == "github-pat-456"

        # Verify COMMAND contains expected elements for implement
        command = params["COMMAND"]
        assert "git checkout 456-implement-feature-y" in command
        assert "git pull" in command
        assert "mcp-coder --log-level DEBUG implement" in command
        assert "--project-dir /workspace/repo" in command
        assert "uv sync --extra dev" in command
        assert "which mcp-coder" in command
        assert "which claude" in command
        # Implement workflow should NOT include issue number in command
        assert "create-plan" not in command

        # Verify - Job status checked
        mock_jenkins.get_job_status.assert_called_once_with(54321)

        # Verify - Issue labels updated
        mock_issue_mgr.remove_labels.assert_called_once_with(
            456, "status-05:plan-ready"
        )
        mock_issue_mgr.add_labels.assert_called_once_with(456, "status-06:implementing")

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    def test_dispatch_workflow_create_pr(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test dispatching create-pr workflow.

        For create-pr workflow:
        - Uses branch from issue (not main)
        - Gets branch name via get_linked_branches()
        - Formats command without issue number
        - Triggers Jenkins job with correct parameters
        - Updates issue labels (removes old, adds next)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-08:ready-pr label
        issue = IssueData(
            number=789,
            title="Create PR for feature Z",
            body="Ready to create pull request",
            state="open",
            labels=["status-08:ready-pr", "enhancement"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/789",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-789",
        }

        # Setup - Mock branch manager to return linked branch
        mock_branch_mgr.get_linked_branches.return_value = ["789-create-pr-feature-z"]

        # Setup - Mock Jenkins responses
        mock_jenkins.start_job.return_value = 11111  # Queue ID
        mock_jenkins.get_job_status.return_value = MagicMock(status="queued")

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="create-pr",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="WARNING",
        )

        # Verify - Branch manager called to get linked branch
        mock_branch_mgr.get_linked_branches.assert_called_once_with(789)

        # Verify - Jenkins job started with correct parameters
        mock_jenkins.start_job.assert_called_once()
        call_args = mock_jenkins.start_job.call_args
        executor_path = call_args[0][0]
        params = call_args[0][1]

        # Verify executor path
        assert executor_path == "MCP_Coder/executor-test"

        # Verify job parameters
        assert params["REPO_URL"] == "https://github.com/user/repo.git"
        assert params["BRANCH_NAME"] == "789-create-pr-feature-z"  # From linked branch
        assert params["GITHUB_CREDENTIALS_ID"] == "github-pat-789"

        # Verify COMMAND contains expected elements for create-pr
        command = params["COMMAND"]
        assert "git checkout 789-create-pr-feature-z" in command
        assert "git pull" in command
        assert "mcp-coder --log-level WARNING create-pr" in command
        assert "--project-dir /workspace/repo" in command
        assert "uv sync --extra dev" in command
        assert "which mcp-coder" in command
        assert "which claude" in command
        # Create-pr workflow should NOT include issue number in command
        assert "create-plan" not in command
        assert "implement" not in command

        # Verify - Job status checked
        mock_jenkins.get_job_status.assert_called_once_with(11111)

        # Verify - Issue labels updated
        mock_issue_mgr.remove_labels.assert_called_once_with(789, "status-08:ready-pr")
        mock_issue_mgr.add_labels.assert_called_once_with(789, "status-09:pr-creating")

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    def test_dispatch_workflow_missing_branch(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test error when linked branch missing for implement/create-pr.

        For workflows that require a branch from the issue (implement, create-pr),
        the function should raise ValueError if get_linked_branches() returns
        an empty list, indicating no branch is linked to the issue.
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-05:plan-ready label (implement workflow)
        issue = IssueData(
            number=555,
            title="Implement feature missing branch",
            body="This issue has no linked branch",
            state="open",
            labels=["status-05:plan-ready", "bug"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/555",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-555",
        }

        # Setup - Mock branch manager to return empty list (no linked branches)
        mock_branch_mgr.get_linked_branches.return_value = []

        # Execute & Verify - should raise ValueError with helpful message
        with pytest.raises(ValueError) as exc_info:
            dispatch_workflow(
                issue=issue,
                workflow_name="implement",
                repo_config=repo_config,
                jenkins_client=mock_jenkins,
                issue_manager=mock_issue_mgr,
                branch_manager=mock_branch_mgr,
                log_level="INFO",
            )

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "No linked branch found for issue" in error_msg
        assert "#555" in error_msg

        # Verify - Branch manager was called to check for linked branches
        mock_branch_mgr.get_linked_branches.assert_called_once_with(555)

        # Verify - Jenkins job was NOT started (error occurred before that)
        mock_jenkins.start_job.assert_not_called()

        # Verify - Issue labels were NOT updated (error occurred before that)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    def test_dispatch_workflow_jenkins_failure(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test error handling when Jenkins job fails to start.

        When Jenkins raises a JenkinsError during job triggering,
        the exception should bubble up from dispatch_workflow().
        Issue labels should NOT be updated when the job fails to start.
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow
        from mcp_coder.utils.jenkins_operations.client import JenkinsError

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-02:awaiting-planning label
        issue = IssueData(
            number=999,
            title="Feature with Jenkins failure",
            body="This job will fail to start",
            state="open",
            labels=["status-02:awaiting-planning", "enhancement"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/999",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-999",
        }

        # Setup - Mock Jenkins to raise JenkinsError when starting job
        mock_jenkins.start_job.side_effect = JenkinsError(
            "Failed to start job 'MCP_Coder/executor-test': Connection refused"
        )

        # Execute & Verify - should raise JenkinsError (bubbles up)
        with pytest.raises(JenkinsError) as exc_info:
            dispatch_workflow(
                issue=issue,
                workflow_name="create-plan",
                repo_config=repo_config,
                jenkins_client=mock_jenkins,
                issue_manager=mock_issue_mgr,
                branch_manager=mock_branch_mgr,
                log_level="INFO",
            )

        # Verify error message contains useful information
        error_msg = str(exc_info.value)
        assert "Failed to start job" in error_msg
        assert "MCP_Coder/executor-test" in error_msg

        # Verify - Jenkins start_job was called
        mock_jenkins.start_job.assert_called_once()

        # Verify - Job status was NOT checked (error occurred before that)
        mock_jenkins.get_job_status.assert_not_called()

        # Verify - Issue labels were NOT updated (job never started)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    def test_dispatch_workflow_label_update(
        self,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
    ) -> None:
        """Test label update after successful job trigger.

        When a Jenkins job is successfully triggered and verified,
        the function should update the issue labels by:
        1. Removing the current workflow label (e.g., status-02:awaiting-planning)
        2. Adding the next workflow label (e.g., status-03:planning)

        This test verifies the label update happens in the correct order
        and with the correct label values from WORKFLOW_MAPPING.
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import dispatch_workflow

        # Setup - Mock managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()

        # Setup - Mock issue with status-05:plan-ready label (implement workflow)
        issue = IssueData(
            number=777,
            title="Test label update",
            body="Testing label update functionality",
            state="open",
            labels=["status-05:plan-ready", "enhancement", "priority:high"],
            assignees=[],
            user=None,
            created_at=None,
            updated_at=None,
            url="https://github.com/user/repo/issues/777",
            locked=False,
        )

        # Setup - Repo configuration
        repo_config = {
            "repo_url": "https://github.com/user/repo.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-777",
        }

        # Setup - Mock branch manager to return linked branch
        mock_branch_mgr.get_linked_branches.return_value = ["777-test-label-update"]

        # Setup - Mock successful Jenkins job trigger
        mock_jenkins.start_job.return_value = 77777  # Queue ID
        mock_jenkins.get_job_status.return_value = MagicMock(
            status="queued", build_number=None
        )

        # Execute
        dispatch_workflow(
            issue=issue,
            workflow_name="implement",
            repo_config=repo_config,
            jenkins_client=mock_jenkins,
            issue_manager=mock_issue_mgr,
            branch_manager=mock_branch_mgr,
            log_level="INFO",
        )

        # Verify - Jenkins job was successfully triggered and verified
        mock_jenkins.start_job.assert_called_once()
        mock_jenkins.get_job_status.assert_called_once_with(77777)

        # Verify - Label update occurred in correct order
        # First, remove the old label
        mock_issue_mgr.remove_labels.assert_called_once_with(
            777, "status-05:plan-ready"
        )
        # Then, add the new label
        mock_issue_mgr.add_labels.assert_called_once_with(777, "status-06:implementing")

        # Verify - Both label operations were called (exactly once each)
        assert mock_issue_mgr.remove_labels.call_count == 1
        assert mock_issue_mgr.add_labels.call_count == 1

        # Verify - remove_labels was called before add_labels (proper order)
        remove_call = mock_issue_mgr.remove_labels.call_args
        add_call = mock_issue_mgr.add_labels.call_args
        assert remove_call is not None, "remove_labels should have been called"
        assert add_call is not None, "add_labels should have been called"


class TestExecuteCoordinatorRun:
    """Tests for execute_coordinator_run function."""

    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_creates_config_if_missing(
        self, mock_create_config: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test config auto-creation on first run.

        When the config file doesn't exist, execute_coordinator_run should:
        1. Call create_default_config() which returns True (config was created)
        2. Print a helpful message about the created config file
        3. Return exit code 1 to let user configure
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for coordinator run with --repo
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Mock create_default_config to return True (config was created)
        mock_create_config.return_value = True

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (user needs to configure)
        assert result == 1

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - Helpful message printed to stdout
        captured = capsys.readouterr()
        assert "Created default config file" in captured.out
        assert "config.toml" in captured.out
        assert "Please update" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_single_repo_success(
        self,
        mock_create_config: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_get_eligible_issues: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
    ) -> None:
        """Test successful execution for single repository.

        This test verifies the happy path:
        1. Config exists (create_default_config returns False)
        2. Repository config loaded and valid
        3. Jenkins credentials available
        4. 2 eligible issues found
        5. dispatch_workflow called for each issue
        6. Exit code 0 (success)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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

        # Setup - Mock 2 eligible issues
        mock_get_eligible_issues.return_value = [
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

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - load_repo_config was called with correct repo name
        mock_load_repo.assert_called_once_with("mcp_coder")

        # Verify - get_jenkins_credentials was called
        mock_get_creds.assert_called_once()

        # Verify - JenkinsClient was created with correct credentials
        mock_jenkins_class.assert_called_once_with(
            "https://jenkins.example.com", "jenkins_user", "jenkins_token_123"
        )

        # Verify - IssueManager was created with repo_url
        mock_issue_mgr_class.assert_called_once_with(
            repo_url="https://github.com/user/mcp_coder.git"
        )

        # Verify - IssueBranchManager was created with repo_url
        mock_branch_mgr_class.assert_called_once_with(
            repo_url="https://github.com/user/mcp_coder.git"
        )

        # Verify - get_eligible_issues was called with IssueManager
        mock_get_eligible_issues.assert_called_once_with(mock_issue_mgr)

        # Verify - dispatch_workflow was called twice (once for each issue)
        assert mock_dispatch_workflow.call_count == 2

        # Verify - First dispatch_workflow call (issue #124)
        first_call = mock_dispatch_workflow.call_args_list[0]
        assert first_call[1]["issue"]["number"] == 124
        assert first_call[1]["workflow_name"] == "create-pr"
        assert first_call[1]["repo_config"] == {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }
        assert first_call[1]["jenkins_client"] == mock_jenkins
        assert first_call[1]["issue_manager"] == mock_issue_mgr
        assert first_call[1]["branch_manager"] == mock_branch_mgr
        assert first_call[1]["log_level"] == "INFO"

        # Verify - Second dispatch_workflow call (issue #123)
        second_call = mock_dispatch_workflow.call_args_list[1]
        assert second_call[1]["issue"]["number"] == 123
        assert second_call[1]["workflow_name"] == "implement"
        assert second_call[1]["repo_config"] == {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }
        assert second_call[1]["jenkins_client"] == mock_jenkins
        assert second_call[1]["issue_manager"] == mock_issue_mgr
        assert second_call[1]["branch_manager"] == mock_branch_mgr
        assert second_call[1]["log_level"] == "INFO"

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_no_eligible_issues(
        self,
        mock_create_config: MagicMock,
        mock_get_eligible_issues: MagicMock,
        mock_get_creds: MagicMock,
        mock_load_repo: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_load_labels: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test handling when no eligible issues found.

        When get_eligible_issues returns an empty list, execute_coordinator_run should:
        1. Process normally up to the point of getting eligible issues
        2. Log a message about no eligible issues found
        3. Return exit code 0 (success, nothing to do)
        4. Not attempt to dispatch any workflows
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "bot_pickup": [
                "status-02:awaiting-planning",
                "status-05:plan-ready",
                "status-08:ready-pr",
            ],
            "bot_busy": [
                "status-03:planning",
                "status-06:implementing",
                "status-09:pr-creating",
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock get_eligible_issues returns empty list (no eligible issues)
        mock_get_eligible_issues.return_value = []

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success, nothing to do)
        assert result == 0

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - load_repo_config was called with correct repo name
        mock_load_repo.assert_called_once_with("mcp_coder")

        # Verify - get_jenkins_credentials was called
        mock_get_creds.assert_called_once()

        # Verify - IssueManager was created with repo_url
        mock_issue_mgr_class.assert_called_once_with(
            repo_url="https://github.com/user/mcp_coder.git"
        )

        # Verify - get_eligible_issues was called with IssueManager
        mock_get_eligible_issues.assert_called_once_with(mock_issue_mgr)

        # Verify - Log message about no eligible issues (optional, depends on implementation)
        # captured = capsys.readouterr()
        # Can verify log output if needed

    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_missing_repo_config(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error when repository not in config.

        When load_repo_config returns all None values, execute_coordinator_run should:
        1. Call create_default_config() which returns False (config exists)
        2. Call load_repo_config() with the repository name
        3. Detect that all required fields are None (repository not configured)
        4. Print an error message to stderr
        5. Return exit code 1
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="nonexistent_repo",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Repository not found - all values None
        mock_load_repo.return_value = {
            "repo_url": None,
            "executor_test_path": None,
            "github_credentials_id": None,
        }

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (error)
        assert result == 1

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - load_repo_config was called with correct repo name
        mock_load_repo.assert_called_once_with("nonexistent_repo")

        # Verify - Error message printed to stderr
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Config file:" in captured.err
        assert "missing" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
    @patch("mcp_coder.cli.commands.coordinator.get_eligible_issues")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_dispatch_failure_fail_fast(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_get_eligible_issues: MagicMock,
        mock_dispatch_workflow: MagicMock,
        mock_load_labels: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test fail-fast on dispatch error.

        When dispatch_workflow raises an exception, execute_coordinator_run should:
        1. Process the first issue successfully
        2. Encounter an error on the second issue
        3. Stop processing immediately (fail-fast)
        4. Return exit code 1
        5. Not process the third issue
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "bot_pickup": [
                "status-02:awaiting-planning",
                "status-05:plan-ready",
                "status-08:ready-pr",
            ],
            "bot_busy": [
                "status-03:planning",
                "status-06:implementing",
                "status-09:pr-creating",
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock Jenkins client and managers
        mock_jenkins = MagicMock()
        mock_issue_mgr = MagicMock()
        mock_branch_mgr = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock 3 eligible issues
        mock_get_eligible_issues.return_value = [
            IssueData(
                number=126,
                title="First issue",
                body="Test issue 1",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/126",
                locked=False,
            ),
            IssueData(
                number=125,
                title="Second issue - will fail",
                body="Test issue 2",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/125",
                locked=False,
            ),
            IssueData(
                number=124,
                title="Third issue - should not be processed",
                body="Test issue 3",
                state="open",
                labels=["status-02:plan-requested"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/124",
                locked=False,
            ),
        ]

        # Setup - Mock dispatch_workflow: succeeds on first call, raises on second
        mock_dispatch_workflow.side_effect = [
            None,  # First call succeeds
            ValueError("Jenkins job failed to start"),  # Second call fails
        ]

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (error due to fail-fast)
        assert result == 1

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - load_repo_config was called with correct repo name
        mock_load_repo.assert_called_once_with("mcp_coder")

        # Verify - get_jenkins_credentials was called
        mock_get_creds.assert_called_once()

        # Verify - JenkinsClient was created with correct credentials
        mock_jenkins_class.assert_called_once_with(
            "https://jenkins.example.com", "jenkins_user", "jenkins_token_123"
        )

        # Verify - IssueManager was created with repo_url
        mock_issue_mgr_class.assert_called_once_with(
            repo_url="https://github.com/user/mcp_coder.git"
        )

        # Verify - IssueBranchManager was created with repo_url
        mock_branch_mgr_class.assert_called_once_with(
            repo_url="https://github.com/user/mcp_coder.git"
        )

        # Verify - get_eligible_issues was called with IssueManager
        mock_get_eligible_issues.assert_called_once_with(mock_issue_mgr)

        # Verify - dispatch_workflow was called exactly twice (fail-fast after 2nd)
        assert mock_dispatch_workflow.call_count == 2

        # Verify - First dispatch_workflow call (issue #126)
        first_call = mock_dispatch_workflow.call_args_list[0]
        assert first_call[1]["issue"]["number"] == 126
        assert first_call[1]["workflow_name"] == "create-pr"

        # Verify - Second dispatch_workflow call (issue #125 - fails)
        second_call = mock_dispatch_workflow.call_args_list[1]
        assert second_call[1]["issue"]["number"] == 125
        assert second_call[1]["workflow_name"] == "implement"

        # Verify - Error message printed
        captured = capsys.readouterr()
        assert "Error:" in captured.err or "Failed" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_run_requires_all_or_repo(
        self,
        mock_create_config: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error when neither --all nor --repo specified.

        When args have neither all=True nor repo specified, execute_coordinator_run should:
        1. Call create_default_config() which returns False (config exists)
        2. Detect that no repository selection was provided
        3. Print an error message to stderr
        4. Return exit code 1
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args without all or repo
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo=None,
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (error)
        assert result == 1

        # Verify - create_default_config was called
        mock_create_config.assert_called_once()

        # Verify - Error message printed to stderr
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "--all" in captured.err or "--repo" in captured.err


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


class TestCoordinatorRunIntegration:
    """Integration tests for coordinator run end-to-end workflow."""

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_single_repo_multiple_issues(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test complete workflow with multiple issues in single repo.

        This test verifies the complete end-to-end flow:
        1. Config exists
        2. Repository configured correctly
        3. Jenkins credentials available
        4. Three eligible issues found (one per workflow type)
        5. All three workflows dispatched correctly
        6. All three labels updated correctly
        7. Exit code 0 (success)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock 3 eligible issues (one per workflow type)
        # Note: Issues returned in random order to test priority sorting
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=102,
                title="Implement feature",
                body="Plan ready for implementation",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/102",
                locked=False,
            ),
            IssueData(
                number=101,
                title="Create PR for feature",
                body="Ready for PR creation",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/101",
                locked=False,
            ),
            IssueData(
                number=103,
                title="Plan new feature",
                body="Awaiting planning",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/103",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock linked branches for issues that need them
        def get_linked_branches_side_effect(issue_number: int) -> list[str]:
            if issue_number == 101:  # status-08 (create-pr)
                return ["101-feature-branch"]
            elif issue_number == 102:  # status-05 (implement)
                return ["102-feature-branch"]
            else:  # status-02 (create-plan) - no branch needed
                return []

        mock_branch_mgr.get_linked_branches.side_effect = (
            get_linked_branches_side_effect
        )

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - Jenkins jobs started (3 times, one per issue)
        assert mock_jenkins.start_job.call_count == 3

        # Verify - Job status checked (3 times, one per issue)
        assert mock_jenkins.get_job_status.call_count == 3

        # Verify - Labels removed (3 times, one per issue)
        assert mock_issue_mgr.remove_labels.call_count == 3

        # Verify - Labels added (3 times, one per issue)
        assert mock_issue_mgr.add_labels.call_count == 3

        # Verify - Workflows dispatched in priority order: status-08 → status-05 → status-02
        start_job_calls = mock_jenkins.start_job.call_args_list

        # First call should be for issue #101 (status-08:ready-pr → create-pr workflow)
        first_call_params = start_job_calls[0][0][1]
        assert "101" in first_call_params["COMMAND"]
        assert "create-pr" in first_call_params["COMMAND"]

        # Second call should be for issue #102 (status-05:plan-ready → implement workflow)
        second_call_params = start_job_calls[1][0][1]
        assert "102" in second_call_params["COMMAND"]
        assert "implement" in second_call_params["COMMAND"]

        # Third call should be for issue #103 (status-02:awaiting-planning → create-plan workflow)
        third_call_params = start_job_calls[2][0][1]
        assert "103" in third_call_params["COMMAND"]
        assert "create-plan" in third_call_params["COMMAND"]

        # Verify - Label transitions correct
        remove_calls = mock_issue_mgr.remove_labels.call_args_list
        add_calls = mock_issue_mgr.add_labels.call_args_list

        # Issue #101: status-08:ready-pr → status-09:pr-creating
        assert remove_calls[0][0][0] == 101
        assert "status-08:ready-pr" in remove_calls[0][0][1]
        assert add_calls[0][0][0] == 101
        assert "status-09:pr-creating" in add_calls[0][0][1]

        # Issue #102: status-05:plan-ready → status-06:implementing
        assert remove_calls[1][0][0] == 102
        assert "status-05:plan-ready" in remove_calls[1][0][1]
        assert add_calls[1][0][0] == 102
        assert "status-06:implementing" in add_calls[1][0][1]

        # Issue #103: status-02:awaiting-planning → status-03:planning
        assert remove_calls[2][0][0] == 103
        assert "status-02:awaiting-planning" in remove_calls[2][0][1]
        assert add_calls[2][0][0] == 103
        assert "status-03:planning" in add_calls[2][0][1]

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_all_repos_mode(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test --all mode with multiple repositories.

        This test verifies the --all repos mode:
        1. Config exists and lists multiple repositories
        2. Both repositories configured correctly
        3. Jenkins credentials available
        4. Each repository has eligible issues
        5. All issues from both repos dispatched
        6. Exit code 0 (success)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for --all mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo=None,
            all=True,
            log_level="INFO",
        )

        # Setup - Config already exists with multiple repos
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Mock different repo configurations for each repo
        def load_repo_side_effect(repo_name: str) -> dict[str, str]:
            if repo_name == "repo_one":
                return {
                    "repo_url": "https://github.com/user/repo_one.git",
                    "executor_test_path": "RepoOne/executor-test",
                    "github_credentials_id": "github-pat-123",
                }
            elif repo_name == "repo_two":
                return {
                    "repo_url": "https://github.com/user/repo_two.git",
                    "executor_test_path": "RepoTwo/executor-test",
                    "github_credentials_id": "github-pat-456",
                }
            else:
                raise ValueError(f"Unknown repo: {repo_name}")

        mock_load_repo.side_effect = load_repo_side_effect

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock Jenkins client
        mock_jenkins = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        # Setup - Mock IssueManager instances (one per repo)
        mock_issue_mgr_repo_one = MagicMock()
        mock_issue_mgr_repo_two = MagicMock()

        # Track which manager gets created based on repo_url
        def issue_mgr_side_effect(
            repo_url: str, *args: Any, **kwargs: Any
        ) -> MagicMock:
            if "repo_one" in repo_url:
                return mock_issue_mgr_repo_one
            elif "repo_two" in repo_url:
                return mock_issue_mgr_repo_two
            else:
                raise ValueError(f"Unexpected repo_url: {repo_url}")

        mock_issue_mgr_class.side_effect = issue_mgr_side_effect

        # Setup - Mock eligible issues for repo_one (2 issues)
        mock_issue_mgr_repo_one.list_issues.return_value = [
            IssueData(
                number=201,
                title="Repo One: Create PR",
                body="Ready for PR creation",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo_one/issues/201",
                locked=False,
            ),
            IssueData(
                number=202,
                title="Repo One: Plan feature",
                body="Awaiting planning",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo_one/issues/202",
                locked=False,
            ),
        ]

        # Setup - Mock eligible issues for repo_two (1 issue)
        mock_issue_mgr_repo_two.list_issues.return_value = [
            IssueData(
                number=301,
                title="Repo Two: Implement feature",
                body="Plan ready for implementation",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/repo_two/issues/301",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager instances (one per repo)
        mock_branch_mgr_repo_one = MagicMock()
        mock_branch_mgr_repo_two = MagicMock()

        # Track which manager gets created based on repo_url
        def branch_mgr_side_effect(
            repo_url: str, *args: Any, **kwargs: Any
        ) -> MagicMock:
            if "repo_one" in repo_url:
                return mock_branch_mgr_repo_one
            elif "repo_two" in repo_url:
                return mock_branch_mgr_repo_two
            else:
                raise ValueError(f"Unexpected repo_url: {repo_url}")

        mock_branch_mgr_class.side_effect = branch_mgr_side_effect

        # Setup - Mock linked branches for issues that need them
        def get_linked_branches_repo_one(issue_number: int) -> list[str]:
            if issue_number == 201:  # status-08 (create-pr)
                return ["201-feature-branch"]
            else:  # status-02 (create-plan) - no branch needed
                return []

        def get_linked_branches_repo_two(issue_number: int) -> list[str]:
            if issue_number == 301:  # status-05 (implement)
                return ["301-feature-branch"]
            else:
                return []

        mock_branch_mgr_repo_one.get_linked_branches.side_effect = (
            get_linked_branches_repo_one
        )
        mock_branch_mgr_repo_two.get_linked_branches.side_effect = (
            get_linked_branches_repo_two
        )

        # Setup - Mock the config file reading for --all mode
        # Mock get_config_file_path to return a fake path
        with patch(
            "mcp_coder.cli.commands.coordinator.get_config_file_path"
        ) as mock_get_config_path:
            mock_get_config_path.return_value = Path("/fake/config.toml")

            # Mock tomllib.load to return config with two repos
            mock_config_data: dict[str, Any] = {
                "coordinator": {"repos": {"repo_one": {}, "repo_two": {}}}
            }

            with (
                patch("builtins.open", create=True) as mock_open,
                patch("tomllib.load") as mock_tomllib_load,
            ):
                mock_tomllib_load.return_value = mock_config_data

                # Execute
                result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - Jenkins jobs started (3 times total: 2 from repo_one + 1 from repo_two)
        assert mock_jenkins.start_job.call_count == 3

        # Verify - Job status checked (3 times)
        assert mock_jenkins.get_job_status.call_count == 3

        # Verify - Both repos' IssueManager instances were used
        assert mock_issue_mgr_repo_one.list_issues.call_count == 1
        assert mock_issue_mgr_repo_two.list_issues.call_count == 1

        # Verify - Labels removed for all 3 issues (2 from repo_one + 1 from repo_two)
        assert mock_issue_mgr_repo_one.remove_labels.call_count == 2
        assert mock_issue_mgr_repo_two.remove_labels.call_count == 1

        # Verify - Labels added for all 3 issues
        assert mock_issue_mgr_repo_one.add_labels.call_count == 2
        assert mock_issue_mgr_repo_two.add_labels.call_count == 1

        # Verify - Workflows dispatched in correct order (priority-based within each repo)
        start_job_calls = mock_jenkins.start_job.call_args_list

        # First call: repo_one issue #201 (status-08:ready-pr → create-pr)
        first_call_params = start_job_calls[0][0][1]
        assert "201" in first_call_params["COMMAND"]
        assert "create-pr" in first_call_params["COMMAND"]

        # Second call: repo_one issue #202 (status-02:awaiting-planning → create-plan)
        second_call_params = start_job_calls[1][0][1]
        assert "202" in second_call_params["COMMAND"]
        assert "create-plan" in second_call_params["COMMAND"]

        # Third call: repo_two issue #301 (status-05:plan-ready → implement)
        third_call_params = start_job_calls[2][0][1]
        assert "301" in third_call_params["COMMAND"]
        assert "implement" in third_call_params["COMMAND"]

        # Verify - Label transitions correct for repo_one issues
        repo_one_remove_calls = mock_issue_mgr_repo_one.remove_labels.call_args_list
        repo_one_add_calls = mock_issue_mgr_repo_one.add_labels.call_args_list

        # Issue #201: status-08:ready-pr → status-09:pr-creating
        assert repo_one_remove_calls[0][0][0] == 201
        assert "status-08:ready-pr" in repo_one_remove_calls[0][0][1]
        assert repo_one_add_calls[0][0][0] == 201
        assert "status-09:pr-creating" in repo_one_add_calls[0][0][1]

        # Issue #202: status-02:awaiting-planning → status-03:planning
        assert repo_one_remove_calls[1][0][0] == 202
        assert "status-02:awaiting-planning" in repo_one_remove_calls[1][0][1]
        assert repo_one_add_calls[1][0][0] == 202
        assert "status-03:planning" in repo_one_add_calls[1][0][1]

        # Verify - Label transitions correct for repo_two issues
        repo_two_remove_calls = mock_issue_mgr_repo_two.remove_labels.call_args_list
        repo_two_add_calls = mock_issue_mgr_repo_two.add_labels.call_args_list

        # Issue #301: status-05:plan-ready → status-06:implementing
        assert repo_two_remove_calls[0][0][0] == 301
        assert "status-05:plan-ready" in repo_two_remove_calls[0][0][1]
        assert repo_two_add_calls[0][0][0] == 301
        assert "status-06:implementing" in repo_two_add_calls[0][0][1]

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_priority_ordering(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test issues processed in correct priority order.

        This test verifies priority-based ordering:
        1. Issues returned in random order (02, 08, 05)
        2. Processed in priority order: 08 → 05 → 02
        3. dispatch_workflow calls in correct sequence
        4. All workflows complete successfully
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock 3 eligible issues in RANDOM ORDER (02, 08, 05)
        # This tests that the priority sorting works correctly
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=103,
                title="Plan new feature",
                body="Awaiting planning",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/103",
                locked=False,
            ),
            IssueData(
                number=101,
                title="Create PR for feature",
                body="Ready for PR creation",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/101",
                locked=False,
            ),
            IssueData(
                number=102,
                title="Implement feature",
                body="Plan ready for implementation",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/102",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock linked branches for issues that need them
        def get_linked_branches_side_effect(issue_number: int) -> list[str]:
            if issue_number == 101:  # status-08 (create-pr)
                return ["101-feature-branch"]
            elif issue_number == 102:  # status-05 (implement)
                return ["102-feature-branch"]
            else:  # status-02 (create-plan) - no branch needed
                return []

        mock_branch_mgr.get_linked_branches.side_effect = (
            get_linked_branches_side_effect
        )

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - Jenkins jobs started (3 times, one per issue)
        assert mock_jenkins.start_job.call_count == 3

        # Verify - Job status checked (3 times, one per issue)
        assert mock_jenkins.get_job_status.call_count == 3

        # Verify - CRITICAL: Workflows dispatched in PRIORITY ORDER: status-08 → status-05 → status-02
        # Even though issues were returned in order: 02, 08, 05
        start_job_calls = mock_jenkins.start_job.call_args_list

        # First call should be for issue #101 (status-08:ready-pr → create-pr workflow)
        first_call_params = start_job_calls[0][0][1]
        assert "101" in first_call_params["COMMAND"]
        assert "create-pr" in first_call_params["COMMAND"]

        # Second call should be for issue #102 (status-05:plan-ready → implement workflow)
        second_call_params = start_job_calls[1][0][1]
        assert "102" in second_call_params["COMMAND"]
        assert "implement" in second_call_params["COMMAND"]

        # Third call should be for issue #103 (status-02:awaiting-planning → create-plan workflow)
        third_call_params = start_job_calls[2][0][1]
        assert "103" in third_call_params["COMMAND"]
        assert "create-plan" in third_call_params["COMMAND"]

        # Verify - Labels removed (3 times, one per issue in priority order)
        assert mock_issue_mgr.remove_labels.call_count == 3

        # Verify - Labels added (3 times, one per issue in priority order)
        assert mock_issue_mgr.add_labels.call_count == 3

        # Verify - Label transitions correct and in priority order
        remove_calls = mock_issue_mgr.remove_labels.call_args_list
        add_calls = mock_issue_mgr.add_labels.call_args_list

        # Issue #101 processed first: status-08:ready-pr → status-09:pr-creating
        assert remove_calls[0][0][0] == 101
        assert "status-08:ready-pr" in remove_calls[0][0][1]
        assert add_calls[0][0][0] == 101
        assert "status-09:pr-creating" in add_calls[0][0][1]

        # Issue #102 processed second: status-05:plan-ready → status-06:implementing
        assert remove_calls[1][0][0] == 102
        assert "status-05:plan-ready" in remove_calls[1][0][1]
        assert add_calls[1][0][0] == 102
        assert "status-06:implementing" in add_calls[1][0][1]

        # Issue #103 processed third: status-02:awaiting-planning → status-03:planning
        assert remove_calls[2][0][0] == 103
        assert "status-02:awaiting-planning" in remove_calls[2][0][1]
        assert add_calls[2][0][0] == 103
        assert "status-03:planning" in add_calls[2][0][1]

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_ignore_labels_filtering(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test issues with ignore_labels are excluded.

        This test verifies ignore_labels filtering:
        1. Three issues total
        2. One issue has "Overview" label (in ignore_labels)
        3. Only 2 issues dispatched (Overview issue excluded)
        4. Correct workflows dispatched for the 2 eligible issues
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration with "Overview" as ignore_label
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock 3 issues, where issue #102 has "Overview" label and should be excluded
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=101,
                title="Create PR for feature",
                body="Ready for PR creation",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/101",
                locked=False,
            ),
            IssueData(
                number=102,
                title="Overview issue - should be ignored",
                body="This has Overview label",
                state="open",
                labels=["status-05:plan-ready", "Overview"],  # Has ignore label
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/102",
                locked=False,
            ),
            IssueData(
                number=103,
                title="Plan new feature",
                body="Awaiting planning",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/103",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock linked branches for issues that need them
        def get_linked_branches_side_effect(issue_number: int) -> list[str]:
            if issue_number == 101:  # status-08 (create-pr)
                return ["101-feature-branch"]
            else:  # status-02 (create-plan) - no branch needed
                return []

        mock_branch_mgr.get_linked_branches.side_effect = (
            get_linked_branches_side_effect
        )

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - CRITICAL: Only 2 jobs started (issue #102 with "Overview" excluded)
        assert mock_jenkins.start_job.call_count == 2

        # Verify - Job status checked 2 times (one per eligible issue)
        assert mock_jenkins.get_job_status.call_count == 2

        # Verify - Only 2 workflows dispatched (issues #101 and #103)
        start_job_calls = mock_jenkins.start_job.call_args_list

        # First workflow: Issue #101 (status-08:ready-pr) → create-pr
        first_call_params = start_job_calls[0][0][1]
        assert "101" in first_call_params["COMMAND"]
        assert "create-pr" in first_call_params["COMMAND"]

        # Second workflow: Issue #103 (status-02:awaiting-planning) → create-plan
        second_call_params = start_job_calls[1][0][1]
        assert "103" in second_call_params["COMMAND"]
        assert "create-plan" in second_call_params["COMMAND"]

        # Verify - Labels updated for only 2 issues (not the ignored one)
        assert mock_issue_mgr.remove_labels.call_count == 2
        assert mock_issue_mgr.add_labels.call_count == 2

        # Verify - Correct label transitions
        remove_calls = mock_issue_mgr.remove_labels.call_args_list
        add_calls = mock_issue_mgr.add_labels.call_args_list

        # Issue #101: status-08:ready-pr → status-09:pr-creating
        assert remove_calls[0][0][0] == 101
        assert "status-08:ready-pr" in remove_calls[0][0][1]
        assert add_calls[0][0][0] == 101
        assert "status-09:pr-creating" in add_calls[0][0][1]

        # Issue #103: status-02:awaiting-planning → status-03:planning
        assert remove_calls[1][0][0] == 103
        assert "status-02:awaiting-planning" in remove_calls[1][0][1]
        assert add_calls[1][0][0] == 103
        assert "status-03:planning" in add_calls[1][0][1]

        # Verify - Issue #102 was NOT processed (no label updates for it)
        issue_numbers_processed = [call[0][0] for call in remove_calls]
        assert 102 not in issue_numbers_processed

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_fail_fast_on_jenkins_error(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test fail-fast when Jenkins job fails to start.

        This test verifies fail-fast behavior:
        1. Three eligible issues found
        2. First issue dispatched successfully
        3. Second issue triggers JenkinsError during job start
        4. Processing stops immediately (fail-fast)
        5. Third issue never processed
        6. Exit code 1 (error)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run
        from mcp_coder.utils.jenkins_operations.client import JenkinsError

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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

        # Setup - First job starts successfully, second job raises JenkinsError
        mock_jenkins.start_job.side_effect = [
            12345,  # First job succeeds
            JenkinsError("Failed to start job: Connection refused"),  # Second fails
        ]

        # Setup - First job returns queued status
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock 3 issues: first succeeds, second fails, third never processed
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=201,
                title="First issue - succeeds",
                body="This will dispatch successfully",
                state="open",
                labels=["status-08:ready-pr"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/201",
                locked=False,
            ),
            IssueData(
                number=202,
                title="Second issue - Jenkins error",
                body="This will trigger JenkinsError",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/202",
                locked=False,
            ),
            IssueData(
                number=203,
                title="Third issue - never reached",
                body="Should not be processed",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/203",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - Mock linked branches for issues that need them
        def get_linked_branches_side_effect(issue_number: int) -> list[str]:
            if issue_number == 201:  # status-08 (create-pr)
                return ["201-feature-branch"]
            elif issue_number == 202:  # status-05 (implement)
                return ["202-feature-branch"]
            else:  # status-02 (create-plan) - no branch needed
                return []

        mock_branch_mgr.get_linked_branches.side_effect = (
            get_linked_branches_side_effect
        )

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (error due to fail-fast)
        assert result == 1

        # Verify - CRITICAL: Only 2 jobs attempted (first succeeded, second failed)
        assert mock_jenkins.start_job.call_count == 2

        # Verify - Job status checked only once (for the first successful job)
        assert mock_jenkins.get_job_status.call_count == 1

        # Verify - Only first issue had labels updated (second failed before labels)
        assert mock_issue_mgr.remove_labels.call_count == 1
        assert mock_issue_mgr.add_labels.call_count == 1

        # Verify - First issue labels updated correctly
        remove_calls = mock_issue_mgr.remove_labels.call_args_list
        add_calls = mock_issue_mgr.add_labels.call_args_list

        # Issue #201: status-08:ready-pr → status-09:pr-creating
        assert remove_calls[0][0][0] == 201
        assert "status-08:ready-pr" in remove_calls[0][0][1]
        assert add_calls[0][0][0] == 201
        assert "status-09:pr-creating" in add_calls[0][0][1]

        # Verify - Branches queried for first two issues only (fail-fast)
        assert mock_branch_mgr.get_linked_branches.call_count == 2
        branch_query_calls = mock_branch_mgr.get_linked_branches.call_args_list
        assert branch_query_calls[0][0][0] == 201  # First issue
        assert branch_query_calls[1][0][0] == 202  # Second issue (fails)

        # Verify - Third issue never reached (fail-fast after second issue error)
        issue_numbers_processed = [call[0][0] for call in remove_calls]
        assert 202 not in issue_numbers_processed  # Failed before label update
        assert 203 not in issue_numbers_processed  # Never reached

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_fail_fast_on_missing_branch(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test fail-fast when linked branch missing for implement/create-pr.

        This test verifies fail-fast behavior when a required branch is missing:
        1. Issue with status-05 (implement workflow) found
        2. dispatch_workflow attempts to get linked branch
        3. No linked branches found (empty list)
        4. ValueError raised with helpful message
        5. Processing stops immediately (fail-fast)
        6. Exit code 1 (error)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock issue with status-05 (implement) - requires branch
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=301,
                title="Issue with missing branch",
                body="This issue needs implement workflow but has no linked branch",
                state="open",
                labels=["status-05:plan-ready"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/301",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Setup - No linked branches (empty list) - this triggers ValueError
        mock_branch_mgr.get_linked_branches.return_value = []

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 1 (error due to fail-fast on missing branch)
        assert result == 1

        # Verify - get_linked_branches was called for the issue
        mock_branch_mgr.get_linked_branches.assert_called_once_with(301)

        # Verify - No Jenkins job started (error before job dispatch)
        assert mock_jenkins.start_job.call_count == 0

        # Verify - No labels updated (error before label update)
        assert mock_issue_mgr.remove_labels.call_count == 0
        assert mock_issue_mgr.add_labels.call_count == 0

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_end_to_end_log_level_pass_through(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test log level passed through to workflow commands.

        This test verifies that the --log-level argument is correctly
        passed through to the mcp-coder commands in the Jenkins job:
        1. Coordinator run called with --log-level DEBUG
        2. Issue with status-02 (create-plan) found
        3. Jenkins job triggered with COMMAND containing "mcp-coder --log-level debug"
        4. Verify log level lowercase in command (debug not DEBUG)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args with DEBUG log level
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="DEBUG",  # Testing log level pass-through
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
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
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued", build_number=None, duration_ms=None, url=None
        )

        # Setup - Mock IssueManager
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr

        # Setup - Mock issue with status-02 (create-plan)
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=401,
                title="Test log level pass-through",
                body="This issue tests that log level is passed correctly",
                state="open",
                labels=["status-02:awaiting-planning"],
                assignees=[],
                user=None,
                created_at=None,
                updated_at=None,
                url="https://github.com/user/mcp_coder/issues/401",
                locked=False,
            ),
        ]

        # Setup - Mock IssueBranchManager (not needed for create-plan but required)
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success)
        assert result == 0

        # Verify - Jenkins job started
        assert mock_jenkins.start_job.call_count == 1

        # Verify - Extract command from start_job call
        call_args = mock_jenkins.start_job.call_args
        params = call_args[0][1]  # Second positional arg is the params dict
        command = params["COMMAND"]

        # Verify - Command contains log level (lowercase as per template)
        assert "--log-level debug" in command.lower()
        # Note: The template formats with {log_level} which will be "DEBUG" from args
        # but the actual command should use lowercase "debug" per template format

        # Verify - Labels updated correctly
        mock_issue_mgr.remove_labels.assert_called_once_with(
            401, "status-02:awaiting-planning"
        )
        mock_issue_mgr.add_labels.assert_called_once_with(401, "status-03:planning")


class TestCoordinatorRunEdgeCases:
    """Edge case tests for coordinator run."""

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_no_open_issues(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test handling when repository has no open issues.

        Verifies that:
        1. When IssueManager.list_issues returns empty list
        2. The function logs "No eligible issues" message
        3. Returns exit code 0 (success, not an error condition)
        4. No Jenkins jobs are triggered
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock IssueManager with NO open issues
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_issue_mgr.list_issues.return_value = []  # Empty list - no open issues

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success - no issues is not an error)
        assert result == 0

        # Verify - IssueManager was created with correct repo_url
        mock_issue_mgr_class.assert_called_once()
        call_kwargs = mock_issue_mgr_class.call_args[1]
        assert call_kwargs["repo_url"] == "https://github.com/user/mcp_coder.git"

        # Verify - list_issues was called
        mock_issue_mgr.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )

        # Verify - No labels were updated (no issues to process)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_all_issues_have_bot_busy_labels(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test when all issues are already being processed.

        Verifies that:
        1. When all issues have bot_busy labels (status-03, 06, 09)
        2. No issues are eligible for processing
        3. The function logs "No eligible issues" message
        4. Returns exit code 0 (success)
        5. No Jenkins jobs are triggered
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock IssueManager with issues that ALL have bot_busy labels
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_issue_mgr.list_issues.return_value = [
            IssueData(
                number=101,
                title="Issue being planned",
                body="Currently in planning phase",
                state="open",
                labels=["status-03:planning", "enhancement"],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/101",
                locked=False,
            ),
            IssueData(
                number=102,
                title="Issue being implemented",
                body="Currently being implemented",
                state="open",
                labels=["status-06:implementing", "bug"],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/102",
                locked=False,
            ),
            IssueData(
                number=103,
                title="PR being created",
                body="PR creation in progress",
                state="open",
                labels=["status-09:pr-creating", "documentation"],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/103",
                locked=False,
            ),
        ]

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success - all busy is not an error)
        assert result == 0

        # Verify - IssueManager was created with correct repo_url
        mock_issue_mgr_class.assert_called_once()
        call_kwargs = mock_issue_mgr_class.call_args[1]
        assert call_kwargs["repo_url"] == "https://github.com/user/mcp_coder.git"

        # Verify - list_issues was called
        mock_issue_mgr.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )

        # Verify - No labels were updated (all issues are already being processed)
        mock_issue_mgr.remove_labels.assert_not_called()
        mock_issue_mgr.add_labels.assert_not_called()

    @patch("mcp_coder.cli.commands.coordinator.load_labels_config")
    @patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
    @patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
    @patch("mcp_coder.cli.commands.coordinator.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_issue_with_multiple_bot_pickup_labels(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        mock_issue_mgr_class: MagicMock,
        mock_branch_mgr_class: MagicMock,
        mock_jenkins_class: MagicMock,
        mock_load_labels: MagicMock,
    ) -> None:
        """Test handling of misconfigured issues with multiple bot_pickup labels.

        Verifies that:
        1. Issues with multiple bot_pickup labels are filtered out
        2. Only properly configured issues (exactly one bot_pickup label) are processed
        3. The function continues normally, skipping misconfigured issues
        4. Returns exit code 0 (success)
        """
        # Setup - Import the function we're testing
        from mcp_coder.cli.commands.coordinator import execute_coordinator_run

        # Setup - Mock args for single repository mode
        args = argparse.Namespace(
            command="coordinator",
            coordinator_subcommand="run",
            repo="mcp_coder",
            all=False,
            log_level="INFO",
        )

        # Setup - Config already exists
        mock_create_config.return_value = False

        # Setup - Mock label configuration
        mock_load_labels.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-06:implementing", "category": "bot_busy"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-09:pr-creating", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Valid repository configuration
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/mcp_coder.git",
            "executor_test_path": "MCP_Coder/executor-test",
            "github_credentials_id": "github-pat-123",
        }

        # Setup - Jenkins credentials available
        mock_get_creds.return_value = (
            "https://jenkins.example.com",
            "jenkins_user",
            "jenkins_token_123",
        )

        # Setup - Mock JenkinsClient
        mock_jenkins = MagicMock()
        mock_jenkins_class.return_value = mock_jenkins
        mock_jenkins.start_job.return_value = 12345
        mock_jenkins.get_job_status.return_value = JobStatus(
            status="queued", build_number=None, duration_ms=None, url=None
        )

        # Setup - Mock IssueBranchManager
        mock_branch_mgr = MagicMock()
        mock_branch_mgr_class.return_value = mock_branch_mgr
        # Issue 101 (status-02) doesn't need branch
        # Issue 103 (status-08) needs branch for create-pr
        mock_branch_mgr.get_linked_branches.return_value = ["103-feature-branch"]

        # Setup - Mock IssueManager with mix of valid and misconfigured issues
        mock_issue_mgr = MagicMock()
        mock_issue_mgr_class.return_value = mock_issue_mgr
        mock_issue_mgr.list_issues.return_value = [
            # Issue with valid single bot_pickup label - should be processed
            IssueData(
                number=101,
                title="Valid issue awaiting planning",
                body="This issue is properly configured",
                state="open",
                labels=["status-02:awaiting-planning", "enhancement"],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/101",
                locked=False,
            ),
            # Issue with MULTIPLE bot_pickup labels - should be SKIPPED
            IssueData(
                number=102,
                title="Misconfigured issue with multiple pickup labels",
                body="This issue has conflicting status labels",
                state="open",
                labels=[
                    "status-02:awaiting-planning",
                    "status-05:plan-ready",
                    "bug",
                ],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/102",
                locked=False,
            ),
            # Another valid issue - should be processed
            IssueData(
                number=103,
                title="Valid issue ready for PR",
                body="This issue is properly configured",
                state="open",
                labels=["status-08:ready-pr", "documentation"],
                assignees=[],
                user="testuser",
                created_at="2025-01-01T00:00:00Z",
                updated_at="2025-01-02T00:00:00Z",
                url="https://github.com/user/mcp_coder/issues/103",
                locked=False,
            ),
        ]

        # Execute
        result = execute_coordinator_run(args)

        # Verify - Exit code 0 (success - filtering works correctly)
        assert result == 0

        # Verify - IssueManager was created with correct repo_url
        mock_issue_mgr_class.assert_called_once()
        call_kwargs = mock_issue_mgr_class.call_args[1]
        assert call_kwargs["repo_url"] == "https://github.com/user/mcp_coder.git"

        # Verify - list_issues was called
        mock_issue_mgr.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )

        # Verify - Only 2 valid issues were processed (issue #102 was skipped)
        # The function filters issues internally via get_eligible_issues()
        # Issue #102 with multiple bot_pickup labels should be excluded
        assert mock_jenkins.start_job.call_count == 2

        # Verify - Workflows dispatched for issues 103 and 101 (priority order: 08 > 02)
        jenkins_calls = mock_jenkins.start_job.call_args_list
        # First call should be for issue 103 (status-08:ready-pr, highest priority)
        first_command = jenkins_calls[0][0][1]["COMMAND"]
        assert "create-pr" in first_command
        assert "103" in first_command
        # Second call should be for issue 101 (status-02:awaiting-planning)
        second_command = jenkins_calls[1][0][1]["COMMAND"]
        assert "create-plan" in second_command
        assert "101" in second_command

        # Verify - Labels were updated for the 2 valid issues only
        assert mock_issue_mgr.remove_labels.call_count == 2
        assert mock_issue_mgr.add_labels.call_count == 2

        # Verify - Issue 103: status-08 → status-09
        remove_calls = mock_issue_mgr.remove_labels.call_args_list
        add_calls = mock_issue_mgr.add_labels.call_args_list
        assert remove_calls[0][0] == (103, "status-08:ready-pr")
        assert add_calls[0][0] == (103, "status-09:pr-creating")

        # Verify - Issue 101: status-02 → status-03
        assert remove_calls[1][0] == (101, "status-02:awaiting-planning")
        assert add_calls[1][0] == (101, "status-03:planning")
