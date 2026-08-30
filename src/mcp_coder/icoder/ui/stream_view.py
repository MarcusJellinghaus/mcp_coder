"""Stream worker + stream-event rendering half of ``ICoderApp``.

Extracted from ``icoder/ui/app.py`` as a pure move so both halves stay well
under the repository file-size gate. ``ICoderApp`` derives from
``StreamViewApp``, so every member below is still reached by its original
name from ``ui/replay.py`` and the pilot tests.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime
from typing import Any

from textual.app import App
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.ui.widgets.busy_indicator import BusyIndicator
from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog
from mcp_coder.llm.formatting.render_actions import (
    ErrorMessage,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)
from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    format_tool_start,
)
from mcp_coder.llm.types import StreamEvent

logger = logging.getLogger(__name__)

STYLE_TOOL_OUTPUT = "white on #0a0a2e"
STYLE_CANCELLED = "dim #e8a838"


class StreamViewApp(App[None]):
    """Stream worker + stream-event rendering half of ``ICoderApp``.

    Owns the per-turn streaming state (renderer, text buffer, open assistant
    turn, open tool units, cancel event) and the worker/dispatch methods that
    mutate it. ``_core`` is supplied by the concrete subclass.
    """

    _core: AppCore

    def __init__(self, *, format_tools: bool = True, **kwargs: Any) -> None:
        """Initialize the per-turn streaming state.

        Args:
            format_tools: Enable tool output formatting (default True).
            **kwargs: Passed to App.__init__.
        """
        super().__init__(**kwargs)
        self._renderer = StreamEventRenderer(format_tools=format_tools)
        self._text_buffer: str = ""
        # Open assistant turn (clickable unit) currently accumulating text.
        self._current_turn_id: str | None = None
        self._current_turn_text: str = ""
        # Per raw-tool-name FIFO of open tool unit ids awaiting a result.
        # Mirrors the renderer's own ``_pending`` FIFO (positional matching).
        self._open_tool_units: dict[str, deque[str]] = {}
        self._unit_counter: int = 0
        self._cancel_event = threading.Event()

    def _stream_llm(self, text: str, skill_name: str | None = None) -> None:
        """Worker target: stream LLM response in background thread.

        Uses call_from_thread() to post updates to the UI event loop.

        Args:
            text: User input to send to LLM.
            skill_name: Provenance of a skill-initiated turn, forwarded to the
                core so it can look up the per-turn permission frame, or ``None``.
        """
        self._cancel_event.clear()
        _error_handled = False
        try:
            for event in self._core.stream_llm(text, skill_name):
                if self._cancel_event.is_set():
                    break
                self.call_from_thread(self._handle_stream_event, event)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _error_handled = True
            self.call_from_thread(self._flush_buffer)
            self.call_from_thread(self._finalize_turn)
            self.call_from_thread(self._cleanup_orphan_tools)
            self.call_from_thread(self._show_error, str(exc))
            self.call_from_thread(self._reset_busy_indicator)
            self.call_from_thread(self._append_blank_line)
        finally:
            if self._cancel_event.is_set() and not _error_handled:
                # Strict order: flush partial text, close the turn, then
                # resolve orphaned tool units as cancelled BEFORE the
                # cancelled marker (so the marker lands below patched blocks).
                self.call_from_thread(self._flush_buffer)
                self.call_from_thread(self._finalize_turn)
                self.call_from_thread(self._cleanup_orphan_tools)
                self.call_from_thread(self._append_cancelled_marker)
                self.call_from_thread(self._reset_busy_indicator)
                self.call_from_thread(self._append_blank_line)
            elif not _error_handled:
                self.call_from_thread(self._reset_busy_indicator)

    def _append_blank_line(self) -> None:
        """Write an empty line to the output log for visual spacing."""
        self.query_one(OutputLog).write("")

    def _flush_buffer(self) -> None:
        """Flush any buffered text to OutputLog and clear the streaming tail.

        The pending partial line is appended to the open assistant turn (so
        it stays a clickable unit) when one is in progress; otherwise it
        falls back to ``append_text`` (e.g. a stray flush with no turn).
        """
        if self._text_buffer:
            output = self.query_one(OutputLog)
            if self._current_turn_id is not None:
                self._current_turn_text += self._text_buffer
                output.extend_open_unit(self._current_turn_id, [self._text_buffer])
            else:
                output.append_text(self._text_buffer)
            self._text_buffer = ""
        self.query_one("#streaming-tail", Static).update("")

    def _new_unit_id(self, kind: str) -> str:
        """Return a fresh, monotonic unit id for ``kind``.

        Args:
            kind: Short kind tag used as the id prefix (e.g. ``"tool"``).

        Returns:
            A unique id of the form ``f"{kind}_{n}"``.
        """
        self._unit_counter += 1
        return f"{kind}_{self._unit_counter}"

    def _finalize_turn(self) -> None:
        """Close the open assistant turn, persisting its accumulated text.

        Writes the final ``full_text`` onto the turn unit (for the modal)
        and finalizes it. No-op when no turn is open.
        """
        if self._current_turn_id is not None:
            output = self.query_one(OutputLog)
            output.update_unit_and_rerender(
                self._current_turn_id, full_text=self._current_turn_text
            )
            output.finalize_open_unit(self._current_turn_id)
            self._current_turn_id = None
            self._current_turn_text = ""

    def _cleanup_orphan_tools(self) -> None:
        """Resolve still-open tool units as cancelled and reset the FIFOs.

        Asks the renderer to synthesize cancelled ``ToolResult``s for any
        orphaned tool starts, then updates the matching open tool unit (by
        raw name, positional FIFO) to a cancelled state. Any deque left
        non-empty after pairing signals a FIFO desync between the renderer
        and this app: it is WARN-logged (not silently swept) before clearing.
        """
        output = self.query_one(OutputLog)
        for cancelled in self._renderer.cleanup_pending():
            dq = self._open_tool_units.get(cancelled.raw_name)
            if dq:
                unit_id = dq.popleft()
                output.update_unit_and_rerender(
                    unit_id,
                    output="(cancelled)",
                    output_lines=("(cancelled)",),
                    total_lines=1,
                    truncated=False,
                    duration_ms=None,
                    is_error=True,
                    full_text="(cancelled)",
                )
        for raw_name, dq in self._open_tool_units.items():
            if dq:
                logger.warning(
                    "FIFO desync: %d open tool units remain for %s after cleanup",
                    len(dq),
                    raw_name,
                )
                dq.clear()

    def _handle_stream_event(
        self, event: StreamEvent, *, replay_mode: bool = False
    ) -> None:
        """Render a single stream event in the output log.

        Args:
            event: StreamEvent dict with a "type" key.
            replay_mode: When True, skip token-display updates (used during
                JSONL log replay where token usage should not change).
        """
        if event.get("type") == "permission_warning":
            self.query_one(OutputLog).append_text(
                str(event.get("message", "")), style=STYLE_CANCELLED
            )
            return
        output = self.query_one(OutputLog)
        action = self._renderer.render(event)
        if action is None:
            return

        if isinstance(action, TextChunk):
            self.query_one(BusyIndicator).show_busy("Thinking...")
            if self._current_turn_id is None:
                turn_id = self._new_unit_id("turn")
                output.append_unit(
                    ContentUnit(
                        id=turn_id,
                        kind="assistant_turn",
                        timestamp=datetime.now(),
                        full_text="",
                    ),
                    [],
                )
                self._current_turn_id = turn_id
                self._current_turn_text = ""
            self._text_buffer += action.text
            lines = self._text_buffer.split("\n")
            for line in lines[:-1]:
                self._current_turn_text += line + "\n"
                output.extend_open_unit(self._current_turn_id, [line])
            self._text_buffer = lines[-1]
            self.query_one("#streaming-tail", Static).update(self._text_buffer)
            return

        # Any non-text action: flush buffer first
        self._flush_buffer()

        if isinstance(action, StreamDone):
            self.query_one(BusyIndicator).show_ready()
            if not replay_mode:
                self._update_token_display()
            self._finalize_turn()
            self._cleanup_orphan_tools()
            self._append_blank_line()
        elif isinstance(action, ToolStart):
            self.query_one(BusyIndicator).show_busy(action.display_name)
            start_lines = format_tool_start(action, full=False)
            tool_id = self._new_unit_id("tool")
            output.append_unit(
                ContentUnit(
                    id=tool_id,
                    kind="tool",
                    timestamp=datetime.now(),
                    tool_name=action.display_name,
                    args=dict(action.args),
                ),
                start_lines,
                style=STYLE_TOOL_OUTPUT,
            )
            self._open_tool_units.setdefault(action.raw_name, deque()).append(tool_id)
        elif isinstance(action, ToolResult):
            dq = self._open_tool_units.get(action.raw_name)
            unit_id = dq.popleft() if dq else None
            if unit_id is None:
                logger.warning(
                    "FIFO desync: no open tool unit for ToolResult %s",
                    action.raw_name,
                )
            if unit_id is not None:
                raw_output = str(event.get("output", ""))
                output.update_unit_and_rerender(
                    unit_id,
                    output=raw_output,
                    output_lines=tuple(action.output_lines),
                    total_lines=action.total_lines,
                    truncated=action.truncated,
                    duration_ms=action.duration_ms,
                    is_error=action.is_error,
                )
            self.query_one(BusyIndicator).show_busy(f"Thinking about {action.name}...")
        elif isinstance(action, ErrorMessage):
            output.append_text(f"Error: {action.message}")

    def _reset_busy_indicator(self) -> None:
        """Reset busy indicator to ready state."""
        self.query_one(BusyIndicator).show_ready()

    def _append_cancelled_marker(self) -> None:
        """Append dim orange '— Cancelled —' marker to output."""
        self.query_one(OutputLog).append_text("— Cancelled —", style=STYLE_CANCELLED)

    def _show_error(self, message: str) -> None:
        """Display error message in output log.

        Args:
            message: Error text to display.
        """
        self.query_one(OutputLog).append_text(f"Error: {message}")

    def _update_token_display(self) -> None:
        """Update status bar token zone from app_core.token_usage."""
        usage = self._core.token_usage
        token_widget = self.query_one("#status-tokens", Static)
        if usage.has_data:
            token_widget.update(usage.display_text())
            token_widget.remove_class("hidden")
        else:
            token_widget.add_class("hidden")
