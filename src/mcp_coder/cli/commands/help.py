"""Help commands for the MCP Coder CLI."""

import argparse
import logging

logger = logging.getLogger(__name__)


def execute_help(args: argparse.Namespace) -> int:
    """Execute help command. Returns exit code."""
    logger.info("Executing help command")

    help_text = get_help_text()
    print(help_text)

    logger.info("Help command completed successfully")
    return 0


def get_help_text() -> str:
    """Get comprehensive help text for all commands."""
    help_content = """MCP Coder - AI-powered software development automation toolkit

USAGE:
    mcp-coder <command> [options]

COMMANDS:
    help                    Show help information
    verify                  Verify Claude CLI installation and configuration
    commit auto             Auto-generate commit message using LLM
    commit auto --preview   Show generated message and ask for confirmation
    commit clipboard        Use commit message from clipboard

{examples}

For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder""".format(
        examples=get_usage_examples()
    )

    return help_content





def get_usage_examples() -> str:
    """Get usage examples for common workflows."""
    return """EXAMPLES:
    mcp-coder help                    # Show this help
    mcp-coder verify                  # Check Claude CLI installation
    mcp-coder commit auto             # Analyze changes and auto-commit
    mcp-coder commit auto --preview   # Review generated message before commit
    mcp-coder commit clipboard        # Commit with clipboard message"""
