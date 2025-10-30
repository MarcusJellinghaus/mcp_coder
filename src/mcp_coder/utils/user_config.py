"""User configuration utilities for MCP Coder.

This module provides functions to read user configuration from TOML files
located in user-specific configuration directories.
"""

import os
import platform
import tomllib
from pathlib import Path
from typing import Optional

from .log_utils import log_function_call


@log_function_call
def get_config_file_path() -> Path:
    r"""Get the path to the user configuration file.

    Returns:
        Path object pointing to platform-specific config location:
        - Windows: %USERPROFILE%\.mcp_coder\config.toml
        - Linux/macOS/Containers: ~/.config/mcp_coder/config.toml
    """
    if platform.system() == "Windows":
        return Path.home() / ".mcp_coder" / "config.toml"
    else:
        # Linux/macOS/Containers - use XDG Base Directory Specification
        return Path.home() / ".config" / "mcp_coder" / "config.toml"


@log_function_call
def get_config_value(
    section: str, key: str, env_var: Optional[str] = None
) -> Optional[str]:
    """Read a configuration value from environment or config file.

    Priority: Environment variable > Config file > None

    Args:
        section: The TOML section name (supports dot notation for nested sections,
                e.g., 'coordinator.repos.mcp_coder')
        key: The configuration key within the section
        env_var: Optional environment variable name to check first.
                If not provided, attempts to construct from section and key.
                For known mappings, uses standardized names:
                - ('github', 'token') -> GITHUB_TOKEN
                - ('jenkins', 'server_url') -> JENKINS_URL
                - ('jenkins', 'username') -> JENKINS_USER
                - ('jenkins', 'api_token') -> JENKINS_TOKEN

    Returns:
        The configuration value as a string, or None if not found

    Note:
        Returns None gracefully for any missing file, section, or key.
        No exceptions are raised for missing resources.

    Examples:
        # Top-level section with automatic env var detection
        get_config_value('jenkins', 'server_url')  # Checks JENKINS_URL first

        # Explicit environment variable name
        get_config_value('github', 'token', env_var='GITHUB_TOKEN')

        # Nested section using dot notation
        get_config_value('coordinator.repos.mcp_coder', 'repo_url')
    """
    # Step 1: Check environment variable first (highest priority)
    if env_var is None:
        # Attempt to construct standard environment variable name
        env_var = _get_standard_env_var(section, key)

    if env_var:
        env_value = os.getenv(env_var)
        if env_value:
            return env_value

    # Step 2: Fall back to config file
    config_path = get_config_file_path()

    # Return None if config file doesn't exist
    if not config_path.exists():
        return None

    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)

        # Navigate nested sections using dot notation
        section_data = config_data
        section_parts = section.split(".")

        for part in section_parts:
            if not isinstance(section_data, dict) or part not in section_data:
                return None
            section_data = section_data[part]

        # Return None if key doesn't exist in section
        if not isinstance(section_data, dict) or key not in section_data:
            return None

        value = section_data[key]

        # Convert to string if not already a string
        return str(value) if value is not None else None

    except (tomllib.TOMLDecodeError, OSError, IOError):
        # Return None for any file reading or parsing errors
        return None


def _get_standard_env_var(section: str, key: str) -> Optional[str]:
    """Get standard environment variable name for known config keys.

    Maps common config keys to their standardized environment variable names.
    This allows automatic environment variable detection for known keys.

    Args:
        section: TOML section name
        key: Configuration key

    Returns:
        Standard environment variable name, or None if no mapping exists

    Examples:
        _get_standard_env_var('github', 'token') -> 'GITHUB_TOKEN'
        _get_standard_env_var('jenkins', 'server_url') -> 'JENKINS_URL'
        _get_standard_env_var('unknown', 'key') -> None
    """
    # Known environment variable mappings
    mappings = {
        ("github", "token"): "GITHUB_TOKEN",
        ("github", "test_repo_url"): "GITHUB_TEST_REPO_URL",
        ("jenkins", "server_url"): "JENKINS_URL",
        ("jenkins", "username"): "JENKINS_USER",
        ("jenkins", "api_token"): "JENKINS_TOKEN",
    }

    return mappings.get((section, key))


@log_function_call
def create_default_config() -> bool:
    r"""Create default configuration file with template content.

    Creates ~/.mcp_coder/config.toml with example configuration
    including Jenkins settings and repository examples.

    Returns:
        True if config was created, False if it already exists

    Raises:
        OSError: If directory/file creation fails due to permissions
    """
    config_path = get_config_file_path()

    # Don't overwrite existing config
    if config_path.exists():
        return False

    # Create parent directory
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Define template content
    template = """# MCP Coder Configuration
# Update with your actual credentials and repository information

[github]
# GitHub authentication
# Environment variable (higher priority): GITHUB_TOKEN
token = "ghp_your_github_personal_access_token_here"

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"
test_job = "Tests/mcp-coder-simple-test"  # Job for integration tests
test_job_coordination = "Tests/mcp-coder-coordinator-test"  # Job for coordinator tests

# Coordinator test repositories
# Add your repositories here following this pattern

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
executor_test_path = "Tests/mcp-coder-coordinator-test"
github_credentials_id = "github-general-pat"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
executor_test_path = "Tests/mcp-filesystem-coordinator-test"
github_credentials_id = "github-general-pat"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# executor_test_path = "Tests/your-repo-coordinator-test"
# github_credentials_id = "github-credentials-id"
"""

    # Write template to file
    config_path.write_text(template, encoding="utf-8")

    return True
