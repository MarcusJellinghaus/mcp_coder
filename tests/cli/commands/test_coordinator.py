"""Tests for coordinator CLI command."""

import pytest
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from mcp_coder.cli.commands.coordinator import (
    load_repo_config,
    validate_repo_config,
    get_jenkins_credentials,
    format_job_output,
)


class TestLoadRepoConfig:
    """Tests for load_repo_config function."""
    
    @patch("mcp_coder.cli.commands.coordinator.get_config_value")
    def test_load_repo_config_success(self, mock_get_config: MagicMock) -> None:
        """Test successful loading of repository configuration."""
        # Setup
        def config_side_effect(section: str, key: str) -> str | None:
            config_map = {
                ("coordinator.repos.mcp_coder", "repo_url"): "https://github.com/user/repo.git",
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
    def test_load_repo_config_handles_missing_config_file(self, mock_get_config: MagicMock) -> None:
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
        with pytest.raises(ValueError, match="missing required field 'github_credentials_id'"):
            validate_repo_config("mcp_coder", config)
    
    def test_validate_repo_config_none_value(self) -> None:
        """Test validation handles None repository config."""
        # Execute & Verify
        with pytest.raises(ValueError, match="Repository 'mcp_coder' not found in config"):
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
        with pytest.raises(ValueError, match="Jenkins configuration incomplete.*server_url"):
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
        with pytest.raises(ValueError, match="Jenkins configuration incomplete.*username"):
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
        with pytest.raises(ValueError, match="Jenkins configuration incomplete.*api_token"):
            get_jenkins_credentials()


class TestFormatJobOutput:
    """Tests for format_job_output function."""
    
    def test_format_job_output_with_url(self) -> None:
        """Test formatting output when job URL is available."""
        # Execute
        result = format_job_output(
            "MCP_Coder/test-job",
            12345,
            "https://jenkins.example.com/job/MCP_Coder/job/test-job/42/"
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
