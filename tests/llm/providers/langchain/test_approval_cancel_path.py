"""Real-path probe: a tool-side ``CancelledError`` escapes the whole agent stack.

R7 of #1045 adopts *hard cancel* — cancelling the ``asyncio.Future`` an approval
interceptor is parked on unwinds the turn — but #1044 only demonstrated that in
Tier A (pure asyncio). Every real-langgraph spike scenario resolved its Future
with ``set_result``. This module closes that gap **before** any engine code is
written: it proves that a ``CancelledError`` raised inside a tool coroutine
escapes ``ToolNode`` -> ``astream_events`` -> the ``_run`` drainer intact.

It is also the permanent regression test behind the "cancel-while-pending ...
``thread.is_alive() is False``" acceptance criterion, so it is kept, not thrown
away.

The engine produces that ``CancelledError`` in **two** shapes, and both are
probed here: cancelling the Future a parked interceptor awaits, and raising on
``request_approval``'s first step when the turn is already cancelled — which
never suspends at all, and is therefore the shape langgraph's node wrapper has
not been observed handling.

The probes drive the real ``run_agent_stream`` through a local copy of
``_ask_agent_stream``'s consumer shape (background thread + ``asyncio.run`` +
``queue.Queue`` + ``None`` sentinel + ``join(timeout=5)``), so it measures the
production topology rather than a convenient one. It needs no credentials and no
network, so it stays **unmarked** and runs in the fast suite.

Every skip guard and every langchain import lives inside a function (see
``approval_harness`` for why CI makes the module-scope version wrong, and why
``importorskip`` alone is not enough in this directory).
"""

from __future__ import annotations

import asyncio
import queue
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp_coder.icoder.permissions.approval import ApprovalEngine
from mcp_coder.llm.types import StreamEvent
from tests.llm.providers.langchain.approval_harness import (
    TOOL_NAME,
    Gate,
    make_blocking_tool,
    make_fake_chat_model,
    require_real_langchain,
    wait_for,
)

#: Generous upper bound on how long the unwind may take to reach the sentinel.
#: Deliberately far above the probe's measured cost (~4.7s idle and serial):
#: under ``-n auto`` this probe competes with the other workers for the CPU, and
#: a deadline near the measured cost turns that contention into a flake. Only
#: the production ``thread.join(timeout=5)`` below keeps its real budget — that
#: one is the acceptance criterion, not a harness deadline.
_DRAIN_TIMEOUT = 30.0

#: Same reasoning, for the wait until the tool parks on its Future.
_GATE_TIMEOUT = 30.0


@dataclass
class _ProbeResult:
    """Everything the probe observed about one cancelled turn.

    Attributes:
        model: The fake chat model, for its ``invoke_count``.
        thread: The agent thread, after the production ``join(timeout=5)``.
        events: The stream events that reached the consumer before the sentinel.
        caught: What ``_run``'s ``except Exception`` saw. Expected empty —
            ``CancelledError`` is a ``BaseException``.
        escaped: What propagated out of ``asyncio.run``. Production catches a
            ``CancelledError`` one frame lower, so nothing reaches there; the
            probe leaves the drain uncaught precisely to record it.
        sentinel_seen: Whether the drain ended on the ``None`` sentinel rather
            than on its own timeout.
    """

    model: Any
    thread: threading.Thread
    events: list[StreamEvent]
    caught: list[Exception]
    escaped: list[BaseException]
    sentinel_seen: bool


def _drive_probe(
    tool: Any, on_started: Callable[[], None] | None = None
) -> _ProbeResult:
    """Run one turn against *tool*, drain it to the sentinel, join it, report.

    Holds the local copy of ``_ask_agent_stream``'s producer half (background
    thread + ``asyncio.run`` + ``queue.Queue`` + ``None`` sentinel +
    ``join(timeout=5)``), so every probe measures the production topology
    rather than a convenient one.

    Args:
        tool: The tool the scripted model asks for. It is what decides *how*
            the ``CancelledError`` arrives — parked on a Future and cancelled
            from outside, or raised before the coroutine ever suspends.
        on_started: Called on this thread once the agent thread is running, for
            a probe that has to reach into the live turn to trigger its cancel.

    Returns:
        The observations, as a :class:`_ProbeResult`.
    """
    require_real_langchain("langchain_core", "langgraph")

    from mcp_coder.llm.providers.langchain.agent import run_agent_stream

    model = make_fake_chat_model()

    # --- local copy of _ask_agent_stream's producer half ---
    q: queue.Queue[StreamEvent | None] = queue.Queue()
    caught: list[Exception] = []
    escaped: list[BaseException] = []
    cancel = threading.Event()

    async def _run() -> None:
        try:
            async for event in run_agent_stream(
                question="please call ping",
                chat_model=model,
                messages=[],
                mcp_config_path="",
                session_id=f"approval-probe-{uuid.uuid4()}",
                cancel_event=cancel,
                tools=[tool],
            ):
                q.put(event)
        except Exception as exc:  # pylint: disable=broad-except
            caught.append(exc)
        finally:
            q.put(None)  # sentinel

    def _thread_main() -> None:
        # Production also runs a bare ``asyncio.run(_run())`` here — but *its*
        # ``_run`` catches ``asyncio.CancelledError`` around the drain, so
        # nothing reaches this frame and no traceback lands on stderr. This
        # probe's ``_run`` deliberately omits that clause: proving what escapes
        # the agent stack is the whole point, and recording it here is the only
        # deviation from production.
        try:
            asyncio.run(_run())
        except BaseException as exc:  # pylint: disable=broad-except
            escaped.append(exc)

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()

    if on_started is not None:
        on_started()

    events: list[StreamEvent] = []
    sentinel_seen = False
    while True:
        try:
            event = q.get(timeout=_DRAIN_TIMEOUT)
        except queue.Empty:
            break
        if event is None:
            sentinel_seen = True
            break
        events.append(event)

    thread.join(timeout=5)

    return _ProbeResult(
        model=model,
        thread=thread,
        events=events,
        caught=caught,
        escaped=escaped,
        sentinel_seen=sentinel_seen,
    )


def _run_cancel_probe() -> _ProbeResult:
    """Cancel a tool **parked on its Future**, on the real agent path.

    Waits until the blocking tool is parked, then cancels that Future from
    *this* thread through the direct engine->loop channel — i.e. the
    ``CancelledError`` arrives at an ``await``.

    Returns:
        The observations, as a :class:`_ProbeResult`.
    """
    gate = Gate()
    tool = make_blocking_tool(gate)

    def _cancel_when_parked() -> None:
        assert wait_for(
            lambda: gate.fired, timeout=_GATE_TIMEOUT
        ), "the tool never reached its await"
        loop = gate.loop
        future = gate.future
        assert loop is not None and future is not None

        # The DIRECT engine->loop cancel channel. None of the three generic
        # cancel paths can reach a parked interceptor (they are all gated on an
        # event arriving from the generator, and a parked tool emits none),
        # which is exactly why the engine owns this one.
        loop.call_soon_threadsafe(future.cancel)

    return _drive_probe(tool, _cancel_when_parked)


def _make_precancelled_approval_tool(engine: ApprovalEngine) -> Any:
    """Build a tool that asks an **already cancelled** engine for approval.

    ``request_approval`` raises ``asyncio.CancelledError`` on its very first
    step when the turn is already cancelled, so the exception leaves this
    coroutine **before it ever suspends** — the shape the parked-Future probe
    cannot produce.

    Args:
        engine: The engine to ask. Must already be attached and cancelled.

    Returns:
        A ``StructuredTool`` usable with ``create_react_agent``.
    """
    require_real_langchain("langchain_core")

    from langchain_core.tools import StructuredTool  # pylint: disable=import-error

    async def _call() -> str:
        # No arguments: ``ToolNode`` validates the model's ``args`` against the
        # schema before the coroutine runs (see ``make_blocking_tool``).
        decision = await engine.request_approval(
            tool_name=f"mcp__test__{TOOL_NAME}", args={}, source="project"
        )
        return f"the request returned instead of raising: {decision.outcome}"

    return StructuredTool.from_function(
        coroutine=_call,
        name=TOOL_NAME,
        description="Asks an already-cancelled approval engine, and unwinds.",
    )


def _run_precancel_probe() -> _ProbeResult:
    """Drive a gated call whose approval raises **before** it can park.

    The engine is attached and then cancelled with nothing pending, which is
    the state an idle Escape press leaves behind for the rest of the turn.
    Nothing has to be triggered from outside afterwards: the raise happens on
    the agent loop, inside the tool coroutine, the moment the turn reaches it.

    Returns:
        The observations, as a :class:`_ProbeResult`.
    """
    engine = ApprovalEngine()
    engine.attach(lambda event: None)
    engine.cancel_all()
    return _drive_probe(_make_precancelled_approval_tool(engine))


def test_cancelled_error_escapes_the_agent_stream() -> None:
    """The tool-side ``CancelledError`` reaches the top of the agent thread.

    Three independent facts make the "hard cancel" of R7 real:

    * ``_run``'s ``except Exception`` catches **nothing** — ``CancelledError``
      is a ``BaseException``, so ``run_agent_stream``'s own
      ``except Exception: yield error; raise`` does not see it either;
    * exactly one exception propagates out of ``asyncio.run``, and it is an
      ``asyncio.CancelledError`` — langgraph neither absorbed nor converted it;
    * the model was invoked once, so the turn unwound instead of re-planning
      around a failed tool.
    """
    result = _run_cancel_probe()

    assert (
        result.caught == []
    ), f"_run's `except Exception` should see nothing, saw {result.caught!r}"
    assert (
        len(result.escaped) == 1
    ), f"expected exactly one escaping exception, got {result.escaped!r}"
    assert isinstance(
        result.escaped[0], asyncio.CancelledError
    ), f"expected CancelledError to escape, got {result.escaped[0]!r}"
    assert (
        result.model.invoke_count == 1
    ), f"the turn re-planned: model invoked {result.model.invoke_count} times"


def test_cancel_leaves_no_error_and_kills_the_thread() -> None:
    """The consumer sees no error event, and the agent thread is dead after 5s.

    This is the acceptance criterion the approval engine's ``detach()`` has to
    satisfy: cancelling the pending Future is what lets the existing
    ``thread.join(timeout=5)`` return with a *dead* thread instead of expiring
    against one parked forever on a Future nothing can resolve.

    Nothing is asserted about the ``done`` event: under hard cancel the yield at
    the end of ``run_agent_stream`` is never reached, and the point of the probe
    is the unwind, not the event list.
    """
    result = _run_cancel_probe()

    assert result.sentinel_seen, "the sentinel never arrived: the turn did not unwind"
    error_events = [e for e in result.events if e.get("type") == "error"]
    assert error_events == [], f"cancel surfaced an error event: {error_events!r}"
    assert result.caught == [], f"cancel recorded an exception: {result.caught!r}"
    assert (
        result.thread.is_alive() is False
    ), "agent thread still alive after join(5) — the cancel did not unwind it"


def test_a_precancelled_request_unwinds_the_turn_the_same_way() -> None:
    """A ``CancelledError`` raised *before* any await unwinds the turn too.

    The two tests above cover the shape where the interceptor parks and its
    Future is cancelled from outside. The engine also raises **on its first
    step**, without ever suspending, when ``request_approval`` finds the turn
    already cancelled — an idle Escape press arms that flag for the rest of the
    turn. Driving the coroutine with ``send(None)`` in a unit test pins the
    guard order but says nothing about how ``ToolNode`` -> ``astream_events``
    -> the ``_run`` drainer handle a node body that raises without suspending,
    which is the one shape langgraph has not been observed handling here.

    The asserted properties are deliberately the ones the parked-Future test
    asserts, because the outcome has to be identical: the turn unwinds to the
    sentinel, nothing is reported as an error, the ``CancelledError`` is what
    reaches the top of the agent thread (production's ``_run`` catches it there
    rather than letting ``asyncio.run`` print a traceback over a live Textual
    screen), the turn does not re-plan, and the thread is dead inside the
    production ``join(timeout=5)``.
    """
    result = _run_precancel_probe()

    assert result.sentinel_seen, "the sentinel never arrived: the turn did not unwind"
    error_events = [e for e in result.events if e.get("type") == "error"]
    assert error_events == [], f"the raise surfaced an error event: {error_events!r}"
    assert result.caught == [], f"the raise was recorded as an error: {result.caught!r}"
    assert (
        len(result.escaped) == 1
    ), f"expected exactly one escaping exception, got {result.escaped!r}"
    assert isinstance(
        result.escaped[0], asyncio.CancelledError
    ), f"langgraph converted the unwind into {result.escaped[0]!r}"
    assert (
        result.model.invoke_count == 1
    ), f"the turn re-planned: model invoked {result.model.invoke_count} times"
    assert (
        result.thread.is_alive() is False
    ), "agent thread still alive after join(5) — the raise did not unwind it"
