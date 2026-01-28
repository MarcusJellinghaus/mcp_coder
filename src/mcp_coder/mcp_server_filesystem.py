"""Wrapper for mcp-server-filesystem file listing functionality."""

import logging
from pathlib import Path

from mcp_server_filesystem.file_tools.directory_utils import list_files as _list_files

# Logger for the external library (verbose at INFO level)
_external_logger = logging.getLogger("mcp_server_filesystem.file_tools.directory_utils")


def list_files(
    directory: str, project_dir: Path, use_gitignore: bool = True
) -> list[str]:
    """List all files in directory with optional gitignore filtering.

    Args:
        directory: Directory to list files from
        project_dir: Project root directory
        use_gitignore: Whether to apply .gitignore filtering (default: True)

    Returns:
        List of relative file paths
    """
    # Temporarily suppress verbose logging from external library
    # See: https://github.com/MarcusJellinghaus/mcp_server_filesystem/issues/48
    original_level = _external_logger.level
    _external_logger.setLevel(logging.WARNING)
    try:
        return _list_files(directory, project_dir, use_gitignore)
    finally:
        _external_logger.setLevel(original_level)
