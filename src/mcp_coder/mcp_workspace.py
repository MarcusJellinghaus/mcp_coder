"""Wrapper for mcp-workspace file listing, gitignore and file access utilities.

``FILE_ACCESS_SUPPORTED`` tells whether the installed mcp-workspace knows the
``.mcp-file-access`` rules file (since upstream f626cf8). Without it,
``FileAccess``, ``get_file_access`` and ``validate_access_rules`` are
stand-ins that give the gitignore-only view: gitignored paths are hidden,
everything else is writable, and no rules file is ever invalid. The flag
describes the Python environment mcp-coder runs in, not the MCP server.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_workspace.file_tools.directory_utils import is_path_gitignored
from mcp_workspace.file_tools.directory_utils import list_files as _list_files

if TYPE_CHECKING:
    from mcp_workspace.file_tools.directory_utils import FileAccess as FileAccess
    from mcp_workspace.file_tools.directory_utils import (
        get_file_access as get_file_access,
    )
    from mcp_workspace.file_tools.directory_utils import (
        validate_access_rules as validate_access_rules,
    )

    FILE_ACCESS_SUPPORTED: bool
else:
    try:
        from mcp_workspace.file_tools.directory_utils import (
            FileAccess,
            get_file_access,
            validate_access_rules,
        )

        FILE_ACCESS_SUPPORTED = True
    except ImportError:  # mcp-workspace older than f626cf8
        from enum import IntEnum

        FILE_ACCESS_SUPPORTED = False

        class FileAccess(IntEnum):
            """Stand-in for mcp-workspace's ``FileAccess``."""

            HIDDEN = 0
            READ_ONLY = 1
            READ_WRITE = 2

        def get_file_access(path: str, project_dir: Path) -> FileAccess:
            """Stand-in: the gitignore default, no rules.

            Returns:
                ``HIDDEN`` for a gitignored path, else ``READ_WRITE``.
            """
            if is_path_gitignored(path, project_dir):
                return FileAccess.HIDDEN
            return FileAccess.READ_WRITE

        def validate_access_rules(project_dir: Path) -> list[str]:
            """Stand-in: no rules file can be checked.

            Returns:
                Always an empty list.
            """
            del project_dir
            return []


__all__ = [
    "FILE_ACCESS_SUPPORTED",
    "FileAccess",
    "get_file_access",
    "is_path_gitignored",
    "list_files",
    "validate_access_rules",
]

# Logger for the external library (verbose at INFO level)
_external_logger = logging.getLogger("mcp_workspace.file_tools.directory_utils")


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
    # See: https://github.com/MarcusJellinghaus/mcp-workspace/issues/48
    original_level = _external_logger.level
    _external_logger.setLevel(logging.WARNING)
    try:
        return _list_files(directory, project_dir, use_gitignore)
    finally:
        _external_logger.setLevel(original_level)
