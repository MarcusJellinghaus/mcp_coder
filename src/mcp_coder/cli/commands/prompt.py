"""Prompt command for the MCP Coder CLI."""

import argparse
import logging
from typing import Any, Dict

from ...llm_providers.claude.claude_code_api import ask_claude_code_api_detailed_sync

logger = logging.getLogger(__name__)


def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question.

    Args:
        args: Command line arguments with prompt attribute and optional verbosity

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Executing prompt command")

    try:
        # Call Claude API using detailed function
        response_data = ask_claude_code_api_detailed_sync(args.prompt, 30)

        # Route to appropriate formatter based on verbosity level
        verbosity = getattr(args, "verbosity", "just_text")
        if verbosity == "verbose":
            formatted_output = _format_verbose(response_data)
        else:
            # Default to just-text format
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


def _format_verbose(response_data: Dict[str, Any]) -> str:
    """Format response data as verbose output with detailed tool interactions and metrics.

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with Claude response + tool details + performance metrics + session info
    """
    # Extract Claude's response text
    response_text = response_data.get("text", "").strip()

    # Extract session info
    session_info = response_data.get("session_info", {})
    session_id = session_info.get("session_id", "unknown")
    model = session_info.get("model", "unknown")
    tools = session_info.get("tools", [])
    mcp_servers = session_info.get("mcp_servers", [])

    # Extract performance metrics
    result_info = response_data.get("result_info", {})
    duration_ms = result_info.get("duration_ms", 0)
    cost_usd = result_info.get("cost_usd", 0.0)
    usage = result_info.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    # Extract tool interactions from raw messages
    raw_messages = response_data.get("raw_messages", [])
    tool_interactions = []
    for message in raw_messages:
        if message.get("role") == "assistant" and "tool_calls" in message:
            for tool_call in message.get("tool_calls", []):
                tool_name = tool_call.get("name", "unknown_tool")
                tool_params = tool_call.get("parameters", {})
                tool_interactions.append(f"  - {tool_name}: {tool_params}")

    # Build formatted output sections
    formatted_parts = []

    # Claude response
    if response_text:
        formatted_parts.append(response_text)
        formatted_parts.append("")

    # Tool interactions section
    formatted_parts.append("=== Tool Interactions ===")
    if tool_interactions:
        for interaction in tool_interactions:
            formatted_parts.append(interaction)
    else:
        formatted_parts.append("  No tool calls made")
    formatted_parts.append("")

    # Performance metrics section
    formatted_parts.append("=== Performance Metrics ===")
    duration_sec = duration_ms / 1000.0
    formatted_parts.append(f"  Duration: {duration_sec:.2f}s ({duration_ms}ms)")
    formatted_parts.append(f"  Cost: ${cost_usd:.4f}")
    formatted_parts.append(f"  Tokens: input={input_tokens}, output={output_tokens}")
    formatted_parts.append("")

    # Session information section
    formatted_parts.append("=== Session Information ===")
    formatted_parts.append(f"  Session ID: {session_id}")
    formatted_parts.append(f"  Model: {model}")
    if tools:
        formatted_parts.append(f"  Available Tools: {', '.join(tools)}")
    if mcp_servers:
        formatted_parts.append("  MCP Servers:")
        for server in mcp_servers:
            server_name = server.get("name", "unknown")
            server_status = server.get("status", "unknown")
            formatted_parts.append(f"    - {server_name}: {server_status}")

    return "\n".join(formatted_parts)
