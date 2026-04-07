"""Configuration reading for formatters with line-length conflict detection."""

from pathlib import Path
from typing import Any, Dict

from ..utils.pyproject_config import (
    check_line_length_conflicts as check_line_length_conflicts,
)
from ..utils.pyproject_config import (
    get_formatter_config,
)


def read_formatter_config(config_file: str = "pyproject.toml") -> Dict[str, Any]:
    """Read formatter configuration from pyproject.toml file.

    Args:
        config_file: Path to the configuration file (default: "pyproject.toml")

    Returns:
        Dictionary containing formatter configurations
    """
    config_path = Path(config_file)
    return get_formatter_config(config_path.parent, filename=config_path.name)
