"""Init command for the MCP Coder CLI."""

import argparse
import logging

from ...utils.user_config import create_default_config, get_config_file_path

logger = logging.getLogger(__name__)


def execute_init(_args: argparse.Namespace) -> int:
    """Execute init command to create default configuration file.

    Args:
        _args: Parsed command-line arguments (unused for this command).

    Returns:
        Exit code (0 for success, 1 for write failure).
    """
    logger.info("Executing init command")

    path = get_config_file_path()
    try:
        created = create_default_config()
    except OSError as e:
        print(f"Error: Failed to write config to {path}: {e}")
        return 1

    if created:
        print(f"Created default config at: {path}")
        print("Please update it with your actual credentials and settings.")
        print("\nNext steps:")
        print("  mcp-coder verify          Check your setup")
        print(
            "  mcp-coder gh-tool define-labels   Sync workflow labels to your GitHub repo"
        )
    else:
        print(f"Config already exists: {path}")

    return 0
