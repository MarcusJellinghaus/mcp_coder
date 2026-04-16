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
_MAX_INLINE_LEN = 100


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


def _render_value_compact(value: object) -> str:
    """Render a value as a single-line summary for compact arg display.

    Returns:
        Single-line string summary of the value. Long strings, long lists,
        lists containing dicts, and long dicts are summarized as counts.
    """
    if isinstance(value, str):
        if len(value) > 80:
            return f"({len(value)} chars)"
        return repr(value)
    if isinstance(value, list):
        if any(isinstance(item, dict) for item in value):
            return f"({len(value)} items)"
        compact = json.dumps(value)
        if len(compact) > 120:
            return f"({len(value)} items)"
        return compact
    if isinstance(value, dict):
        compact = json.dumps(value)
        if len(compact) > 120:
            return f"({len(value)} keys)"
        return compact
    return repr(value)


def _render_value_full(value: object) -> list[str]:
    """Render a value as multiple lines with full detail for block arg display.

    Returns:
        List of display lines: multiline strings split, long strings truncated
        to 120 chars, lists/dicts inline when short else pretty-printed JSON.
    """
    if isinstance(value, str):
        if "\n" in value:
            return value.splitlines()
        if len(value) > 120:
            return [f"{value[:117]}..."]
        return [value]
    if isinstance(value, (list, dict)):
        compact = json.dumps(value)
        if len(compact) <= 120:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    return [repr(value)]


def _render_output_value(value: object) -> list[str]:
    """Render any JSON value generically for tool output display.

    Recursively renders dicts: multiline string values become an indented
    block; nested dict/list values render inline when short or as an
    indented block when multi-line; scalar values render inline via
    ``json.dumps``.

    Returns:
        List of display lines for the rendered value.
    """
    if isinstance(value, str):
        if "\n" in value:
            return value.splitlines()
        return [value]
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, str) and "\n" in child:
                lines.append(f"{key}:")
                for sub in child.splitlines():
                    lines.append(f"  {sub}")
            elif isinstance(child, (dict, list)):
                rendered = _render_output_value(child)
                if len(rendered) == 1:
                    lines.append(f"{key}: {rendered[0]}")
                else:
                    lines.append(f"{key}:")
                    for sub in rendered:
                        lines.append(f"  {sub}")
            else:
                lines.append(f"{key}: {json.dumps(child)}")
        return lines
    if isinstance(value, list):
        compact = json.dumps(value)
        if len(compact) <= _MAX_INLINE_LEN:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    return [json.dumps(value)]


def _render_tool_output(
    output: str, *, format_tools: bool = True, full: bool = False
) -> tuple[list[str], int]:
    """Render tool output into display lines with optional truncation.

    When *format_tools* is ``False``, return the raw output split into lines
    with no parsing or truncation.

    Otherwise:
    1. Try ``json.loads`` — if a dict with a ``"result"`` key, render
       ``parsed["result"]`` via ``_render_output_value()`` and append any
       remaining keys (as extras) below a blank separator.
    2. If not a dict or no ``"result"`` key, render the parsed value via
       ``_render_output_value()``.
    3. If JSON parsing fails, split the raw output into lines.
    4. Apply head/tail truncation when ``full`` is ``False`` and lines
       exceed the threshold.

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
        if isinstance(parsed, dict) and "result" in parsed:
            lines = _render_output_value(parsed["result"])
            extras = {k: v for k, v in parsed.items() if k != "result"}
            if extras:
                lines.append("")
                lines.extend(_render_output_value(extras))
        else:
            lines = _render_output_value(parsed)
    except (json.JSONDecodeError, ValueError):
        lines = output.splitlines()

    total = len(lines)
    if not full and total > _TRUNCATION_THRESHOLD:
        skipped = total - _HEAD_LINES - _TAIL_LINES
        lines = (
            lines[:_HEAD_LINES]
            + [f"... ({skipped} {'line' if skipped == 1 else 'lines'} skipped)"]
            + lines[-_TAIL_LINES:]
        )
    return (lines, total)


def format_tool_start(action: ToolStart, full: bool = False) -> list[str]:
    """Format a ``ToolStart`` action into display lines.

    Returns a single inline header line when args fit in
    ``_MAX_INLINE_LEN`` characters, otherwise a block header with one
    line per arg. When args are present, a ``├──`` separator line is
    appended as the last line.

    Args:
        action: The ``ToolStart`` action to format.
        full: When ``True``, expand block args using full detail; when
            ``False``, use compact summaries for long values.

    Returns:
        A list of display lines.
    """
    if not action.args:
        return [f"\u250c {action.display_name}"]

    inline_parts = [
        f"{key}={_render_value_compact(value)}" for key, value in action.args.items()
    ]
    inline = f"\u250c {action.display_name}({', '.join(inline_parts)})"
    if len(inline) <= _MAX_INLINE_LEN:
        lines = [inline]
    else:
        lines = [f"\u250c {action.display_name}"]
        for key, value in action.args.items():
            if full:
                rendered = _render_value_full(value)
                if len(rendered) == 1:
                    lines.append(f"\u2502  {key}: {rendered[0]}")
                else:
                    lines.append(f"\u2502  {key}:")
                    for sub in rendered:
                        lines.append(f"\u2502    {sub}")
            else:
                lines.append(f"\u2502  {key}: {_render_value_compact(value)}")
    lines.append("\u251c\u2500\u2500")
    return lines


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
            if not isinstance(args, dict):
                args = {}
            return ToolStart(
                display_name=_format_tool_name(name),
                raw_name=name,
                args=args,
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
                truncated=len(output_lines) != total_lines,
            )

        if event_type == "error":
            return ErrorMessage(message=str(event.get("message", "")))

        if event_type == "done":
            return StreamDone()

        return None
