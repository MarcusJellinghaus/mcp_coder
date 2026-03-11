"""Verify command for the MCP Coder CLI."""

import argparse
import logging

from ...llm.providers.claude.claude_cli_verification import verify_claude
from ..utils import _get_status_symbols

logger = logging.getLogger(__name__)


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command to check Claude CLI installation.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    result = verify_claude()
    # Minimal output until Step 5 rewrites this
    symbols = _get_status_symbols()
    print("=== BASIC VERIFICATION ===")
    for key, entry in result.items():
        if key == "overall_ok":
            continue
        if isinstance(entry, dict):
            status = symbols["success"] if entry.get("ok") else symbols["failure"]
            print(f"{key}: {status} {entry.get('value', '')}")
    return 0 if result.get("overall_ok") else 1
