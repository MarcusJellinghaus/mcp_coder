"""CLI utility functions for shared parameter handling.

This module provides utilities that are shared across CLI commands
for parameter parsing and conversion.
"""

import logging
import os
import sys
from pathlib import Path

from ..llm.session import parse_llm_method
from ..utils.user_config import get_config_values

logger = logging.getLogger(__name__)

__all__ = [
    "_get_status_symbols",
    "parse_llm_method_from_args",
    "resolve_llm_method",
    "resolve_mcp_config_path",
    "resolve_execution_dir",
]


def _get_status_symbols() -> dict[str, str]:
    """Get platform-appropriate status symbols for terminal display.

    Returns:
        Dict with 'success', 'failure', and 'warning' status symbols
    """
    if sys.platform.startswith("win"):
        return {"success": "[OK]", "failure": "[NO]", "warning": "[!!]"}
    else:
        return {"success": "\u2713", "failure": "\u2717", "warning": "\u26a0"}


_VALID_PROVIDERS = {"claude", "langchain"}


def resolve_llm_method(llm_method: str | None) -> tuple[str, str]:
    """Resolve LLM method from CLI arg, env var, config file, or default.

    Resolution order:
        1. CLI argument
        2. Environment variable MCP_CODER_LLM_PROVIDER
        3. Config [llm] default_provider
        4. Default "claude"

    Args:
        llm_method: CLI --llm-method value, or None if not specified

    Returns:
        Tuple of (provider, source) where source describes where the value came from.
        Source is one of: "cli argument", "env MCP_CODER_LLM_PROVIDER",
        "config default_provider", "default".

    Raises:
        ValueError: If env var MCP_CODER_LLM_PROVIDER has an invalid value.
    """
    if llm_method is not None:
        return (llm_method, "cli argument")

    # Check env var
    env_value = os.environ.get("MCP_CODER_LLM_PROVIDER")
    if env_value is not None:
        if env_value not in _VALID_PROVIDERS:
            raise ValueError(
                f"Invalid MCP_CODER_LLM_PROVIDER value: {env_value!r}. "
                f"Valid values: {sorted(_VALID_PROVIDERS)}"
            )
        return (env_value, "env MCP_CODER_LLM_PROVIDER")

    # Check config [llm] default_provider
    config = get_config_values([("llm", "default_provider", None)])
    provider = config[("llm", "default_provider")]
    if provider == "langchain":
        return ("langchain", "config default_provider")

    return ("claude", "default")


def parse_llm_method_from_args(llm_method: str) -> str:
    """Parse CLI llm_method into provider name for internal APIs.

    Args:
        llm_method: CLI parameter ('claude' or 'langchain')

    Returns:
        Provider name (e.g., "claude" or "langchain")

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider = parse_llm_method_from_args("claude")
        >>> print(provider)
        claude
    """
    return parse_llm_method(llm_method)


def resolve_mcp_config_path(
    mcp_config: str | None,
    project_dir: str | None = None,
) -> str | None:
    """Resolve MCP config path to absolute path.

    When mcp_config is explicitly provided, converts to absolute path and validates.
    When mcp_config is None, auto-detects .mcp.json in project_dir (or CWD).

    Args:
        mcp_config: MCP config path (relative or absolute) or None
        project_dir: Project directory to search for .mcp.json (defaults to CWD)

    Returns:
        Absolute path as string, or None if no config found

    Raises:
        FileNotFoundError: If an explicitly provided MCP config file does not exist
    """
    if mcp_config is not None:
        # Explicit path: resolve and validate
        mcp_config_path = Path(mcp_config).resolve()
        if not mcp_config_path.exists():
            raise FileNotFoundError(
                f"MCP config file not found: {mcp_config_path}\n"
                f"  Original path: {mcp_config}\n"
                f"  Current directory: {Path.cwd()}"
            )
        logger.debug(f"Resolved MCP config path: {mcp_config} -> {mcp_config_path}")
        return str(mcp_config_path)

    # Auto-detect .mcp.json
    base = Path(project_dir) if project_dir else Path.cwd()
    candidate = base / ".mcp.json"
    if candidate.exists():
        resolved = str(candidate.resolve())
        logger.debug(f"Auto-detected MCP config: {resolved}")
        return resolved

    logger.debug(f"No .mcp.json found in {base}")
    return None


def resolve_execution_dir(execution_dir: str | None) -> Path:
    """Resolve execution directory path to absolute Path object.

    Args:
        execution_dir: Optional execution directory path
                      - None: Returns current working directory
                      - Absolute path: Validates and returns as Path
                      - Relative path: Resolves relative to CWD

    Returns:
        Path: Absolute path to execution directory

    Raises:
        ValueError: If specified directory doesn't exist

    Examples:
        >>> resolve_execution_dir(None)
        PosixPath('/current/working/dir')

        >>> resolve_execution_dir('/absolute/path')
        PosixPath('/absolute/path')

        >>> resolve_execution_dir('./relative')
        PosixPath('/current/working/dir/relative')
    """
    if execution_dir is None:
        return Path.cwd()

    path = Path(execution_dir)

    # Convert relative paths to absolute
    if not path.is_absolute():
        path = Path.cwd() / path

    # Validate that the directory exists
    if not path.exists():
        raise ValueError(
            f"Execution directory does not exist: {path}\n"
            f"  Original path: {execution_dir}\n"
            f"  Current directory: {Path.cwd()}"
        )

    logger.debug(f"Resolved execution directory: {execution_dir} -> {path}")
    return path.resolve()
