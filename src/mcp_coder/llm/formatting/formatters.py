"""Streaming output formatting for Claude CLI stream events.

This module provides ``print_stream_event``, which renders a single
``StreamEvent`` to an output stream in one of several formats (rendered,
text, ndjson, json-raw) used by the CLI prompt path.
"""

import json
import logging
import sys
from typing import IO

from ..types import StreamEvent
from .render_actions import ErrorMessage, StreamDone, TextChunk, ToolResult, ToolStart
from .stream_renderer import (
    StreamEventRenderer,
    _render_value_compact,
    format_tool_start,
)

logger = logging.getLogger(__name__)

__all__ = [
    "print_stream_event",
]


def _normalize_event_to_ndjson(event: StreamEvent) -> dict[str, object] | None:
    """Map a StreamEvent to Claude CLI stream-json compatible NDJSON dict.

    Returns:
        NDJSON dict, or None for event types that have no NDJSON representation.
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
        output_format: One of "rendered", "text", "ndjson", "json-raw"
        file: Output stream for normal output (default: stdout)
        err_file: Output stream for errors (default: stderr)

    Behavior by format:
        - rendered: Human-friendly output with box-drawing characters for
          tool calls and truncated tool results.
        - text: Print text_delta content inline (no newline between deltas).
          Tool calls shown with bordered sections.
        - ndjson: Print normalized NDJSON line (Claude CLI schema).
        - json-raw: Print raw_line content as-is.
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

    if output_format == "rendered":
        renderer = StreamEventRenderer()
        action = renderer.render(event)
        if action is None:
            return
        if isinstance(action, TextChunk):
            print(action.text, end="", file=file, flush=True)
        elif isinstance(action, ToolStart):
            for line in format_tool_start(action, full=False):
                print(line, file=file)
        elif isinstance(action, ToolResult):
            for line in action.output_lines:
                print(f"\u2502  {line}", file=file)
            if action.truncated:
                print(
                    f"\u2514 done ({action.total_lines} lines, truncated to {len(action.output_lines)})",
                    file=file,
                )
            else:
                print("\u2514 done", file=file)
            print(file=file)
        elif isinstance(action, ErrorMessage):
            print(action.message, file=err_file)
        elif isinstance(action, StreamDone):
            print(file=file)
        return

    # text format
    if event_type == "text_delta":
        print(event.get("text", ""), end="", file=file, flush=True)
    elif event_type == "tool_use_start":
        name = str(event.get("name", ""))
        args = event.get("args") or {}
        if isinstance(args, dict):
            args_str = ", ".join(
                f"{k}={_render_value_compact(v)}" for k, v in args.items()
            )
        else:
            args_str = ""
        print(f"\n── tool: {name}({args_str}) ──", file=file)
    elif event_type == "tool_result":
        output = str(event.get("output", ""))
        print(f"{output}\n{'─' * 26}", file=file)
    elif event_type == "error":
        print(event.get("message", ""), file=err_file)
    elif event_type == "done":
        print(file=file)
