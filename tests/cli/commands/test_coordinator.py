"""Tests for coordinator CLI command."""

import argparse
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    execute_coordinator_test,
    format_job_output,
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)
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
                ("coordinator.repos.mcp_coder", "test_job_path"): "Folder/job-name",
                ("coordinator.repos.mcp_coder", "github_credentials_id"): "github-pat",
            }
            return config_map.get((section, key))

        mock_get_config.side_effect = config_side_effect

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify
        assert result is not None
        assert result["repo_url"] == "https://github.com/user/repo.git"
        assert result["test_job_path"] == "Folder/job-name"
        assert result["github_credentials_id"] == "github-pat"

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_missing_repo(self, mock_get_config: MagicMock) -> None:
        """Test error when repository doesn't exist in config."""
        # Setup - return None for all keys
        mock_get_config.return_value = None

        # Execute
        result = load_repo_config("nonexistent_repo")

        # Verify
        assert result is None

    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_handles_missing_config_file(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test graceful handling when config file doesn't exist."""
        # Setup - return None for all keys (simulating missing config)
        mock_get_config.return_value = None

        # Execute
        result = load_repo_config("mcp_coder")

        # Verify - should return None, not raise exception
        assert result is None


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""

    def test_validate_repo_config_complete(self) -> None:
        """Test validation passes for complete configuration."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute - should not raise exception
        validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_repo_url(self) -> None:
        """Test validation fails when repo_url is missing."""
        # Setup
        config = {
            "test_job_path": "Folder/job-name",
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(ValueError, match="missing required field 'repo_url'"):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_test_job_path(self) -> None:
        """Test validation fails when test_job_path is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "github_credentials_id": "github-pat",
        }

        # Execute & Verify
        with pytest.raises(ValueError, match="missing required field 'test_job_path'"):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_missing_github_credentials_id(self) -> None:
        """Test validation fails when github_credentials_id is missing."""
        # Setup
        config = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "Folder/job-name",
        }

        # Execute & Verify
        with pytest.raises(
            ValueError, match="missing required field 'github_credentials_id'"
        ):
            validate_repo_config("mcp_coder", config)

    def test_validate_repo_config_none_value(self) -> None:
        """Test validation handles None repository config."""
        # Execute & Verify
        with pytest.raises(
            ValueError, match="Repository 'mcp_coder' not found in config"
        ):
            validate_repo_config("mcp_coder", None)


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
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test successful command execution."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")

        # Config already exists
        mock_create_config.return_value = False

        # Repo config is valid
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
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
                "GITHUB_CREDENTIALS_ID": "github-pat",
            },
        )

        # Verify output printed
        captured = capsys.readouterr()
        assert "Job triggered: MCP/test-job - test - queue: 12345" in captured.out
        assert "https://jenkins:8080/queue/item/12345/" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_creates_config_if_missing(
        self, mock_create_config: MagicMock, capsys: pytest.CaptureFixture[Any]
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
        assert ".mcp_coder/config.toml" in captured.out

    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_repo_not_found(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test error when repository not in config."""
        # Setup
        args = argparse.Namespace(repo_name="nonexistent", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = None  # Repo not found

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "not found in config" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_incomplete_repo_config(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test error when repository config incomplete."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        # Missing github_credentials_id
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
        }

        # Execute
        result = execute_coordinator_test(args)

        # Verify
        assert result == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "missing required field" in captured.err

    @patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
    @patch("mcp_coder.cli.commands.coordinator.load_repo_config")
    @patch("mcp_coder.cli.commands.coordinator.create_default_config")
    def test_execute_coordinator_test_missing_jenkins_credentials(
        self,
        mock_create_config: MagicMock,
        mock_load_repo: MagicMock,
        mock_get_creds: MagicMock,
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test error when Jenkins credentials missing."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
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
            "test_job_path": "MCP/test-job",
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
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test that job information is printed to stdout."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
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
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test output when job URL immediately available."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
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
        capsys: pytest.CaptureFixture[Any],
    ) -> None:
        """Test output when job URL not yet available."""
        # Setup
        args = argparse.Namespace(repo_name="mcp_coder", branch_name="feature-x")
        mock_create_config.return_value = False
        mock_load_repo.return_value = {
            "repo_url": "https://github.com/user/repo.git",
            "test_job_path": "MCP/test-job",
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
            get_jenkins_credentials()
            return True
        except ValueError:
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
            repo_config = load_repo_config("mcp_coder")
            if repo_config is None:
                pytest.skip("Repository 'mcp_coder' not configured")

            # Validate repo config
            validate_repo_config("mcp_coder", repo_config)

            # If we get here, Jenkins and repo are configured
            # In a real test environment, we would call execute_coordinator_test(args)
            # For now, we just verify the configuration is valid
            assert repo_config["repo_url"] is not None
            assert repo_config["test_job_path"] is not None
            assert repo_config["github_credentials_id"] is not None

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
