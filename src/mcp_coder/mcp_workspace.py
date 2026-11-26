"""Wrapper for mcp-workspace file listing, gitignore and file access utilities.

Also re-exports the FILE ACCESS / GIT / GITHUB / GITHUB SECURITY section
formatters and checks that ``mcp-coder verify`` shares with
``mcp-workspace verify``.
"""

import logging
from pathlib import Path

from mcp_workspace.cli.verify_formatting import (
    format_file_access_section,
    format_git_section,
    format_github_section,
    format_github_security_section,
)
from mcp_workspace.file_tools import FileAccessVerification, verify_file_access
from mcp_workspace.file_tools.directory_utils import (
    FileAccess,
    get_file_access,
    is_path_gitignored,
    validate_access_rules,
)
from mcp_workspace.file_tools.directory_utils import list_files as _list_files

# Private upstream name: the only API that also returns the rejected references.
from mcp_workspace.main import _check_reference_projects

__all__ = [
    "FileAccess",
    "FileAccessVerification",
    "_check_reference_projects",
    "format_file_access_section",
    "format_git_section",
    "format_github_section",
    "format_github_security_section",
    "get_file_access",
    "is_path_gitignored",
    "list_files",
    "validate_access_rules",
    "verify_file_access",
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
