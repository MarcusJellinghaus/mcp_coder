"""Replay JSONL event logs into ICoderApp's UI primitives."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from mcp_coder.icoder.core.event_log import iter_events
from mcp_coder.icoder.ui.widgets.output_log import OutputLog

from .app import STYLE_USER_INPUT, format_runtime_banner

if TYPE_CHECKING:
    from .app import ICoderApp


def replay_log(app: "ICoderApp", path: Path) -> None:
    """Replay a JSONL event log into ``app``'s UI primitives.

    Renders banner, user inputs, slash output, stream events, tool blocks,
    and the cancelled marker (when an LLM turn was interrupted) using the
    same UI methods as the live path. Updates ``app.command_history``.
    Does NOT update token usage. Does NOT emit anything to the current
    event log (that side-effect is handled in Step 11).
    """
    output = app.query_one(OutputLog)
    in_flight = False
    for event in iter_events(path):
        kind = event.get("event")
        if kind == "session_start":
            output.append_text("\n".join(format_runtime_banner(event)), style="dim")
        elif kind == "input_received":
            text = event.get("text")
            if isinstance(text, str):
                app._core.command_history.add(text)
                output.append_text(f"> {text}", style=STYLE_USER_INPUT)
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
    if in_flight:
        app._flush_buffer()
        app._append_cancelled_marker()
        app._append_blank_line()
