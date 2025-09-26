"""Personal configuration utilities for MCP Coder.

This module provides functions to read personal configuration from TOML files
located in platform-specific user configuration directories.
"""

import platform
import tomllib
from pathlib import Path
from typing import Optional

from .log_utils import log_function_call


@log_function_call
def get_config_file_path() -> Path:
    """Get the path to the personal configuration file.

    Returns platform-specific path:
    - Windows: %USERPROFILE%\\.mcp_coder\\config.toml
    - macOS/Linux: ~/.mcp_coder/config.toml

    Returns:
        Path object pointing to the configuration file location
    """
    system = platform.system()

    if system == "Windows":
        base_path = Path.home()
    else:
        # Unix-like systems (Linux, macOS, etc.)
        base_path = Path.home()

    return base_path / ".mcp_coder" / "config.toml"


@log_function_call
def get_config_value(section: str, key: str) -> Optional[str]:
    """Read a configuration value from the personal config file.

    Args:
        section: The TOML section name
        key: The configuration key within the section

    Returns:
        The configuration value as a string, or None if not found

    Note:
        Returns None gracefully for any missing file, section, or key.
        No exceptions are raised for missing resources.
    """
    config_path = get_config_file_path()

    # Return None if config file doesn't exist
    if not config_path.exists():
        return None

    try:
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)

        # Return None if section doesn't exist
        if section not in config_data:
            return None

        section_data = config_data[section]

        # Return None if key doesn't exist in section
        if key not in section_data:
            return None

        value = section_data[key]

        # Convert to string if not already a string
        return str(value) if value is not None else None

    except (tomllib.TOMLDecodeError, OSError, IOError):
        # Return None for any file reading or parsing errors
        return None
