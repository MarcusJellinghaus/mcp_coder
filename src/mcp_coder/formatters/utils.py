"""Shared utilities for formatter implementations."""

import tomllib
from pathlib import Path
from typing import Any, Dict, List


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


def read_tool_config(
    project_root: Path, tool_name: str, defaults: Dict[str, Any]
) -> Dict[str, Any]:
    """Read tool configuration from pyproject.toml with defaults.

    Args:
        project_root: Root directory to search for pyproject.toml
        tool_name: Name of the tool section to read (e.g., "black", "isort")
        defaults: Default configuration values to use if not found

    Returns:
        Dictionary with tool configuration, merged with defaults
    """
    # Start with default configuration
    config = defaults.copy()

    # Try to read from pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)

            # Extract tool configuration
            tool_config = pyproject_data.get("tool", {}).get(tool_name, {})

            # Update config with values from pyproject.toml
            config.update(tool_config)

        except (tomllib.TOMLDecodeError, OSError):
            # Use defaults if file can't be read
            pass

    return config
