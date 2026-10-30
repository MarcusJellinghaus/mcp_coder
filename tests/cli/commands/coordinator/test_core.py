"""Tests for coordinator core.py functions.

This module contains tests for:
- Configuration management functions (load_repo_config, validate_repo_config, get_jenkins_credentials)
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    get_jenkins_credentials,
    load_repo_config,
    validate_repo_config,
)


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
            ("coordinator.repos.mcp_coder", "update_issue_labels"): None,
            ("coordinator.repos.mcp_coder", "post_issue_comments"): None,
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
            ("coordinator.repos.nonexistent_repo", "update_issue_labels"): None,
            ("coordinator.repos.nonexistent_repo", "post_issue_comments"): None,
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
            ("coordinator.repos.test_repo", "update_issue_labels"): None,
            ("coordinator.repos.test_repo", "post_issue_comments"): None,
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
            ("coordinator.repos.test_repo", "update_issue_labels"): None,
            ("coordinator.repos.test_repo", "post_issue_comments"): None,
        }

        # Execute
        config = load_repo_config("test_repo")

        # Verify
        assert config["executor_os"] == "windows"  # Normalized to lowercase

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_includes_issue_interaction_flags(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test config includes update_issue_labels and post_issue_comments when set to True."""
        section = "coordinator.repos.test_repo"
        mock_get_config.return_value = {
            (section, "repo_url"): "https://github.com/test/repo.git",
            (section, "executor_job_path"): "Tests/test",
            (section, "github_credentials_id"): "cred-id",
            (section, "executor_os"): "linux",
            (section, "update_issue_labels"): True,
            (section, "post_issue_comments"): True,
        }

        config = load_repo_config("test_repo")

        assert config["update_issue_labels"] is True
        assert config["post_issue_comments"] is True

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_defaults_flags_to_true_when_missing(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test flags default to True when not present in config."""
        section = "coordinator.repos.test_repo"
        mock_get_config.return_value = {
            (section, "repo_url"): "https://github.com/test/repo.git",
            (section, "executor_job_path"): "Tests/test",
            (section, "github_credentials_id"): "cred-id",
            (section, "executor_os"): None,
            (section, "update_issue_labels"): None,
            (section, "post_issue_comments"): None,
        }

        config = load_repo_config("test_repo")

        assert config["update_issue_labels"] is True
        assert config["post_issue_comments"] is True

    @patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
    def test_load_repo_config_respects_explicit_false(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test an explicit false in config disables the flags."""
        section = "coordinator.repos.test_repo"
        mock_get_config.return_value = {
            (section, "repo_url"): "https://github.com/test/repo.git",
            (section, "executor_job_path"): "Tests/test",
            (section, "github_credentials_id"): "cred-id",
            (section, "executor_os"): None,
            (section, "update_issue_labels"): False,
            (section, "post_issue_comments"): False,
        }

        config = load_repo_config("test_repo")

        assert config["update_issue_labels"] is False
        assert config["post_issue_comments"] is False


class TestValidateRepoConfig:
    """Tests for validate_repo_config function."""

    def test_validate_repo_config_complete(self) -> None:
        """Test validation passes for complete configuration."""
        # Setup
        config: dict[str, str | bool | int | list[str] | None] = {
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
        config: dict[str, str | bool | int | list[str] | None] = {
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
        config: dict[str, str | bool | int | list[str] | None] = {
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
        config: dict[str, str | bool | int | list[str] | None] = {
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
        config: dict[str, str | bool | int | list[str] | None] = {
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
            config: dict[str, str | bool | int | list[str] | None] = {
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
