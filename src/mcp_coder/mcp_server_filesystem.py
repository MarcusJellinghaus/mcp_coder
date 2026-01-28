"""Wrapper for mcp-server-filesystem file listing functionality."""

from pathlib import Path

from mcp_server_filesystem.file_tools.directory_utils import list_files as _list_files


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
    return _list_files(directory, project_dir, use_gitignore)
