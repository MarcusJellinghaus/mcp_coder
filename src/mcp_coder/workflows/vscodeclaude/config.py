"""Configuration loading for vscodeclaude feature."""

import json
import logging
import re
from importlib import resources
from pathlib import Path
from typing import Any, cast

from ...utils.github_operations import get_authenticated_username
from ...utils.github_operations.label_config import load_labels_config
from ...utils.user_config import get_config_file_path, get_config_values, load_config
from .types import (
    DEFAULT_MAX_SESSIONS,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)

logger = logging.getLogger(__name__)


def _load_labels_config() -> dict[str, Any]:
    """Load labels configuration from bundled package config.

    Returns:
        Labels config dict with workflow_labels and ignore_labels
    """
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    result: dict[str, Any] = load_labels_config(config_path)
    return result


def get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Get vscodeclaude config for a status label.

    Shared helper used by workspace.py, helpers.py, and issues.py.

    Args:
        status: Status label like "status-07:code-review"

    Returns:
        vscodeclaude config dict or None if not found
    """
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return cast(dict[str, Any], label["vscodeclaude"])
    return None


def load_vscodeclaude_config() -> VSCodeClaudeConfig:
    """Load vscodeclaude configuration from config.toml.

    Returns:
        VSCodeClaudeConfig with workspace_base and max_sessions

    Raises:
        ValueError: If workspace_base not configured or doesn't exist
    """
    # Batch fetch config values
    config = get_config_values(
        [
            ("coordinator.vscodeclaude", "workspace_base", None),
            ("coordinator.vscodeclaude", "max_sessions", None),
        ]
    )

    workspace_base = config[("coordinator.vscodeclaude", "workspace_base")]
    max_sessions_str = config[("coordinator.vscodeclaude", "max_sessions")]

    # Validate workspace_base is configured
    if not workspace_base:
        config_path = get_config_file_path()
        raise ValueError(
            f"workspace_base not configured in [coordinator.vscodeclaude] section. "
            f"Config file: {config_path}"
        )

    # Validate workspace_base path exists
    workspace_path = Path(workspace_base)
    if not workspace_path.exists():
        raise ValueError(f"workspace_base path does not exist: {workspace_base}")

    # Parse max_sessions with default fallback
    max_sessions = DEFAULT_MAX_SESSIONS
    if max_sessions_str:
        try:
            max_sessions = int(max_sessions_str)
        except ValueError:
            logger.warning(
                f"Invalid max_sessions value '{max_sessions_str}', "
                f"using default {DEFAULT_MAX_SESSIONS}"
            )

    return VSCodeClaudeConfig(
        workspace_base=workspace_base,
        max_sessions=max_sessions,
    )


def load_repo_vscodeclaude_config(repo_name: str) -> RepoVSCodeClaudeConfig:
    """Load repo-specific vscodeclaude config (setup commands).

    Args:
        repo_name: Repository name from config (e.g., "mcp_coder")

    Returns:
        RepoVSCodeClaudeConfig with optional setup_commands_windows/linux
    """
    section = f"coordinator.repos.{repo_name}"

    # Batch fetch config values
    config = get_config_values(
        [
            (section, "setup_commands_windows", None),
            (section, "setup_commands_linux", None),
        ]
    )

    result: RepoVSCodeClaudeConfig = {}

    # Parse setup_commands_windows if present
    windows_commands = config[(section, "setup_commands_windows")]
    if windows_commands:
        # Config value might be a JSON-encoded list or comma-separated string
        try:
            parsed = json.loads(windows_commands)
            if isinstance(parsed, list):
                result["setup_commands_windows"] = parsed
        except json.JSONDecodeError:
            # Treat as single command
            result["setup_commands_windows"] = [windows_commands]

    # Parse setup_commands_linux if present
    linux_commands = config[(section, "setup_commands_linux")]
    if linux_commands:
        try:
            parsed = json.loads(linux_commands)
            if isinstance(parsed, list):
                result["setup_commands_linux"] = parsed
        except json.JSONDecodeError:
            result["setup_commands_linux"] = [linux_commands]

    return result


# Re-export for backwards compatibility
get_github_username = get_authenticated_username


def get_repo_short_name(repo_config: dict[str, str]) -> str:
    """Extract short repo name from repo_url.

    Args:
        repo_config: Repository config dict with repo_url

    Returns:
        Short repo name (e.g., "mcp-coder" from the URL)
    """
    repo_url = repo_config.get("repo_url", "")
    if "/" in repo_url:
        url_clean = repo_url.rstrip("/")
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
        return url_clean.split("/")[-1]
    return "repo"


def get_repo_full_name(repo_config: dict[str, str]) -> str:
    """Extract full repo name (owner/repo) from repo_url.

    Args:
        repo_config: Repository config dict with repo_url

    Returns:
        Full repo name (e.g., "owner/repo")

    Raises:
        ValueError: If repo URL cannot be parsed
    """
    repo_url = repo_config.get("repo_url", "")
    if "/" in repo_url:
        url_clean = repo_url.rstrip("/")
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
        parts = url_clean.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    raise ValueError(f"Cannot parse repo URL: {repo_url}")


def sanitize_folder_name(name: str) -> str:
    """Sanitize string for use in folder names.

    Args:
        name: Input string (e.g., repo name)

    Returns:
        String with only alphanumeric, dash, underscore chars
    """
    # Replace any non-alphanumeric character (except dash and underscore) with dash
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", name)
    # Collapse multiple dashes
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    # Strip leading/trailing dashes
    sanitized = sanitized.strip("-")
    return sanitized


def _get_configured_repos() -> set[str]:
    """Get set of repo full names from config.

    Reads config file and extracts repo_url values from
    [coordinator.repos.*] sections, converting them to "owner/repo" format.

    Returns:
        Set of repo full names in "owner/repo" format
    """
    config_data = load_config()
    repos_section = config_data.get("coordinator", {}).get("repos", {})

    configured_repos: set[str] = set()
    for _repo_name, repo_config in repos_section.items():
        repo_url = repo_config.get("repo_url", "")
        if repo_url:
            try:
                repo_full_name = get_repo_full_name({"repo_url": repo_url})
                configured_repos.add(repo_full_name)
            except ValueError:
                # Skip invalid repo URLs
                pass

    return configured_repos
