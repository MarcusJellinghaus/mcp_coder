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
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from textual.app import App
from textual.widgets import Static

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.permissions.approval import ApprovalDecision
from mcp_coder.icoder.permissions.loader import LOCAL_SETTINGS_RELPATH
from mcp_coder.icoder.permissions.matcher import parse_matcher
from mcp_coder.icoder.permissions.model import Policy, Rule
from mcp_coder.icoder.permissions.persist import write_rule
from mcp_coder.icoder.ui.widgets.approval_modal import ApprovalModal
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
    pop_pending_tool,
)
from mcp_coder.llm.types import StreamEvent

logger = logging.getLogger(__name__)

STYLE_TOOL_OUTPUT = "white on #0a0a2e"
STYLE_CANCELLED = "dim #e8a838"


def _grant_rule(tool_name: str) -> Rule | None:
    """Build the whole-tool ``runtime`` grant a "remember" choice adds.

    A canonical ``mcp__server__tool`` name always parses to exactly one
    matcher, so the guard is a type-level safety net: on a malformed name the
    UI grants nothing (and the caller still answers the pending call) rather
    than raising on the UI thread.

    Args:
        tool_name: The canonical tool name from the ``approval_request`` event.

    Returns:
        The ``Rule(matcher, ALWAYS, "runtime")`` grant, or ``None`` when the
        name does not parse to a matcher.
    """
    matchers, errors = parse_matcher(tool_name)
    if errors or not matchers:
        logger.warning("no runtime grant for %r: %s", tool_name, errors)
        return None
    return Rule(matchers[0], Policy.ALWAYS, "runtime")


class StreamViewApp(App[None]):
    """Stream worker + stream-event rendering half of ``ICoderApp``.

    Owns the per-turn streaming state (renderer, text buffer, open assistant
    turn, open tool units, cancel event) and the worker/dispatch methods that
    mutate it. ``_core`` and ``_project_dir`` are supplied by the concrete
    subclass.
    """

    _core: AppCore
    _project_dir: Path

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
        # FIFO of open tool units awaiting a result:
        # (tool_run_id, raw_name, unit_id). Mirrors the renderer's own
        # ``_pending`` FIFO and is popped by the same ``pop_pending_tool``.
        self._open_tool_units: deque[tuple[str | None, str, str]] = deque()
        self._unit_counter: int = 0
        self._cancel_event = threading.Event()
        # Set exactly once by ``on_unmount``, never cleared: the worker thread
        # outlives the message pump, so its tail must stop talking to it.
        self._shutting_down = threading.Event()

    def on_unmount(self) -> None:
        """Stop the streaming worker so quitting never stalls (R9).

        Three halves, all required. Raising ``_shutting_down`` closes the UI
        door before the unwind starts (see
        :meth:`_call_from_thread_if_running`); the other two start the unwind
        itself, and they cover *different* turns:

        * ``cancel_pending_approvals()`` is the only thing that reaches a
          worker parked in ``q.get`` behind an unanswered approval — an
          interceptor blocked on a future emits no event, so none of the
          generic cancel paths can fire, and the turn would otherwise wait out
          the provider's 300s inactivity timeout;
        * ``_cancel_event`` covers the ordinary approval-free turn, where there
          is no pending future to cancel. The worker's ``for`` loop tests it on
          the next event and breaks, which closes the provider generator and
          runs its ``GeneratorExit`` path (``cancel.set()`` -> ``detach()`` ->
          ``join``). Without it the worker drains the whole remaining turn while
          the non-daemon thread-pool keeps the process alive at exit.
        """
        self._shutting_down.set()
        self._cancel_event.set()
        self._core.cancel_pending_approvals()

    def _call_from_thread_if_running(
        self, callback: Callable[..., None], *args: Any
    ) -> None:
        """Run *callback* on the UI thread, or drop it when the app is shutting down.

        ``App._shutdown()`` dispatches ``Unmount`` **after** ``_close_all()``
        and ``_close_messages()``, so a worker unwound by ``on_unmount`` reaches
        its tail against a message pump that is already gone.
        ``call_from_thread`` schedules onto ``App._loop`` and blocks on the
        result, and on a stopped-but-not-closed loop that callback never runs —
        the worker would block *forever*. Textual thread workers live in a
        ``ThreadPoolExecutor`` whose non-daemon threads are joined by
        ``concurrent.futures``' atexit hook, so that is a hung process, not a
        hung thread.

        The ``RuntimeError`` catch is the backstop for the race window only
        (``call_from_thread`` raises it once ``App._loop`` is gone). Every other
        exception is left to propagate.

        Args:
            callback: UI-thread callable to invoke.
            *args: Positional arguments forwarded to *callback*.
        """
        if self._shutting_down.is_set():
            return
        try:
            self.call_from_thread(callback, *args)
        except RuntimeError as exc:
            logger.debug("call_from_thread dropped during shutdown: %s", exc)

    def action_cancel_stream(self) -> None:
        """Cancel the stream AND any pending approval. No-op when idle.

        The engine call is the *direct* UI -> engine channel and is what
        actually unwinds a turn parked on an approval: all three generic paths
        (``cancel_event``, ``_cancel_event``, ``GeneratorExit``) are gated on an
        event arriving from the generator, and a blocked interceptor emits none,
        so none of them can trigger a cancel while the consumer waits in
        ``q.get``. They stay wired as the post-resolution backstop.
        """
        self._cancel_event.set()
        self._core.cancel_pending_approvals()

    def _persist_target(self) -> Path:
        """Return the file a ``persist`` grant is written to.

        Always the gitignored ``local`` layer: a personal "remember this" must
        never mutate a committed, team-shared config.
        """
        return self._project_dir / LOCAL_SETTINGS_RELPATH

    def _push_approval_modal(self, event: StreamEvent) -> None:
        """Push the :class:`ApprovalModal` for one ``approval_request`` event.

        Uses ``push_screen(screen, callback)``, never ``push_screen_wait``:
        this runs under ``call_from_thread``, which blocks the consumer thread
        until it returns, and both streaming timeouts are suspended while an
        approval is pending — a wait here would wedge the turn permanently.

        Args:
            event: The ``approval_request`` stream event.
        """
        approval_id = str(event.get("approval_id", ""))
        tool_name = str(event.get("tool_name", ""))
        args = event.get("args")
        modal = ApprovalModal(
            tool_name=tool_name,
            args=args if isinstance(args, dict) else {},
            source=str(event.get("source", "")),
            persist_target=self._persist_target(),
        )
        self.push_screen(
            modal, lambda d: self._apply_approval(approval_id, tool_name, d)
        )

    def _apply_approval(
        self,
        approval_id: str,
        tool_name: str,
        decision: ApprovalDecision | None,
    ) -> None:
        """Apply the modal's choice, then answer the pending call.

        ``None`` (choice ``5``) abandons the turn through the same path as
        ``Esc`` on the main screen and never resolves. A ``session`` or
        ``persist`` scope adds the whole-tool runtime grant first, so a later
        call in the same turn already resolves ``ALWAYS``; ``persist`` also
        writes the rule to :meth:`_persist_target` so it survives a relaunch.
        The Future itself is only ever touched by ``resolve_pending``, which
        runs in every branch.

        The parse guard runs before the write: ``write_rule`` inserts the
        matcher verbatim and ``loader._load_layer`` is per-layer atomic, so
        one rejected token would fail the whole ``local`` layer on the next
        launch. A failed write degrades to a session grant and says so; the
        single ``except OSError`` also covers ``PersistError``.

        Args:
            approval_id: The pending call's id from the event.
            tool_name: The canonical tool name from the event.
            decision: The user's decision, or ``None`` to cancel the turn.
        """
        if decision is None:
            self.action_cancel_stream()
            return
        if decision.scope in ("session", "persist"):
            rule = _grant_rule(tool_name)
            if rule is None:
                self.query_one(OutputLog).append_text(
                    f"Could not remember {tool_name}: not a valid matcher.",
                    style=STYLE_CANCELLED,
                )
            else:
                if decision.scope == "persist":
                    try:
                        write_rule(self._persist_target(), tool_name)
                    except OSError as exc:
                        logger.warning("persist write failed: %s", exc)
                        self.query_one(OutputLog).append_text(
                            f"Could not write the permission rule: {exc}",
                            style=STYLE_CANCELLED,
                        )
                self._core.add_runtime_rule(rule)
        self._core.resolve_pending(approval_id, decision)

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
                self._call_from_thread_if_running(self._handle_stream_event, event)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            _error_handled = True
            self._call_from_thread_if_running(self._flush_buffer)
            self._call_from_thread_if_running(self._finalize_turn)
            self._call_from_thread_if_running(self._cleanup_orphan_tools)
            self._call_from_thread_if_running(self._show_error, str(exc))
            self._call_from_thread_if_running(self._reset_busy_indicator)
            self._call_from_thread_if_running(self._append_blank_line)
        finally:
            if self._cancel_event.is_set() and not _error_handled:
                # Strict order: flush partial text, close the turn, then
                # resolve orphaned tool units as cancelled BEFORE the
                # cancelled marker (so the marker lands below patched blocks).
                self._call_from_thread_if_running(self._flush_buffer)
                self._call_from_thread_if_running(self._finalize_turn)
                self._call_from_thread_if_running(self._cleanup_orphan_tools)
                self._call_from_thread_if_running(self._append_cancelled_marker)
                self._call_from_thread_if_running(self._reset_busy_indicator)
                self._call_from_thread_if_running(self._append_blank_line)
            elif not _error_handled:
                self._call_from_thread_if_running(self._reset_busy_indicator)

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
        """Resolve still-open tool units as cancelled and reset the FIFO.

        Asks the renderer to synthesize cancelled ``ToolResult``s for any
        orphaned tool starts, then updates the matching open tool unit (by
        ``tool_run_id``, or name-FIFO when the provider emits no id) to a
        cancelled state. Any entry left over after pairing signals a FIFO
        desync between the renderer and this app: it is WARN-logged (not
        silently swept) before clearing.
        """
        output = self.query_one(OutputLog)
        for cancelled in self._renderer.cleanup_pending():
            entry = pop_pending_tool(
                self._open_tool_units, cancelled.tool_run_id, cancelled.raw_name
            )
            if entry is not None:
                output.update_unit_and_rerender(
                    entry[2],
                    output="(cancelled)",
                    output_lines=("(cancelled)",),
                    total_lines=1,
                    truncated=False,
                    duration_ms=None,
                    is_error=True,
                    full_text="(cancelled)",
                )
        if self._open_tool_units:
            logger.warning(
                "FIFO desync: %d open tool units left over after cleanup",
                len(self._open_tool_units),
            )
            self._open_tool_units.clear()

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
        if event.get("type") == "approval_request":
            self._push_approval_modal(event)
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
            self._open_tool_units.append((action.tool_run_id, action.raw_name, tool_id))
        elif isinstance(action, ToolResult):
            entry = pop_pending_tool(
                self._open_tool_units, action.tool_run_id, action.raw_name
            )
            unit_id = entry[2] if entry is not None else None
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
