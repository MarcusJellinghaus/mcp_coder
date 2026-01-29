"""Configuration loading for vscodeclaude feature."""

import json
import logging
import re
from pathlib import Path
from types import ModuleType

from ..user_config import get_config_file_path
from .types import (
    DEFAULT_MAX_SESSIONS,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
)

logger = logging.getLogger(__name__)


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


def load_vscodeclaude_config() -> VSCodeClaudeConfig:
    """Load vscodeclaude configuration from config.toml.

    Returns:
        VSCodeClaudeConfig with workspace_base and max_sessions

    Raises:
        ValueError: If workspace_base not configured or doesn't exist
    """
    coordinator = _get_coordinator()

    # Batch fetch config values
    config = coordinator.get_config_values(
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
    coordinator = _get_coordinator()

    section = f"coordinator.repos.{repo_name}"

    # Batch fetch config values
    config = coordinator.get_config_values(
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


def get_github_username() -> str:
    """Get authenticated GitHub username via PyGithub API.

    Returns:
        GitHub username string

    Raises:
        ValueError: If GitHub authentication fails
    """
    coordinator = _get_coordinator()

    # Get GitHub token from config
    config = coordinator.get_config_values([("github", "token", None)])
    token = config[("github", "token")]

    if not token:
        raise ValueError(
            "GitHub token not configured. Set via GITHUB_TOKEN environment "
            "variable or config file [github] section"
        )

    try:
        from github import Github

        github_client = Github(token)
        user = github_client.get_user()
        return user.login
    except Exception as e:
        raise ValueError(f"Failed to authenticate with GitHub: {e}") from e


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
