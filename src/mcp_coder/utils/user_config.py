"""User configuration utilities for MCP Coder.

This module reads user-level configuration from config.toml files located
in user-specific configuration directories (e.g. ~/.mcp_coder/config.toml).

    config.toml  — user config (API tokens, Jenkins, coordinator settings)
    pyproject.toml — project config (formatter settings, GitHub deps)

For project-level configuration from pyproject.toml, see pyproject_config.py.
"""

import logging
import os
import platform
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .log_utils import log_function_call


@dataclass(frozen=True, slots=True)
class FieldDef:
    """Schema definition for a single config field."""

    field_type: type  # str, bool, int, list
    required: bool = False
    env_var: str | None = None


_CONFIG_SCHEMA: dict[str, dict[str, FieldDef]] = {
    "github": {
        "token": FieldDef(str, required=True, env_var="GITHUB_TOKEN"),
        "test_repo_url": FieldDef(str, env_var="GITHUB_TEST_REPO_URL"),
    },
    "jenkins": {
        "server_url": FieldDef(str, required=True, env_var="JENKINS_URL"),
        "username": FieldDef(str, required=True, env_var="JENKINS_USER"),
        "api_token": FieldDef(str, required=True, env_var="JENKINS_TOKEN"),
        "test_job": FieldDef(str),
        "test_job_coordination": FieldDef(str),
    },
    "mcp": {
        "default_config_path": FieldDef(str, env_var="MCP_CODER_MCP_CONFIG"),
    },
    "llm": {
        "default_provider": FieldDef(str),
    },
    "llm.langchain": {
        "backend": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_BACKEND"),
        "model": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_MODEL"),
        "api_key": FieldDef(str),
        "endpoint": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_ENDPOINT"),
        "api_version": FieldDef(str, env_var="MCP_CODER_LLM_LANGCHAIN_API_VERSION"),
    },
    "coordinator": {
        "cache_refresh_minutes": FieldDef(int),
    },
    "coordinator.repos.*": {
        "repo_url": FieldDef(str, required=True),
        "executor_job_path": FieldDef(str, required=True),
        "github_credentials_id": FieldDef(str, required=True),
        "executor_os": FieldDef(str),
        "update_issue_labels": FieldDef(bool),
        "post_issue_comments": FieldDef(bool),
        "setup_commands_windows": FieldDef(list),
        "setup_commands_linux": FieldDef(list),
    },
    "vscodeclaude": {
        "workspace_base": FieldDef(str, required=True),
        "max_sessions": FieldDef(int),
    },
    "mlflow": {
        "enabled": FieldDef(bool),
        "tracking_uri": FieldDef(str, env_var="MLFLOW_TRACKING_URI"),
        "experiment_name": FieldDef(str, env_var="MLFLOW_EXPERIMENT_NAME"),
        "artifact_location": FieldDef(str, env_var="MLFLOW_DEFAULT_ARTIFACT_ROOT"),
    },
}


def _get_field_def(section: str, key: str) -> FieldDef | None:
    """Look up field definition from schema, supporting wildcard sections."""
    if section in _CONFIG_SCHEMA and key in _CONFIG_SCHEMA[section]:
        return _CONFIG_SCHEMA[section][key]
    if section.startswith("coordinator.repos.") and section.count(".") == 2:
        wildcard = _CONFIG_SCHEMA.get("coordinator.repos.*", {})
        return wildcard.get(key)
    return None


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
    error_str = str(error)
    lines.append(f"TOML parse error: {error_str}")

    # Add hint for common Windows path backslash issues
    if "Invalid" in error_str and ("hex" in error_str or "escape" in error_str):
        lines.append("")
        lines.append("Hint: Backslashes in paths need escaping in TOML.")
        lines.append('  Use forward slashes: "C:/Users/..."')
        lines.append("  Or single quotes:    'C:\\Users\\...'")

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
        ("mcp", "default_config_path"): "MCP_CODER_MCP_CONFIG",
    }

    return mappings.get((section, key))


def _get_nested_value(
    config_data: dict[str, Any], section: str, key: str
) -> str | bool | int | list[Any] | None:
    """Get a value from nested config data using dot notation for section.

    Args:
        config_data: The loaded config dictionary
        section: Section name with dot notation for nesting (e.g., 'coordinator.repos.mcp_coder')
        key: The key within the section

    Returns:
        The native TOML value, or None if not found
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

    value: str | bool | int | list[Any] | None = section_data[key]
    return value


def get_config_values(
    keys: list[tuple[str, str, str | None]],
) -> dict[tuple[str, str], str | bool | int | list[Any] | None]:
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
        ValueError: If config file exists but has invalid TOML syntax,
                   or if a config value has the wrong type per the schema.

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
    results: dict[tuple[str, str], str | bool | int | list[Any] | None] = {}
    config_data: dict[str, Any] | None = None  # Lazy load

    for section, key, env_var in keys:
        # Check env var first (schema lookup replaces _get_standard_env_var)
        field_def = _get_field_def(section, key)
        actual_env_var = env_var or (field_def.env_var if field_def else None)
        if actual_env_var:
            env_value = os.getenv(actual_env_var)
            if env_value:
                results[(section, key)] = env_value
                continue

        # Lazy load config (only if needed, only once)
        if config_data is None:
            config_data = load_config()

        # Navigate to value
        value = _get_nested_value(config_data, section, key)

        # Schema-driven type validation
        if value is not None and field_def is not None:
            if not isinstance(value, field_def.field_type):
                raise ValueError(
                    f"Config error in [{section}] {key}: "
                    f"expected {field_def.field_type.__name__}, "
                    f"got {type(value).__name__} ('{value}'). "
                    f"Check your config.toml \u2014 use native TOML types."
                )

        results[(section, key)] = value

    return results


@log_function_call
def create_default_config() -> bool:
    r"""Create default configuration file with template content.

    Creates ~/.mcp_coder/config.toml with example configuration
    including Jenkins settings and repository examples.

    Returns:
        True if config was created, False if it already exists
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

# [llm]
# Default LLM provider: "claude" (default) or "langchain"
# default_provider = "langchain"

# [mcp]
# Default MCP config file path (relative to CWD or absolute)
# Environment variable (higher priority): MCP_CODER_MCP_CONFIG
# default_config_path = ".mcp.json"

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
update_issue_labels = true
post_issue_comments = true

[coordinator.repos.mcp_workspace]
repo_url = "https://github.com/your-org/mcp-workspace.git"
executor_job_path = "Tests/mcp-workspace-coordinator-test"
github_credentials_id = "github-general-pat"
executor_os = "linux"
update_issue_labels = true
post_issue_comments = true

# Example Windows executor configuration:
# [coordinator.repos.windows_project]
# repo_url = "https://github.com/your-org/windows-app.git"
# executor_job_path = "Windows/Executor/Test"
# github_credentials_id = "github-general-pat"
# executor_os = "windows"
# update_issue_labels = true
# post_issue_comments = true

# Add more repositories as needed:
# [coordinator.repos.your_repo_name]
# repo_url = "https://github.com/your-org/your_repo.git"
# executor_job_path = "Tests/your-repo-coordinator-test"
# github_credentials_id = "github-credentials-id"
# executor_os = "linux"

[vscodeclaude]
# VSCodeClaude session configuration
# workspace_base = "C:/path/to/vscodeclaude/workspaces"
# max_sessions = 3
"""

    # Write template to file
    config_path.write_text(template, encoding="utf-8")

    return True


# Section-to-env-var mapping for verify_config
_SECTION_ENV_VARS: dict[str, list[tuple[str, str]]] = {
    "github": [("token", "GITHUB_TOKEN")],
    "jenkins": [
        ("server_url", "JENKINS_URL"),
        ("username", "JENKINS_USER"),
        ("api_token", "JENKINS_TOKEN"),
    ],
}


def _get_source_annotation(section: str, key: str, config_data: dict[str, Any]) -> str:
    """Get source annotation for a config key (env var, config.toml, or both).

    Args:
        section: TOML section name
        key: Configuration key
        config_data: Loaded config data

    Returns:
        Source annotation string like "(env var)", "(config.toml)",
        or "(env var, also in config.toml)"
    """
    env_var_name = _get_standard_env_var(section, key)
    has_env = bool(env_var_name and os.environ.get(env_var_name))
    has_config = bool(
        config_data.get(section, {}).get(key)
        if isinstance(config_data.get(section), dict)
        else False
    )

    if has_env and has_config:
        return "(env var, also in config.toml)"
    if has_env:
        return "(env var)"
    return "(config.toml)"


def verify_config() -> dict[str, Any]:
    """Verify user config file and return structured result.

    Returns:
        Dict with:
        - "entries": list of {"label": str, "status": "ok"|"warning"|"error"|"info",
          "value": str}
        - "has_error": bool (True only for invalid TOML)
    """
    entries: list[dict[str, str]] = []
    path = get_config_file_path()

    # Step 1-2: Check if config file exists
    if not path.exists():
        entries.append(
            {"label": "Config file", "status": "warning", "value": "not found"}
        )
        entries.append({"label": "Expected path", "status": "info", "value": str(path)})
        entries.append(
            {
                "label": "Hint",
                "status": "info",
                "value": "Run 'mcp-coder init' to create a default config",
            }
        )
        config_data: dict[str, Any] = {}
    else:
        # Step 3: Try to load config
        try:
            config_data = load_config()
        except ValueError as e:
            entries.append(
                {"label": "Config file", "status": "error", "value": "invalid TOML"}
            )
            entries.append({"label": "Parse error", "status": "error", "value": str(e)})
            return {"entries": entries, "has_error": True}

        # Config file found and valid
        entries.append({"label": "Config file", "status": "ok", "value": str(path)})

    # Step 4: Check known sections
    # [llm] - show if section exists
    llm_section = config_data.get("llm")
    if isinstance(llm_section, dict) and "default_provider" in llm_section:
        provider = llm_section["default_provider"]
        entries.append(
            {
                "label": "[llm]",
                "status": "ok",
                "value": f"default_provider = {provider}",
            }
        )

    # [mcp] - always shown
    mcp_env = os.environ.get("MCP_CODER_MCP_CONFIG")
    mcp_config = (
        config_data.get("mcp", {}).get("default_config_path")
        if isinstance(config_data.get("mcp"), dict)
        else None
    )
    if mcp_env:
        source = _get_source_annotation("mcp", "default_config_path", config_data)
        entries.append(
            {
                "label": "[mcp]",
                "status": "ok",
                "value": f"default_config_path configured {source}",
            }
        )
    elif mcp_config:
        entries.append(
            {
                "label": "[mcp]",
                "status": "ok",
                "value": f"default_config_path = {mcp_config} (config.toml)",
            }
        )
    else:
        entries.append(
            {
                "label": "[mcp]",
                "status": "info",
                "value": "not configured (using auto-detect)",
            }
        )

    # [github] - check env var + config
    github_env = os.environ.get("GITHUB_TOKEN")
    github_config = (
        config_data.get("github", {}).get("token")
        if isinstance(config_data.get("github"), dict)
        else None
    )
    if github_env or github_config:
        source = _get_source_annotation("github", "token", config_data)
        entries.append(
            {
                "label": "[github]",
                "status": "ok",
                "value": f"token configured {source}",
            }
        )

    # [jenkins] - check env vars + config, use server_url as representative
    jenkins_env_any = any(
        os.environ.get(env_var) for _, env_var in _SECTION_ENV_VARS["jenkins"]
    )
    jenkins_config_any = (
        bool(config_data.get("jenkins"))
        if isinstance(config_data.get("jenkins"), dict)
        else False
    )
    if jenkins_env_any or jenkins_config_any:
        source = _get_source_annotation("jenkins", "server_url", config_data)
        entries.append(
            {
                "label": "[jenkins]",
                "status": "ok",
                "value": f"server_url configured {source}",
            }
        )

    # [coordinator] - count repos
    coordinator = config_data.get("coordinator")
    if isinstance(coordinator, dict):
        repos = coordinator.get("repos")
        if isinstance(repos, dict) and repos:
            count = len(repos)
            entries.append(
                {
                    "label": "[coordinator]",
                    "status": "ok",
                    "value": f"{count} repos configured",
                }
            )

    # [vscodeclaude] - check workspace_base
    vscodeclaude = config_data.get("vscodeclaude")
    if isinstance(vscodeclaude, dict) and vscodeclaude.get("workspace_base"):
        entries.append(
            {
                "label": "[vscodeclaude]",
                "status": "ok",
                "value": "workspace_base configured",
            }
        )

    return {"entries": entries, "has_error": False}


def find_repo_section_by_url(repo_url: str) -> str | None:
    """Scan all [coordinator.repos.*] sections for matching repo_url.

    Normalizes URLs before comparison (strips trailing .git and slash).

    Args:
        repo_url: Repository URL to match (e.g., "https://github.com/org/repo")

    Returns:
        Section name like "coordinator.repos.mcp_coder", or None if no match.
    """

    def _normalize_url(url: str) -> str:
        """Strip trailing .git and slash from URL.

        Returns:
            Normalized URL string.
        """
        if url.endswith(".git"):
            url = url[:-4]
        return url.rstrip("/")

    normalized_input = _normalize_url(repo_url)
    config = load_config()
    repos = config.get("coordinator", {}).get("repos", {})
    for repo_name, repo_data in repos.items():
        if not isinstance(repo_data, dict):
            continue
        config_url = repo_data.get("repo_url", "")
        if _normalize_url(config_url) == normalized_input:
            return f"coordinator.repos.{repo_name}"
    return None


# Module-level logger for configuration functions
logger = logging.getLogger(__name__)


def get_cache_refresh_minutes() -> int:
    """Get cache refresh threshold from config with default fallback.

    Returns:
        Cache refresh threshold in minutes (default: 1440 = 24 hours)
    """
    config = get_config_values([("coordinator", "cache_refresh_minutes", None)])
    value = config[("coordinator", "cache_refresh_minutes")]

    if value is None:
        return 1440  # Default: 24 hours

    if isinstance(value, int):
        if value <= 0:
            logger.warning(
                f"Invalid cache_refresh_minutes value '{value}' (must be positive), "
                "using default 1440"
            )
            return 1440
        return value

    # Env var case: value is str
    try:
        result = int(str(value))
        if result <= 0:
            logger.warning(
                f"Invalid cache_refresh_minutes value '{value}' (must be positive), "
                "using default 1440"
            )
            return 1440
        return result
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid cache_refresh_minutes value '{value}' (must be integer), "
            "using default 1440"
        )
        return 1440
