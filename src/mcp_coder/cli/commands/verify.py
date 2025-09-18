"""Verify command for the MCP Coder CLI."""

import argparse
import logging

from ...llm_providers.claude.claude_cli_verification import (
    verify_claude_cli_installation as _verify_claude_cli_installation,
)

logger = logging.getLogger(__name__)


def execute_verify(args: argparse.Namespace) -> int:
    """Execute verify command to check Claude CLI installation.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Executing verify command")
    return _verify_claude_cli_installation(args)
