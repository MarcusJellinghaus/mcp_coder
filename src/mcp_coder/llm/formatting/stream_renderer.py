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

_HEAD_LINES = 10
_TAIL_LINES = 5
_TRUNCATION_THRESHOLD = _HEAD_LINES + _TAIL_LINES  # 15
_INLINE_ARG_LIMIT = 2

_ENVELOPE_FIELDS: frozenset[str] = frozenset(
    {
        "type",
        "role",
        "model",
        "stop_reason",
        "session_id",
        "usage",
    }
)

_MAIN_CONTENT_KEYS: tuple[str, ...] = ("result", "text", "content")


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


def _render_value(value: object) -> list[str]:
    """Render a single value into display lines.

    Returns:
        List of display lines rendered from the input value.
    """
    if isinstance(value, str):
        return value.splitlines() if value else [""]
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2).splitlines()
    return [str(value)]


def _render_tool_output(
    output: str, *, format_tools: bool = True
) -> tuple[list[str], int]:
    """Render tool output into display lines with field filtering and truncation.

    When *format_tools* is ``False``, return the raw output split into lines
    with no filtering or truncation.

    Otherwise:
    1. Try ``json.loads`` — if dict, apply field filtering:
       a. Find main content (first of result / text / content present).
       b. Render main content value directly.
       c. Collect extras (non-envelope, non-main keys) below a blank line.
    2. If not dict or JSON fails, split into plain text lines.
    3. Apply head/tail truncation when lines exceed threshold.

    Returns:
        ``(display_lines, total_line_count)``.
    """
    if not output:
        return ([], 0)

    if not format_tools:
        raw_lines = output.splitlines()
        return (raw_lines, len(raw_lines))

    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            lines: list[str] = []

            # Find main content key
            main_key: str | None = None
            for key in _MAIN_CONTENT_KEYS:
                if key in parsed:
                    main_key = key
                    break

            # Render main content
            if main_key is not None:
                lines.extend(_render_value(parsed[main_key]))

            # Collect and render extras
            extras: list[tuple[str, object]] = []
            for key, value in parsed.items():
                if key == main_key:
                    continue
                if key in _ENVELOPE_FIELDS:
                    continue
                extras.append((key, value))

            if extras and main_key is not None:
                lines.append("")  # blank separator between main content and extras
            if extras:
                for key, value in extras:
                    if isinstance(value, str) and "\n" in value:
                        lines.append(f"{key}:")
                        for subline in value.splitlines():
                            lines.append(f"  {subline}")
                    elif isinstance(value, str):
                        lines.append(f"{key}: {value}")
                    else:
                        lines.append(f"{key}: {json.dumps(value)}")
        else:
            lines = str(parsed).splitlines()
    except (json.JSONDecodeError, ValueError):
        lines = output.splitlines()

    total = len(lines)
    if total > _TRUNCATION_THRESHOLD:
        skipped = total - _HEAD_LINES - _TAIL_LINES
        lines = (
            lines[:_HEAD_LINES]
            + [f"... ({skipped} lines skipped)"]
            + lines[-_TAIL_LINES:]
        )
    return (lines, total)


class StreamEventRenderer:
    """Converts ``StreamEvent`` dicts into typed ``RenderAction`` dataclasses.

    Usage::

        renderer = StreamEventRenderer()
        action = renderer.render(event)
        if isinstance(action, TextChunk):
            ...
    """

    def __init__(self, *, format_tools: bool = True) -> None:
        self._format_tools = format_tools

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
            output_lines, total_lines = _render_tool_output(
                output, format_tools=self._format_tools
            )
            return ToolResult(
                name=_format_tool_name(name),
                output_lines=output_lines,
                total_lines=total_lines,
                truncated=total_lines > _TRUNCATION_THRESHOLD,
            )

        if event_type == "error":
            return ErrorMessage(message=str(event.get("message", "")))

        if event_type == "done":
            return StreamDone()

        return None
