"""User configuration utilities for MCP Coder.

This module provides functions to read user configuration from TOML files
located in user-specific configuration directories.
"""

import os
import platform
import tomllib
from pathlib import Path
from typing import Any, Optional

from .log_utils import log_function_call


def _format_toml_error(file_path: Path, error: tomllib.TOMLDecodeError) -> str:
    """Format TOML parse error in Python SyntaxError style.

    Args:
        file_path: Path to the config file that failed to parse
        error: The TOMLDecodeError from tomllib

    Returns:
        Formatted error string with file path, line content, and pointer
    """
    import re

    # TOMLDecodeError has lineno/colno attributes (added in Python 3.11)
    # but type stubs may not include them
    line_num: int | None = getattr(error, "lineno", None)
    col_num: int | None = getattr(error, "colno", None)

    # If attributes aren't available, try to extract from error message
    # Error message format: "... (at line X, column Y)"
    if line_num is None:
        match = re.search(r"at line (\d+)", str(error))
        if match:
            line_num = int(match.group(1))
    if col_num is None:
        match = re.search(r"column (\d+)", str(error))
        if match:
            col_num = int(match.group(1))

    # Build the file/line header
    lines = [f'  File "{file_path}", line {line_num}']

    # Try to read the error line from the file
    try:
        file_content = file_path.read_text(encoding="utf-8")
        file_lines = file_content.splitlines()

        # Check if line number is valid (1-based)
        if line_num is not None and 1 <= line_num <= len(file_lines):
            error_line = file_lines[line_num - 1].rstrip()
            lines.append(f"    {error_line}")

            # Add pointer at column position (1-based to 0-based)
            if col_num is not None and col_num >= 1:
                pointer_pos = col_num - 1
                lines.append("    " + " " * pointer_pos + "^")
    except OSError:
        # File can't be read - skip line content
        pass

    # Add the error message
    lines.append(f"TOML parse error: {error}")

    return "\n".join(lines)


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


@log_function_call(sensitive_fields=["token", "api_token"])
def load_config() -> dict[str, Any]:
    """Load user configuration from TOML file.

    Returns:
        Configuration dictionary. Empty dict if file doesn't exist.

    Raises:
        ValueError: If config file exists but has invalid TOML syntax.
                   Error message includes file path, line content, and pointer.
    """
    config_path = get_config_file_path()

    # Return empty dict if config file doesn't exist
    if not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(_format_toml_error(config_path, e)) from e
    except OSError as e:
        raise ValueError(f"Error reading config file: {config_path}\n{e}") from e


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


def _get_nested_value(
    config_data: dict[str, Any], section: str, key: str
) -> Optional[str]:
    """Get a value from nested config data using dot notation for section.

    Args:
        config_data: The loaded config dictionary
        section: Section name with dot notation for nesting (e.g., 'coordinator.repos.mcp_coder')
        key: The key within the section

    Returns:
        The value as string, or None if not found
    """
    # Navigate nested sections using dot notation
    section_data: Any = config_data
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


@log_function_call(sensitive_fields=["token", "api_token"])
def get_config_values(
    keys: list[tuple[str, str, str | None]],
) -> dict[tuple[str, str], str | None]:
    """Get multiple config values in one disk read.

    Retrieves configuration values from environment variables or config file,
    with environment variables taking priority. Reads the config file at most
    once, regardless of how many keys are requested.

    Args:
        keys: List of (section, key, env_var) tuples where:
            - section: The TOML section name (supports dot notation for nested
                      sections, e.g., 'coordinator.repos.mcp_coder')
            - key: The configuration key within the section
            - env_var: Optional environment variable name to check first.
                      Use None for auto-detection based on known mappings:
                      - ('github', 'token') -> GITHUB_TOKEN
                      - ('jenkins', 'server_url') -> JENKINS_URL
                      - ('jenkins', 'username') -> JENKINS_USER
                      - ('jenkins', 'api_token') -> JENKINS_TOKEN

    Returns:
        Dict mapping (section, key) tuples to their values (or None if not found).
        Access values using: result[(section, key)]

    Priority: Environment variable > Config file > None

    Raises:
        ValueError: If config file exists but has invalid TOML syntax.

    Examples:
        # Basic usage with auto-detected env vars
        config = get_config_values([
            ("github", "token", None),
            ("jenkins", "server_url", None),
        ])
        token = config[("github", "token")]

        # With explicit env var override
        config = get_config_values([
            ("custom", "setting", "MY_CUSTOM_VAR"),
        ])

        # Nested sections
        config = get_config_values([
            ("coordinator.repos.mcp_coder", "repo_url", None),
        ])
    """
    results: dict[tuple[str, str], str | None] = {}
    config_data: dict[str, Any] | None = None  # Lazy load

    for section, key, env_var in keys:
        # Check env var first
        actual_env_var = env_var or _get_standard_env_var(section, key)
        if actual_env_var:
            env_value = os.getenv(actual_env_var)
            if env_value:
                results[(section, key)] = env_value
                continue

        # Lazy load config (only if needed, only once)
        if config_data is None:
            config_data = load_config()

        # Navigate to value
        results[(section, key)] = _get_nested_value(config_data, section, key)

    return results


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
executor_job_path = "Tests/mcp-coder-coordinator-test"
github_credentials_id = "github-general-pat"
# executor_os: "windows" or "linux" (default: "linux", case-insensitive)
# Use "windows" for Windows Jenkins executors, "linux" for Linux/container executors
executor_os = "linux"

[coordinator.repos.mcp_server_filesystem]
repo_url = "https://github.com/your-org/mcp_server_filesystem.git"
executor_job_path = "Tests/mcp-filesystem-coordinator-test"
github_credentials_id = "github-general-pat"
executor_os = "linux"

# Example Windows executor configuration:
# [coordinator.repos.windows_project]
# repo_url = "https://github.com/your-org/windows-app.git"
# executor_job_path = "Windows/Executor/Test"
# github_credentials_id = "github-general-pat"
# executor_os = "windows"

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# executor_job_path = "Tests/your-repo-coordinator-test"
# github_credentials_id = "github-credentials-id"
# executor_os = "linux"
"""

    # Write template to file
    config_path.write_text(template, encoding="utf-8")

    return True
