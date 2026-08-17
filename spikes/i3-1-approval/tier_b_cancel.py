"""Tier B (cancel) — real bridge, three inert cancel paths, direct resolve, 5s join.

Reconstructs the REAL thread+queue bridge (verbatim copy in ``_common.py``)
driven by a fake model and a tool that blocks on a cross-thread Future, then
proves gotcha #3 and D2:

  * ``scenario_inert``    — the three generic cancel paths are unobservable
    while the tool is blocked (``cancel_event`` checked only between
    ``astream_events`` iterations; ``GeneratorExit`` is *unrequestable* —
    ``gen.close()`` raises ``ValueError: generator already executing``; the TUI
    ``_cancel_event`` is gated on event arrival, and no event arrives).
  * ``scenario_direct``   — a DIRECT engine-side resolve of the Future unblocks
    the pending call, and after the real ``join(timeout=5)`` the agent thread
    ACTUALLY terminates (``is_alive() is False``).
  * ``scenario_backstop`` — ``cancel_event`` set while blocked (inert) becomes
    LIVE once the Future is resolved: on the first event after resume the
    agent breaks before ever invoking the model a second time.

Run directly::

    python spikes/i3-1-approval/tier_b_cancel.py

Requires the REAL langchain/langgraph in the venv. Exits 0 with a ``PASS:``
line per mechanic; any failed assertion raises ``AssertionError``.
"""

from __future__ import annotations

import sys
import threading
import time
import uuid
from pathlib import Path

from langchain_core.tools import StructuredTool

# Allow ``python spikes/i3-1-approval/tier_b_cancel.py`` to import the sibling.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FakeChatModel,
    Gate,
    make_blocking_tool,
    run_bridge,
    wait_for,
)

from mcp_coder.llm.providers.langchain.agent import run_agent_stream  # noqa: E402


def _build_gen_factory(model: FakeChatModel, gate: Gate):  # type: ignore[no-untyped-def]
    """Return ``gen_factory(cancel_event)`` -> real ``run_agent_stream(...)``.

    The tool is closed over THIS scenario's ``gate`` via ``make_blocking_tool``;
    ``cancel_event`` is the bridge-owned Event, wired through exactly as
    production wires its ``cancel`` into ``run_agent_stream``.
    """
    tool = StructuredTool.from_function(
        coroutine=make_blocking_tool(gate),
        name="ping",
        description="Blocks until the cross-thread Future is resolved.",
    )

    def gen_factory(cancel_event: threading.Event):  # type: ignore[no-untyped-def]
        return run_agent_stream(
            question="please call ping",
            chat_model=model,
            messages=[],
            mcp_config_path="",
            session_id=f"spike-i3-1-{uuid.uuid4()}",
            cancel_event=cancel_event,
            tools=[tool],
        )

    return gen_factory


def scenario_inert() -> None:
    """All three generic cancel paths do nothing while the tool is blocked (#3)."""
    model = FakeChatModel()
    gate = Gate()
    run = run_bridge(_build_gen_factory(model, gate))

    assert wait_for(lambda: gate.fired), "tool never reached its await"
    # Let the pre-block events (chat_model_start/end, tool_start) fully drain to
    # the worker's events list before snapshotting.
    assert wait_for(
        lambda: any(e.get("type") == "tool_use_start" for e in run.events)
    ), "tool_use_start never surfaced"
    time.sleep(0.3)  # settle: no further events can arrive while blocked
    before = list(run.events)

    # Path 1 — cancel_event: checked only BETWEEN astream_events iterations
    # (agent.py:569-570); no events flow while blocked, so setting it is inert.
    run.cancel_event.set()

    # Path 2 — GeneratorExit: UNREQUESTABLE while blocked. The worker thread is
    # inside next()/q.get(), executing the generator frame, so CPython refuses
    # gen.close() from this (main) thread.
    run.close()
    assert isinstance(run.close_error, ValueError), (
        f"expected ValueError from close() while blocked, got {run.close_error!r}"
    )
    assert "generator already executing" in str(run.close_error), (
        f"unexpected close() error text: {run.close_error!r}"
    )

    # Path 3 — TUI _cancel_event (ui/app.py:290): checked only AFTER an event
    # arrives from the generator. Model a minimal UI-consumer that would poll a
    # tui_cancel Event on each new event. No event arrives, so it never checks.
    tui_cancel = threading.Event()
    seen = len(run.events)
    tui_cancel.set()
    time.sleep(0.3)
    ui_would_check = len(run.events) > seen  # UI only wakes on a new event
    assert not ui_would_check, "unexpected new event let the TUI path become reachable"

    assert run.events == before, "a generic cancel path leaked a new event while blocked"
    assert run.agent_thread.is_alive(), "agent thread died despite being blocked"
    print("PASS: generic-paths-inert")


def scenario_direct() -> None:
    """Direct engine-side resolve unblocks; thread actually terminates (D2)."""
    model = FakeChatModel()
    gate = Gate()
    run = run_bridge(_build_gen_factory(model, gate))

    assert wait_for(lambda: gate.fired), "tool never reached its await"
    assert gate.loop is not None and gate.future is not None

    # PUSH the resolution onto the agent loop (never poll): this is the direct
    # engine-side path #1045 will use — NOT one of the generic cancel paths.
    gate.loop.call_soon_threadsafe(gate.future.set_result, "cancel")

    # tool returns -> fake returns 'done' -> generator drains -> join(timeout=5)
    run.join(timeout=10)
    assert run.error is None, f"consumer raised unexpectedly: {run.error!r}"
    print("PASS: direct-resolve-unblocks")

    assert run.agent_thread.is_alive() is False, (
        "agent thread still alive after join(5) — join returned but thread did not die"
    )
    print("PASS: thread-terminated")


def scenario_backstop() -> None:
    """cancel_event set while blocked fires as a backstop once resolved (D2 (c))."""
    model = FakeChatModel()
    gate = Gate()
    run = run_bridge(_build_gen_factory(model, gate))

    assert wait_for(lambda: gate.fired), "tool never reached its await"
    assert gate.loop is not None and gate.future is not None

    # INERT right now (scenario_inert already proved this): no events flow while
    # blocked and agent.py:569-570 is only reached between astream_events iters.
    run.cancel_event.set()

    # PUSH: events resume. On the FIRST event after resume the already-set
    # cancel_event is checked and the loop breaks — before the model is invoked
    # a second time. (Ordering must not invert: setting the flag only after a
    # tool result would race the run to completion and never fire.)
    gate.loop.call_soon_threadsafe(gate.future.set_result, "resolve")

    run.join(timeout=10)
    assert run.error is None, f"consumer raised unexpectedly: {run.error!r}"

    # DISCRIMINATOR (F15): do NOT assert absence of the {"type":"done"}
    # StreamEvent — agent.py:698 yields it unconditionally, cancelled or not.
    # Assert instead on what truly separates cancelled from completed: the
    # second model invoke never happened, and no 2nd-invoke assistant text
    # ('done') streamed back.
    assert model.invoke_count == 1, (
        f"backstop failed: model was invoked {model.invoke_count} times "
        "(break did not come before the 2nd invoke)"
    )
    post_resume_text = [
        e
        for e in run.events
        if e.get("type") == "text_delta" and e.get("text") == "done"
    ]
    assert not post_resume_text, (
        f"a 2nd-invoke text_delta leaked past the backstop: {post_resume_text!r}"
    )
    assert run.agent_thread.is_alive() is False, (
        "backstop did not terminate the agent thread"
    )
    print("PASS: backstop-fires-after-resolve")


def main() -> None:
    scenario_inert()
    scenario_direct()
    scenario_backstop()


if __name__ == "__main__":
    main()
