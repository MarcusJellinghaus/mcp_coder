"""Init command for the MCP Coder CLI."""

import argparse
import logging

from ...utils.log_utils import OUTPUT
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
        logger.error("Failed to write config to %s: %s", path, e)
        return 1

    if created:
        logger.log(OUTPUT, "Created default config at: %s", path)
        logger.log(
            OUTPUT, "Please update it with your actual credentials and settings."
        )
        logger.log(OUTPUT, "\nNext steps:")
        logger.log(OUTPUT, "  mcp-coder verify          Check your setup")
        logger.log(
            OUTPUT,
            "  mcp-coder gh-tool define-labels   Sync workflow labels to your GitHub repo",
        )
    else:
        logger.log(OUTPUT, "Config already exists: %s", path)

    return 0
