"""Replay JSONL event logs into ICoderApp's UI primitives."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_coder.icoder.core.event_log import EventLog, iter_events
from mcp_coder.icoder.ui import runtime_banner
from mcp_coder.icoder.ui.widgets.output_log import ContentUnit, OutputLog

from .app import STYLE_USER_INPUT

if TYPE_CHECKING:
    from .app import ICoderApp


def replay_log(
    app: "ICoderApp",
    path: Path,
    event_log: EventLog | None = None,
) -> None:
    """Replay a JSONL event log into ``app``'s UI primitives.

    Renders banner, user inputs, slash output, stream events, tool blocks,
    and the cancelled marker (when an LLM turn was interrupted) using the
    same UI methods as the live path. Updates ``app.command_history``.
    Does NOT update token usage.

    When ``event_log`` is supplied, every replayed event other than
    ``session_start`` is re-emitted into it, making the new run's log
    self-contained.

    Replayed ``ContentUnit`` timestamps are approximated as
    ``session_start_time + timedelta(seconds=event["t"])`` using the event's
    relative ``t`` offset. This reflects original event ordering, not
    wall-clock precision (the absolute session start time is unknown at
    replay time, so ``datetime.now()`` is used as the base).
    """
    output = app.query_one(OutputLog)
    session_start_time = datetime.now()
    in_flight = False
    for event in iter_events(path):
        kind = event.get("event")
        if kind == "session_start":
            output.append_text(
                "\n".join(runtime_banner.format_runtime_banner(event)), style="dim"
            )
        elif kind == "input_received":
            text = event.get("text")
            if isinstance(text, str):
                app._core.command_history.add(text)
                offset = event.get("t", 0.0)
                timestamp = session_start_time + timedelta(
                    seconds=float(offset) if isinstance(offset, (int, float)) else 0.0
                )
                unit = ContentUnit(
                    id=app._new_unit_id("user_input"),
                    kind="user_input",
                    timestamp=timestamp,
                    full_text=text,
                )
                output.append_unit(unit, [f"> {text}"], style=STYLE_USER_INPUT)
        elif kind == "output_emitted":
            text = event.get("text")
            if isinstance(text, str):
                output.append_text(text)
        elif kind == "llm_request_start":
            in_flight = True
        elif kind == "llm_request_end":
            in_flight = False
        elif kind == "stream_event":
            payload: dict[str, Any] = {
                k: v for k, v in event.items() if k not in ("event", "t")
            }
            app._handle_stream_event(payload, replay_mode=True)
        # any other event type → ignored (forward-compat)
        if event_log is not None and isinstance(kind, str) and kind != "session_start":
            extra = {k: v for k, v in event.items() if k not in ("event", "t")}
            event_log.emit(kind, **extra)
    if in_flight:
        app._flush_buffer()
        app._finalize_turn()
        app._cleanup_orphan_tools()
        app._append_cancelled_marker()
        app._append_blank_line()
