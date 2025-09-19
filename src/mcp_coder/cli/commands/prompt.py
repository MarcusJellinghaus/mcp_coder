"""Prompt command for the MCP Coder CLI."""

import argparse
import logging
from typing import Any, Dict

from ...llm_providers.claude.claude_code_api import ask_claude_code_api_detailed_sync

logger = logging.getLogger(__name__)


def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question.

    Args:
        args: Command line arguments with prompt attribute

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Executing prompt command")

    try:
        # Call Claude API using detailed function
        response_data = ask_claude_code_api_detailed_sync(args.prompt, 30)

        # Format output using just-text format
        formatted_output = _format_just_text(response_data)

        # Print formatted output to stdout
        print(formatted_output)

        logger.info("Prompt command completed successfully")
        return 0

    except Exception as e:
        # Handle API errors
        logger.error("Prompt command failed: %s", str(e))
        print(f"Error: {str(e)}", file=__import__("sys").stderr)
        return 1


def _format_just_text(response_data: Dict[str, Any]) -> str:
    """Format response data as just-text output (default verbosity level).

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with Claude response + tool usage summary
    """
    # Extract Claude's response text
    response_text = response_data.get("text", "").strip()

    # Extract tools used from session info
    session_info = response_data.get("session_info", {})
    tools = session_info.get("tools", [])

    # Create tool usage summary
    if tools:
        tool_summary = f"Used {len(tools)} tools: {', '.join(tools)}"
    else:
        tool_summary = "No tools used"

    # Combine response and tool summary
    formatted_parts = []
    if response_text:
        formatted_parts.append(response_text)
    formatted_parts.append(f"\n--- {tool_summary} ---")

    return "\n".join(formatted_parts)
