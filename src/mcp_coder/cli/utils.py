"""CLI utility functions for shared parameter handling.

This module provides utilities that are shared across CLI commands
for parameter parsing and conversion.
"""

import logging
from pathlib import Path

from ..llm.session import parse_llm_method

logger = logging.getLogger(__name__)

__all__ = [
    "parse_llm_method_from_args",
    "resolve_mcp_config_path",
    "resolve_execution_dir",
]


def parse_llm_method_from_args(llm_method: str) -> tuple[str, str]:
    """Parse CLI llm_method into provider, method for internal APIs.

    Args:
        llm_method: CLI parameter ('claude_code_cli' or 'claude_code_api')

    Returns:
        Tuple of (provider, method) for internal API usage

    Raises:
        ValueError: If llm_method is not supported

    Example:
        >>> provider, method = parse_llm_method_from_args("claude_code_api")
        >>> print(provider, method)
        claude api
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
