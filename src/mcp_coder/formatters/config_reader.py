"""Configuration reader for code formatters."""

import tomllib
import warnings
from pathlib import Path
from typing import Any, Dict, List

from .models import FormatterConfig


def parse_pyproject_toml(toml_path: Path) -> Dict[str, Any]:
    """Parse pyproject.toml file safely.

    Args:
        toml_path: Path to the pyproject.toml file

    Returns:
        Parsed TOML data as dictionary, empty dict if file missing or malformed
    """
    if not toml_path.exists():
        return {}

    try:
        with open(toml_path, "rb") as f:
            return tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def read_formatter_config(project_root: Path, formatter_name: str) -> FormatterConfig:
    """Read configuration for a specific formatter from pyproject.toml.

    Args:
        project_root: Root directory of the project
        formatter_name: Name of the formatter ("black" or "isort")

    Returns:
        FormatterConfig with parsed settings and target directories
    """
    toml_path = project_root / "pyproject.toml"
    toml_data = parse_pyproject_toml(toml_path)

    # Extract tool-specific configuration
    tool_config = toml_data.get("tool", {}).get(formatter_name, {})

    # Determine target directories
    target_dirs = _get_target_directories(project_root, tool_config)

    return FormatterConfig(
        tool_name=formatter_name,
        settings=tool_config,
        target_directories=target_dirs,
        project_root=project_root,
    )


def get_black_config(project_root: Path) -> FormatterConfig:
    """Get Black-specific configuration with defaults.

    Args:
        project_root: Root directory of the project

    Returns:
        FormatterConfig with Black settings merged with defaults
    """
    config = read_formatter_config(project_root, "black")

    # Apply Black defaults
    defaults = {"line-length": 88, "target-version": ["py311"]}

    # Merge defaults with existing settings (existing settings take precedence)
    merged_settings = {**defaults, **config.settings}

    # Check for line-length conflicts
    _check_line_length_conflicts(project_root, merged_settings.get("line-length"))

    return FormatterConfig(
        tool_name="black",
        settings=merged_settings,
        target_directories=config.target_directories,
        project_root=project_root,
    )


def get_isort_config(project_root: Path) -> FormatterConfig:
    """Get isort-specific configuration with defaults.

    Args:
        project_root: Root directory of the project

    Returns:
        FormatterConfig with isort settings merged with defaults
    """
    config = read_formatter_config(project_root, "isort")

    # Apply isort defaults
    defaults = {"profile": "black", "line_length": 88, "float_to_top": True}

    # Merge defaults with existing settings (existing settings take precedence)
    merged_settings = {**defaults, **config.settings}

    # Check for line-length conflicts
    _check_line_length_conflicts(project_root, merged_settings.get("line_length"))

    return FormatterConfig(
        tool_name="isort",
        settings=merged_settings,
        target_directories=config.target_directories,
        project_root=project_root,
    )


def _get_target_directories(
    project_root: Path, tool_config: Dict[str, Any]
) -> List[Path]:
    """Get target directories for formatting.

    Args:
        project_root: Root directory of the project
        tool_config: Tool-specific configuration

    Returns:
        List of existing target directories
    """
    # Check if custom target directories are specified
    if "target_directories" in tool_config:
        custom_dirs = tool_config["target_directories"]
        return [
            project_root / dir_name
            for dir_name in custom_dirs
            if (project_root / dir_name).exists()
        ]

    # Use default directories if they exist
    default_dirs = ["src", "tests"]
    return [
        project_root / dir_name
        for dir_name in default_dirs
        if (project_root / dir_name).exists()
    ]


def _check_line_length_conflicts(project_root: Path, current_line_length: Any) -> None:
    """Check for line-length conflicts between Black and isort.

    Args:
        project_root: Root directory of the project
        current_line_length: Current tool's line length setting
    """
    if current_line_length is None:
        return

    toml_path = project_root / "pyproject.toml"
    toml_data = parse_pyproject_toml(toml_path)

    tool_section = toml_data.get("tool", {})
    black_length = tool_section.get("black", {}).get("line-length")
    isort_length = tool_section.get("isort", {}).get("line_length")

    # Only warn if both values are present and different
    if (
        black_length is not None
        and isort_length is not None
        and black_length != isort_length
    ):
        warnings.warn(
            f"Line-length conflict detected: Black uses {black_length}, "
            f"isort uses {isort_length}. Consider aligning these values "
            f"for consistent formatting.",
            UserWarning,
            stacklevel=3,
        )
