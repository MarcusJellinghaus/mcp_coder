"""StreamEventRenderer — converts stream events into typed RenderActions.

The renderer is stateless: each ``render()`` call maps a single
``StreamEvent`` to a ``RenderAction`` (or ``None`` for unknown types).
Consumers do ``isinstance`` dispatch on the returned action to decide
how to display it.
"""

from __future__ import annotations

import json

from ..types import StreamEvent
from .render_actions import (
    ErrorMessage,
    RenderAction,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)

_TRUNCATION_LIMIT = 5
_INLINE_ARG_LIMIT = 2


def _format_tool_name(name: str) -> str:
    """Format tool name for rendered display.

    Strip 'mcp__' prefix, split on first remaining '__':
      mcp__workspace__read_file  → workspace > read_file
      mcp__tools-py__run_pytest  → tools-py > run_pytest
      Bash                       → Bash (unchanged)

    Returns:
        Shortened display name for the tool.
    """
    if name.startswith("mcp__"):
        rest = name[5:]
        server, _, tool = rest.partition("__")
        if tool:
            return f"{server} > {tool}"
        return server
    return name


def _format_tool_args(args: object) -> str:
    """Format tool arguments for text display.

    Returns:
        Formatted string of tool arguments.
    """
    if isinstance(args, dict):
        parts = [f"{k}={v!r}" for k, v in args.items()]
        return ", ".join(parts)
    return str(args) if args else ""


def _render_tool_output(output: str) -> tuple[list[str], int]:
    """Render tool output into display lines with truncation.

    1. If output is empty, return ([], 0)
    2. Try json.loads: if dict, expand top-level keys as "key: value" lines.
       For string values containing newlines, indent continuation lines.
    3. If json.loads fails, split output into plain text lines.
    4. Truncate to _TRUNCATION_LIMIT lines.

    Returns:
        (display_lines, total_line_count) — display_lines may be shorter
        than total_line_count if truncated.
    """
    if not output:
        return ([], 0)
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            lines: list[str] = []
            for key, value in parsed.items():
                if isinstance(value, str) and "\n" in value:
                    lines.append(f"{key}:")
                    for subline in value.splitlines():
                        lines.append(f"  {subline}")
                else:
                    if isinstance(value, str):
                        lines.append(f"{key}: {value}")
                    else:
                        lines.append(f"{key}: {json.dumps(value)}")
        else:
            lines = str(parsed).splitlines()
    except (json.JSONDecodeError, ValueError):
        lines = output.splitlines()
    total = len(lines)
    truncated = lines[:_TRUNCATION_LIMIT]
    return (truncated, total)


class StreamEventRenderer:
    """Converts ``StreamEvent`` dicts into typed ``RenderAction`` dataclasses.

    Usage::

        renderer = StreamEventRenderer()
        action = renderer.render(event)
        if isinstance(action, TextChunk):
            ...
    """

    def render(self, event: StreamEvent) -> RenderAction | None:
        """Map a single stream event to a render action.

        Returns:
            A ``RenderAction`` for known event types, or ``None`` for
            unrecognised types (e.g. ``raw_line``).
        """
        event_type = event.get("type")

        if event_type == "text_delta":
            return TextChunk(text=str(event.get("text", "")))

        if event_type == "tool_use_start":
            name = str(event.get("name", ""))
            args = event.get("args", {})
            display_name = _format_tool_name(name)

            if isinstance(args, dict) and len(args) <= _INLINE_ARG_LIMIT:
                inline_args = _format_tool_args(args)
                block_args: list[tuple[str, str]] = []
            else:
                inline_args = None
                if isinstance(args, dict):
                    block_args = [
                        (key, json.dumps(value)) for key, value in args.items()
                    ]
                else:
                    block_args = []

            return ToolStart(
                display_name=display_name,
                raw_name=name,
                inline_args=inline_args,
                block_args=block_args,
            )

        if event_type == "tool_result":
            name = str(event.get("name", ""))
            output = str(event.get("output", ""))
            output_lines, total_lines = _render_tool_output(output)
            return ToolResult(
                name=_format_tool_name(name),
                output_lines=output_lines,
                total_lines=total_lines,
                truncated=total_lines > _TRUNCATION_LIMIT,
            )

        if event_type == "error":
            return ErrorMessage(message=str(event.get("message", "")))

        if event_type == "done":
            return StreamDone()

        return None
