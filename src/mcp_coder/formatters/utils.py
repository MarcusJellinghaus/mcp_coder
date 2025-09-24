"""Shared utilities for formatter implementations."""

from pathlib import Path
from typing import List


def get_default_target_dirs(project_root: Path) -> List[str]:
    """Get default target directories for formatting.

    Args:
        project_root: Root directory of the project

    Returns:
        List of directory names to format
    """
    target_dirs = []

    # Check if "src" directory exists
    if (project_root / "src").exists():
        target_dirs.append("src")

    # Check if "tests" directory exists
    if (project_root / "tests").exists():
        target_dirs.append("tests")

    # If neither exists, default to current directory
    if not target_dirs:
        target_dirs.append(".")

    return target_dirs


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory recursively.

    Args:
        directory: Directory to search for Python files

    Returns:
        List of Python file paths
    """
    python_files = []

    if directory.is_file() and directory.suffix == ".py":
        python_files.append(directory)
    elif directory.is_dir():
        # Recursively find Python files
        for file_path in directory.rglob("*.py"):
            python_files.append(file_path)

    return python_files
