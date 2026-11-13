"""Setup command for the MCP Coder CLI."""

import argparse
import logging
from pathlib import Path

from ...install.project_setup import SetupError, run_setup

logger = logging.getLogger(__name__)


def execute_setup(args: argparse.Namespace) -> int:
    """Run the project's [tool.mcp-coder.setup] steps.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success; 1 when the project directory is missing, the setup
        configuration is invalid, a step fails or setup changed files.
    """
    project_dir = Path(args.project_dir or ".").resolve()
    if not project_dir.is_dir():
        logger.error(
            "Project directory does not exist or is not a directory: %s", project_dir
        )
        return 1

    try:
        run_setup(project_dir, refresh=args.refresh, skip_overrides=args.skip_overrides)
    except (ValueError, SetupError) as exc:
        logger.error(str(exc))
        return 1

    return 0
