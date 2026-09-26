"""Install command for the MCP Coder CLI."""

import argparse
import logging

from ...install import InstallConfig, install

logger = logging.getLogger(__name__)


def execute_install(args: argparse.Namespace) -> int:
    """Install mcp-coder into a target environment.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 when the requested configuration or the
        pyproject.toml at --local-path is invalid. A failing install
        command exits the process directly.
    """
    try:
        config = InstallConfig.from_args(args)
        install(config)
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    return 0
