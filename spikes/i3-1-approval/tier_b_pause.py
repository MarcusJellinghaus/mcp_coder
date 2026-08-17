"""Tier B (pause) — pending counter defeats BOTH timeouts; verbatim consumer dies.

Reuses the Tier B setup (``FakeChatModel`` + a tool that blocks on a
cross-thread Future, from ``_common.py``) but drives a **pause-aware** copy of
the consumer, proving gotcha #4 and D1: a legitimately paused turn survives
both the inactivity ``q.get(timeout=…)`` and the ``_AGENT_OVERALL_TIMEOUT``
wall-clock cap.

  * ``scenario_pause_survives`` — the tool pauses for ``RESOLVER_THINK_TIME``
    (5s), longer than BOTH ``INACTIVITY_TIMEOUT`` (2s) and ``OVERALL_CAP`` (3s).
    The pause-aware consumer (``run_bridge_paused``) re-waits on ``queue.Empty``
    while ``pending.value > 0`` and computes the cap over ``elapsed - paused``,
    so the turn still completes.
  * ``scenario_baseline_dies`` — NEGATIVE CONTROL (F5/F10): identical setup and
    identical 5s think-time, but driving the VERBATIM (non-pause) ``run_bridge``
    from ``_common.py`` under the same short timeouts. Its consumer raises
    ``TimeoutError`` (captured on ``BridgeRun.error``), proving the pause is
    load-bearing, not vacuous.

Only the pause-aware consumer variant and its pausing tool live here; the fake
model, ``Gate`` and the verbatim bridge come from ``_common.py`` unchanged.

Rejected alternative — KEEPALIVES (record, do NOT implement; D1):
  Keepalives are rejected in favour of the pending counter. The
  ``_AGENT_OVERALL_TIMEOUT`` check sits *inside* the consumer loop (``:524``),
  so keepalive events are what **arm** the cap rather than resetting it (the
  negative control below substantiates exactly this — events flowing through
  the loop trip the cap). Keepalives also reach the session ``.jsonl``
  (``app_core.py:198``) and replay, and add an interval-tuning surface. A
  counter is only needed for pause. (This text is lifted into ``FINDINGS.md``
  in Step 6.)

Run directly::

    python spikes/i3-1-approval/tier_b_pause.py

Requires the REAL langchain/langgraph in the venv. Exits 0 with a ``PASS:``
line per mechanic; any failed assertion raises ``AssertionError``.
"""

from __future__ import annotations

import asyncio
import queue
import sys
import threading
import time
import uuid
from pathlib import Path

from langchain_core.tools import StructuredTool

# Allow ``python spikes/i3-1-approval/tier_b_pause.py`` to import the sibling.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    FakeChatModel,
    Gate,
    run_bridge,
    wait_for,
)

from mcp_coder.llm.providers.langchain.agent import run_agent_stream  # noqa: E402

# Small local constants stand in for the monkeypatched production values (#4):
# the natural 300s / 3600s are never exercised — the whole point is short,
# deterministic timeouts with a fixed resolver think-time between them.
INACTIVITY_TIMEOUT = 2.0  # models q.get(timeout=…); natural 300s not exercised
OVERALL_CAP = 3.0  # models _AGENT_OVERALL_TIMEOUT; natural 3600s not exercised
RESOLVER_THINK_TIME = 5.0  # > INACTIVITY_TIMEOUT and > OVERALL_CAP, so a
#                            non-pause consumer WOULD die under these values


# ---------------------------------------------------------------------------
# Thread-safe pending-approval counter
# ---------------------------------------------------------------------------


class PendingCounter:
    """Thread-safe pending-approval counter (Lock-guarded int).

    The counter #1045 already pins as the observation channel; here it also
    *drives* the pause decision — ``run_bridge_paused`` re-waits on
    ``queue.Empty`` only while ``value > 0``.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._n = 0

    def incr(self) -> None:
        with self._lock:
            self._n += 1

    def decr(self) -> None:
        with self._lock:
            self._n -= 1

    @property
    def value(self) -> int:
        with self._lock:
            return self._n


# ---------------------------------------------------------------------------
# Pause-aware blocking tool (the pause counterpart of _common.make_blocking_tool)
# ---------------------------------------------------------------------------


def make_pausing_tool(gate: Gate, pending: PendingCounter):  # type: ignore[no-untyped-def]
    """Factory -> tool coroutine that marks itself pending while it awaits.

    Identical to ``_common.make_blocking_tool`` except it brackets the
    ``await`` with ``pending.incr()`` / ``pending.decr()`` — it calls
    ``incr()`` when it BEGINS awaiting the Future and ``decr()`` immediately
    after it resolves. That is the signal ``run_bridge_paused`` reads to decide
    an ``Empty`` is a legitimate pause rather than genuine inactivity.
    """

    async def ping() -> str:
        loop = asyncio.get_running_loop()
        gate.loop = loop
        gate.future = loop.create_future()
        pending.incr()
        gate.fired = True
        try:
            return await gate.future
        finally:
            pending.decr()

    return ping


def _build_gen_factory(  # type: ignore[no-untyped-def]
    model: FakeChatModel, gate: Gate, pending: PendingCounter
):
    """Return ``gen_factory(cancel_event)`` -> real ``run_agent_stream(...)``.

    The tool is the pause-aware variant closed over THIS scenario's ``gate`` and
    ``pending``; ``cancel_event`` is the bridge-owned Event, wired through
    exactly as production wires its ``cancel`` into ``run_agent_stream``. Both
    scenarios use this SAME factory — the only difference between them is the
    consumer (pause-aware vs verbatim), which is what makes the negative control
    a true control.
    """
    tool = StructuredTool.from_function(
        coroutine=make_pausing_tool(gate, pending),
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


# ---------------------------------------------------------------------------
# Pause-aware consumer (the pause counterpart of _common.run_bridge)
# ---------------------------------------------------------------------------


def run_bridge_paused(gen_factory, pending: PendingCounter) -> list:  # type: ignore[no-untyped-def]
    """Bridge copy WITH pause, run synchronously on the calling thread.

    Same producer side as ``_common.run_bridge`` (agent ``asyncio.run`` on a
    daemon thread feeding a ``queue.Queue``). The consumer differs in exactly
    two lines relative to the verbatim copy:

      * on ``queue.Empty``, re-wait (``continue``) while ``pending.value > 0``
        instead of raising — that is the inactivity-timeout defeat;
      * the overall-cap comparison is ``(elapsed) - paused`` instead of plain
        ``elapsed`` — paused wall-time does not count against the cap.

    Runs synchronously (not on a worker thread like ``_common.run_bridge``)
    because the pause scenario COMPLETES rather than staying blocked, so the
    final events list can simply be returned. Returns ``list[StreamEvent]``.
    """
    q: queue.Queue = queue.Queue()
    error_holder: list[BaseException] = []
    cancel = threading.Event()

    async def _run() -> None:
        try:
            async for event in gen_factory(cancel):
                q.put(event)
        except Exception as exc:  # pylint: disable=broad-except
            error_holder.append(exc)
        finally:
            q.put(None)  # sentinel

    def _thread_main() -> None:
        asyncio.run(_run())

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()

    events: list = []
    start = time.monotonic()
    paused = 0.0
    try:
        while True:
            try:
                event = q.get(timeout=INACTIVITY_TIMEOUT)
            except queue.Empty as exc:
                if pending.value > 0:
                    paused += INACTIVITY_TIMEOUT  # re-wait, don't die
                    continue
                cancel.set()
                raise TimeoutError(
                    f"LLM inactivity timeout (langchain): no response for "
                    f"{INACTIVITY_TIMEOUT}s while nothing pending."
                ) from exc
            if event is None:
                break
            if (time.monotonic() - start) - paused > OVERALL_CAP:  # cap excludes paused
                cancel.set()
                raise TimeoutError(
                    f"Agent execution exceeded {OVERALL_CAP}s overall timeout"
                )
            events.append(event)
    finally:
        thread.join(timeout=5)

    if error_holder:
        raise error_holder[0]
    return events


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


def _start_resolver(gate: Gate, decision: str) -> threading.Thread:
    """Driver thread: wait for the tool to block, think 5s, then resolve.

    5s (> both timeouts) is the fixed resolver think-time; a non-pause consumer
    would raise ``TimeoutError`` long before it.
    """

    def resolver() -> None:
        assert wait_for(lambda: gate.fired), "tool never reached its await"
        assert gate.loop is not None and gate.future is not None
        time.sleep(RESOLVER_THINK_TIME)
        # PUSH the resolution onto the agent loop (never poll).
        gate.loop.call_soon_threadsafe(gate.future.set_result, decision)

    t = threading.Thread(target=resolver, daemon=True)
    t.start()
    return t


def scenario_pause_survives() -> None:
    """A paused turn survives BOTH the inactivity timeout and the overall cap (D1)."""
    model = FakeChatModel()
    gate = Gate()
    pending = PendingCounter()

    _start_resolver(gate, "resolve")

    t0 = time.monotonic()
    events = run_bridge_paused(_build_gen_factory(model, gate, pending), pending)
    elapsed = time.monotonic() - t0

    # The turn actually COMPLETED: the fake was invoked a 2nd time (post-tool)
    # and its 'done' assistant text streamed back through the bridge. Events are
    # ``raw_line`` dicts wrapping langgraph's astream_events JSON, so the final
    # assistant text surfaces as an ``on_chat_model_end`` line carrying
    # ``content='done'``.
    assert model.invoke_count == 2, (
        f"turn did not complete: model invoked {model.invoke_count} times "
        "(expected 2 — tool_call then 'done')"
    )
    done_line = [
        e
        for e in events
        if "on_chat_model_end" in e.get("line", "") and "content='done'" in e.get("line", "")
    ]
    assert done_line, f"final assistant 'done' text never streamed: {events!r}"
    assert pending.value == 0, f"pending counter not drained: {pending.value}"

    # Survived the inactivity timeout: the run outlived INACTIVITY_TIMEOUT (at
    # least one Empty re-wait happened) yet still completed.
    assert elapsed > INACTIVITY_TIMEOUT, (
        f"run finished in {elapsed:.2f}s — did not outlast the "
        f"{INACTIVITY_TIMEOUT}s inactivity timeout, so surviving it is vacuous"
    )
    print("PASS: pause-survives-inactivity")

    # Survived the overall cap: the run outlived OVERALL_CAP yet still completed,
    # because the cap is computed over elapsed - paused.
    assert elapsed > OVERALL_CAP, (
        f"run finished in {elapsed:.2f}s — did not outlast the {OVERALL_CAP}s "
        "overall cap, so surviving it is vacuous"
    )
    print("PASS: pause-survives-overall-cap")


def scenario_baseline_dies() -> None:
    """NEGATIVE CONTROL: same 5s think-time, VERBATIM consumer, raises TimeoutError."""
    model = FakeChatModel()
    gate = Gate()
    pending = PendingCounter()  # tool still marks pending; verbatim consumer ignores it

    _start_resolver(gate, "resolve")

    # Drive the VERBATIM run_bridge from _common.py (no pause branch) under the
    # SAME short timeouts. Its consumer runs on a worker thread, so the raise
    # reaches the main thread only via BridgeRun.error (Step 2's error channel).
    run = run_bridge(
        _build_gen_factory(model, gate, pending),
        inactivity_timeout=INACTIVITY_TIMEOUT,
        overall_cap=OVERALL_CAP,
    )
    run.join(timeout=10)

    assert isinstance(run.error, TimeoutError), (
        f"expected the verbatim consumer to raise TimeoutError under identical "
        f"conditions, got {run.error!r} — the pause would be vacuous"
    )
    print("PASS: baseline-without-pause-dies")


def main() -> None:
    scenario_pause_survives()
    scenario_baseline_dies()


if __name__ == "__main__":
    main()
