"""Response formatting functions for different verbosity levels.

This module provides formatters that transform LLM response data into
human-readable output formats (text, verbose, raw).
"""

import json
import logging
import sys
from typing import IO, Any, Dict

from ..types import StreamEvent
from .sdk_serialization import extract_tool_interactions, serialize_message_for_json

logger = logging.getLogger(__name__)

__all__ = [
    "format_text_response",
    "format_verbose_response",
    "format_raw_response",
    "print_stream_event",
]


def format_text_response(response_data: Dict[str, Any]) -> str:
    """Format response data as simple text output (default verbosity level).

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


def format_verbose_response(response_data: Dict[str, Any]) -> str:
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

    # Extract tool interactions from raw messages using utility functions
    raw_messages = response_data.get("raw_messages", [])
    tool_interactions = extract_tool_interactions(raw_messages)

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


def format_raw_response(response_data: Dict[str, Any]) -> str:
    """Format response data as raw output with complete debug output including JSON structures.

    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync

    Returns:
        Formatted string with complete debugging information including JSON structures
    """
    # Start with everything from verbose format
    verbose_output = format_verbose_response(response_data)

    # Extract additional data for raw output
    raw_messages = response_data.get("raw_messages", [])
    api_metadata = response_data.get("api_metadata", {})

    # Build additional raw output sections
    formatted_parts = [verbose_output, ""]

    # Complete JSON API Response section
    formatted_parts.append("=== Complete JSON API Response ===")
    try:
        formatted_parts.append(
            json.dumps(response_data, indent=2, default=serialize_message_for_json)
        )
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        # If serialization fails (e.g., circular reference), fall back to string representation
        formatted_parts.append(f"JSON serialization failed: {e}")
        formatted_parts.append(f"Response data type: {type(response_data)}")
        formatted_parts.append(
            f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}"
        )
    formatted_parts.append("")

    # Raw Messages section with complete details
    formatted_parts.append("=== Raw Messages ===")
    if raw_messages:
        for i, message in enumerate(raw_messages):
            formatted_parts.append(f"Message {i + 1}:")
            try:
                formatted_parts.append(
                    json.dumps(message, indent=2, default=serialize_message_for_json)
                )
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
                # If individual message serialization fails, show basic info
                formatted_parts.append(f"Message serialization failed: {e}")
                formatted_parts.append(f"Message type: {type(message)}")
                formatted_parts.append(
                    f"Message string representation: {str(message)[:200]}..."
                )
            formatted_parts.append("")
    else:
        formatted_parts.append("  No raw messages available")
        formatted_parts.append("")

    # API Metadata section
    formatted_parts.append("=== API Metadata ===")
    if api_metadata:
        try:
            formatted_parts.append(
                json.dumps(api_metadata, indent=2, default=serialize_message_for_json)
            )
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            formatted_parts.append(f"API metadata serialization failed: {e}")
            formatted_parts.append(f"Metadata type: {type(api_metadata)}")
    else:
        formatted_parts.append("  No API metadata available")

    return "\n".join(formatted_parts)


def _format_tool_args(args: object) -> str:
    """Format tool arguments for text display."""
    if isinstance(args, dict):
        parts = [f"{k}={v!r}" for k, v in args.items()]
        return ", ".join(parts)
    return str(args) if args else ""


def _normalize_event_to_ndjson(event: StreamEvent) -> dict[str, object] | None:
    """Map a StreamEvent to Claude CLI stream-json compatible NDJSON dict.

    Returns None for event types that have no NDJSON representation.
    """
    event_type = event.get("type")

    if event_type == "text_delta":
        return {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": event.get("text", "")}],
            },
        }
    if event_type == "tool_use_start":
        return {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "",
                        "name": event.get("name", ""),
                        "input": event.get("args", {}),
                    }
                ],
            },
        }
    if event_type == "tool_result":
        return {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "",
                        "content": str(event.get("output", "")),
                    }
                ],
            },
        }
    if event_type == "done":
        result: dict[str, object] = {"type": "result"}
        if "session_id" in event:
            result["session_id"] = event["session_id"]
        if "usage" in event:
            result["usage"] = event["usage"]
        if "cost_usd" in event:
            result["total_cost_usd"] = event["cost_usd"]
        return result
    if event_type == "error":
        return {
            "type": "error",
            "message": str(event.get("message", "")),
        }
    return None


def print_stream_event(
    event: StreamEvent,
    output_format: str,
    file: IO[str] | None = None,
    err_file: IO[str] | None = None,
) -> None:
    """Print a single stream event to stdout based on output format.

    Args:
        event: StreamEvent dict to print
        output_format: One of "text", "ndjson", "json-raw"
        file: Output stream for normal output (default: stdout)
        err_file: Output stream for errors (default: stderr)

    Behavior by format:
        text: Print text_delta content inline (no newline between deltas).
              Tool calls shown with bordered sections.
        ndjson: Print normalized NDJSON line (Claude CLI schema).
        json-raw: Print raw_line content as-is.
    """
    if file is None:
        file = sys.stdout
    if err_file is None:
        err_file = sys.stderr
    event_type = event.get("type")

    if output_format == "json-raw":
        if event_type == "raw_line":
            print(event["line"], file=file, flush=True)
        return

    if output_format == "ndjson":
        ndjson = _normalize_event_to_ndjson(event)
        if ndjson is not None:
            print(json.dumps(ndjson), file=file, flush=True)
        return

    # text format
    if event_type == "text_delta":
        print(event.get("text", ""), end="", file=file, flush=True)
    elif event_type == "tool_use_start":
        name = event.get("name", "")
        args_str = _format_tool_args(event.get("args"))
        print(f"\n── tool: {name}({args_str}) ──", file=file)
    elif event_type == "tool_result":
        output = event.get("output", "")
        print(f"{output}\n{'─' * 26}", file=file)
    elif event_type == "error":
        print(event.get("message", ""), file=err_file)
    elif event_type == "done":
        print(file=file)
