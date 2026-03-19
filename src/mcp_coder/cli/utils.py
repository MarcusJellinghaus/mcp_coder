"""CLI utility functions for shared parameter handling.

This module provides utilities that are shared across CLI commands
for parameter parsing and conversion.
"""

import logging
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


def resolve_llm_method(llm_method: str | None) -> str:
    """Resolve LLM method from CLI arg, config file, or default.

    Resolution order: CLI argument > config [llm] provider > "claude_code_cli".

    When config [llm] provider is "langchain", the resolved value is "langchain".
    Other config provider values are not mapped (fall through to default).

    Args:
        llm_method: CLI --llm-method value, or None if not specified

    Returns:
        Resolved llm_method string suitable for parse_llm_method()
    """
    if llm_method is not None:
        return llm_method

    # Check config [llm] provider
    config = get_config_values([("llm", "provider", None)])
    provider = config[("llm", "provider")]
    if provider == "langchain":
        return "langchain"

    return "claude_code_cli"


def parse_llm_method_from_args(llm_method: str) -> str:
    """Parse CLI llm_method into provider name for internal APIs.

    Args:
        llm_method: CLI parameter ('claude_code_cli' or 'langchain')

    Returns:
        Provider name (e.g., "claude" or "langchain")

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider = parse_llm_method_from_args("claude_code_cli")
        >>> print(provider)
        claude
    """
    return parse_llm_method(llm_method)


def resolve_mcp_config_path(mcp_config: str | None) -> str | None:
    """Resolve MCP config path to absolute path.

    Converts relative paths to absolute paths based on current working directory.
    This ensures the MCP config file can be found regardless of where subprocesses
    set their working directory.

    Args:
        mcp_config: MCP config path (relative or absolute) or None

    Returns:
        Absolute path as string, or None if input is None

    Raises:
        FileNotFoundError: If the MCP config file does not exist

    Examples:
        >>> # Relative path gets resolved
        >>> path = resolve_mcp_config_path(".mcp.json")
        >>> print(path)
        /absolute/path/to/.mcp.json

        >>> # Absolute path is validated but unchanged
        >>> path = resolve_mcp_config_path("/etc/mcp.json")
        >>> print(path)
        /etc/mcp.json

        >>> # None returns None
        >>> path = resolve_mcp_config_path(None)
        >>> print(path)
        None
    """
    if mcp_config is None:
        return None

    # Resolve to absolute path
    mcp_config_path = Path(mcp_config).resolve()

    # Validate that the file exists
    if not mcp_config_path.exists():
        raise FileNotFoundError(
            f"MCP config file not found: {mcp_config_path}\n"
            f"  Original path: {mcp_config}\n"
            f"  Current directory: {Path.cwd()}"
        )

    logger.debug(f"Resolved MCP config path: {mcp_config} -> {mcp_config_path}")
    return str(mcp_config_path)


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
