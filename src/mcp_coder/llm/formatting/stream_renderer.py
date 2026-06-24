"""StreamEventRenderer — converts stream events into typed RenderActions.

Each ``render()`` call maps a single ``StreamEvent`` to a ``RenderAction``
(or ``None`` for unknown types). Consumers do ``isinstance`` dispatch on the
returned action to decide how to display it.

The renderer is **stateful**: it keeps a per-instance FIFO of pending tool
starts so each ``tool_result`` can be paired with its originating
``tool_use_start`` to compute ``duration_ms``. Because the FIFO survives
across turns, callers MUST invoke :meth:`StreamEventRenderer.cleanup_pending`
on cancellation and on ``StreamDone`` to synthesize cancelled results for any
orphaned tool starts and reset the FIFO.
"""

from __future__ import annotations

import json
import time
from collections import deque

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
      mcp__mcp-workspace__read_file  → mcp-workspace > read_file
      mcp__mcp-tools-py__run_pytest  → mcp-tools-py > run_pytest
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
            elif isinstance(child, str):
                lines.append(f"{key}: {child}")
            else:
                lines.append(f"{key}: {json.dumps(child)}")
        return lines
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return list(value)
        compact = json.dumps(value)
        if len(compact) <= _MAX_INLINE_LEN:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    return [json.dumps(value)]


def _render_tool_output(
    output: str, *, format_tools: bool = True, full: bool = False
) -> tuple[list[str], int, bool]:
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
        ``(display_lines, total_line_count, truncated)`` where ``truncated``
        is ``True`` when the original output exceeded the truncation
        threshold (independent of whether ``full`` suppressed the trim).
    """
    if not output:
        return ([], 0, False)

    if not format_tools:
        raw_lines = output.splitlines()
        return (raw_lines, len(raw_lines), False)

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
    truncated = total > _TRUNCATION_THRESHOLD
    if not full and truncated:
        skipped = total - _HEAD_LINES - _TAIL_LINES
        lines = (
            lines[:_HEAD_LINES]
            + [f"... ({skipped} {'line' if skipped == 1 else 'lines'} skipped)"]
            + lines[-_TAIL_LINES:]
        )
    return (lines, total, truncated)


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


def format_tool_oneline(
    *,
    name: str,
    args: dict[str, object],
    duration_ms: int | None,
    is_error: bool,
) -> str:
    """One-line tier-1 summary for a tool invocation.

    Status semantics (tri-state -- preserves the issue's running/done/error
    model without requiring a ToolResult object):
        - duration_ms is None AND is_error is False -> tool still running
        - duration_ms is not None AND is_error is False -> done
        - is_error is True -> error (duration optional; may be None if
          cancelled before completion)

    Examples::

        format_tool_oneline(name="read_file", args={"path": "src/main.py"},
                            duration_ms=120, is_error=False)
            -> read_file("src/main.py") done (120ms)

    Args:
        name: Display name of the tool (already shortened by the caller).
        args: Tool arguments; the first entry (insertion order) is summarized.
        duration_ms: Elapsed time in milliseconds, or ``None`` while running.
        is_error: Whether the tool invocation failed.

    Returns:
        A single line (no trailing newline) with status and optional duration.
    """
    if is_error:
        status = "error"
    elif duration_ms is None:
        status = "running…"
    else:
        status = "done"

    arg_part = ""
    if args:
        _key, value = next(iter(args.items()))
        rendered = _render_value_compact(value)
        if len(rendered) > 40:
            rendered = rendered[:37] + "…"
        arg_part = rendered

    oneline = f"⚙ {name}({arg_part}) → {status}"
    if duration_ms is not None:
        oneline += f" ({duration_ms}ms)"
    return oneline


def format_tool_compressed(
    *,
    name: str,
    args: dict[str, object],
    output_lines: tuple[str, ...],
    total_lines: int,
    truncated: bool,
    duration_ms: int | None,
    is_error: bool,
) -> list[str]:
    """Tier-2 compressed body lines for a completed tool invocation.

    Renders the ``│  …`` output body followed by a ``└ done`` /
    ``└ error`` footer. The footer for a successful tool reports the
    total line count (with ``truncated`` and ``duration_ms`` suffixes when
    present); an errored tool collapses to a bare ``└ error``.

    The companion start header (the ``┌`` line) is produced separately
    by :func:`format_tool_start`; this helper covers only the body + footer
    that follows it.

    Args:
        name: Display name of the tool (unused here; kept for signature
            symmetry with :func:`format_tool_oneline` and future use).
        args: Tool arguments (unused here; kept for signature symmetry).
        output_lines: Pre-rendered, already-truncated body lines.
        total_lines: Total line count of the original output.
        truncated: Whether head/tail truncation was applied.
        duration_ms: Elapsed time in milliseconds, or ``None``.
        is_error: Whether the tool reported an error.

    Returns:
        Body lines (each prefixed ``│  ``) followed by a footer line.
    """
    lines = [f"│  {ln}" for ln in output_lines]
    if is_error:
        lines.append("└ error")
    else:
        word = "line" if total_lines == 1 else "lines"
        detail = f"{total_lines} {word}"
        if truncated:
            detail += ", truncated"
        if duration_ms is not None:
            detail += f", {duration_ms}ms"
        lines.append(f"└ done ({detail})")
    return lines


class StreamEventRenderer:
    """Converts ``StreamEvent`` dicts into typed ``RenderAction`` dataclasses.

    The renderer is stateful: it maintains a FIFO of pending tool starts
    (``raw_name`` + monotonic start time) so each ``tool_result`` can be
    paired with its originating ``tool_use_start`` to compute
    ``duration_ms``. Callers MUST invoke :meth:`cleanup_pending` on
    cancellation and on ``StreamDone`` to flush orphaned tool starts.

    Usage::

        renderer = StreamEventRenderer()
        action = renderer.render(event)
        if isinstance(action, TextChunk):
            ...
    """

    def __init__(self, *, format_tools: bool = True) -> None:
        self._format_tools = format_tools
        self._pending: deque[tuple[str, float]] = deque()

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
            self._pending.append((name, time.monotonic()))
            return ToolStart(
                display_name=_format_tool_name(name),
                raw_name=name,
                args=args,
            )

        if event_type == "tool_result":
            name = str(event.get("name", ""))
            output = str(event.get("output", ""))
            output_lines, total_lines, truncated = _render_tool_output(
                output, format_tools=self._format_tools
            )
            duration_ms = self._pair_pending(name)
            return ToolResult(
                name=_format_tool_name(name),
                raw_name=name,
                output_lines=output_lines,
                total_lines=total_lines,
                truncated=truncated,
                is_error=bool(event.get("is_error", False)),
                duration_ms=duration_ms,
            )

        if event_type == "error":
            return ErrorMessage(message=str(event.get("message", "")))

        if event_type == "done":
            return StreamDone()

        return None

    def _pair_pending(self, name: str) -> int | None:
        """Pop the first pending start matching *name* and compute its duration.

        Walks the FIFO left-to-right and removes the first entry whose raw
        name equals *name* (positional matching within the same name).

        Returns:
            Elapsed time in milliseconds for the matched start, or ``None``
            when no pending start matches (an unpaired result).
        """
        for i, (pending_name, start) in enumerate(self._pending):
            if pending_name == name:
                del self._pending[i]
                return int((time.monotonic() - start) * 1000)
        return None

    def cleanup_pending(self) -> list[ToolResult]:
        """Synthesize cancelled-result actions for every orphaned tool start.

        Builds one ``ToolResult`` per still-pending ``tool_use_start`` (in
        FIFO order), each marked ``is_error=True`` with ``output_lines``
        ``["(cancelled)"]`` and ``duration_ms=None``. The raw tool name is
        preserved on ``raw_name`` so the caller can locate the matching open
        tool unit via the per-name FIFO. Clears the FIFO.

        Called by the app layer on cancellation and on ``StreamDone``.

        Returns:
            The synthesized cancelled results in FIFO order (empty when the
            FIFO is empty).
        """
        results = [
            ToolResult(
                name=_format_tool_name(name),
                raw_name=name,
                output_lines=["(cancelled)"],
                total_lines=1,
                truncated=False,
                is_error=True,
                duration_ms=None,
            )
            for name, _start in self._pending
        ]
        self._pending.clear()
        return results
