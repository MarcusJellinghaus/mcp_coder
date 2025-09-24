"""Configuration reading for formatters with line-length conflict detection."""

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional


def read_formatter_config(config_file: str = "pyproject.toml") -> Dict[str, Any]:
    """Read formatter configuration from pyproject.toml file.

    Args:
        config_file: Path to the configuration file (default: "pyproject.toml")

    Returns:
        Dictionary containing formatter configurations
    """
    config_path = Path(config_file)

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        tool_config = data.get("tool", {})
        formatter_config = {}

        # Extract Black configuration
        if "black" in tool_config:
            formatter_config["black"] = tool_config["black"]

        # Extract isort configuration
        if "isort" in tool_config:
            formatter_config["isort"] = tool_config["isort"]

        return formatter_config

    except (tomllib.TOMLDecodeError, OSError):
        return {}


def check_line_length_conflicts(config: Dict[str, Any]) -> Optional[str]:
    """Check for line-length conflicts between black and isort configurations.

    Args:
        config: Dictionary containing formatter configurations

    Returns:
        Warning message if conflict detected, None otherwise
    """
    black_config = config.get("black", {})
    isort_config = config.get("isort", {})

    # Extract line-length settings
    black_length = black_config.get("line-length")
    isort_length = isort_config.get("line_length")

    # Check for conflict only if both are configured
    if black_length is not None and isort_length is not None:
        if black_length != isort_length:
            return (
                f"Line-length conflict detected: "
                f"black line-length={black_length}, "
                f"isort line_length={isort_length}"
            )

    return None
