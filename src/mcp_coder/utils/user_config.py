"""User configuration utilities for MCP Coder.

This module provides functions to read user configuration from TOML files
located in user-specific configuration directories.
"""

import tomllib
from pathlib import Path
from typing import Optional

from .log_utils import log_function_call


@log_function_call
def get_config_file_path() -> Path:
    """Get the path to the user configuration file.

    Returns:
        Path object pointing to ~/.mcp_coder/config.toml
    """
    return Path.home() / ".mcp_coder" / "config.toml"


@log_function_call
def get_config_value(section: str, key: str) -> Optional[str]:
    """Read a configuration value from the user config file.

    Args:
        section: The TOML section name
        key: The configuration key within the section

    Returns:
        The configuration value as a string, or None if not found

    Note:
        Returns None gracefully for any missing file, section, or key.
        No exceptions are raised for missing resources.
    """
    config_path = get_config_file_path()

    # Return None if config file doesn't exist
    if not config_path.exists():
        return None

    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)

        # Return None if section doesn't exist
        if section not in config_data:
            return None

        section_data = config_data[section]

        # Return None if key doesn't exist in section
        if key not in section_data:
            return None

        value = section_data[key]

        # Convert to string if not already a string
        return str(value) if value is not None else None

    except (tomllib.TOMLDecodeError, OSError, IOError):
        # Return None for any file reading or parsing errors
        return None


@log_function_call
def create_default_config() -> bool:
    """Create default configuration file with template content.

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

[jenkins]
# Jenkins server configuration
# Environment variables (higher priority): JENKINS_URL, JENKINS_USER, JENKINS_TOKEN
server_url = "https://jenkins.example.com:8080"
username = "your-jenkins-username"
api_token = "your-jenkins-api-token"

# Coordinator test repositories
# Add your repositories here following this pattern

[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
test_job_path = "MCP_Coder/mcp-coder-test-job"
github_credentials_id = "github-general-pat"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
test_job_path = "MCP_Filesystem/test-job"
github_credentials_id = "github-general-pat"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# test_job_path = "Folder/job-name"
# github_credentials_id = "github-credentials-id"
"""

    # Write template to file
    config_path.write_text(template, encoding="utf-8")

    return True
