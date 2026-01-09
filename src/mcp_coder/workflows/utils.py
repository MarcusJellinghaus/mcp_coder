"""Utility functions for workflows.

This module contains shared utility functions used across different workflow modules.
"""

import logging
from pathlib import Path
from typing import Optional

# Setup logger
logger = logging.getLogger(__name__)


def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert project directory argument to absolute Path, with validation.

    Args:
        project_dir_arg: Optional project directory path string, uses current directory if None

    Returns:
        Path: Validated absolute path to project directory

    Raises:
        ValueError: If path is invalid, doesn't exist, not a directory, not accessible, or not a git repo
    """
    # Use current directory if no argument provided
    if project_dir_arg is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_dir_arg)

    # Resolve to absolute path
    try:
        project_path = project_path.resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid project directory path: {e}") from e

    # Validate directory exists
    if not project_path.exists():
        raise ValueError(f"Project directory does not exist: {project_path}")

    # Validate it's a directory
    if not project_path.is_dir():
        raise ValueError(f"Project path is not a directory: {project_path}")

    # Validate directory is accessible
    try:
        # Test read access by listing directory
        list(project_path.iterdir())
    except PermissionError as e:
        raise ValueError(f"No read access to project directory: {project_path}") from e

    # Validate directory contains .git subdirectory
    git_dir = project_path / ".git"
    if not git_dir.exists():
        raise ValueError(f"Project directory is not a git repository: {project_path}")

    return project_path
