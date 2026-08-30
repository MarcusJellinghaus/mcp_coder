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

The probe drives the real ``run_agent_stream`` through a local copy of
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
from dataclasses import dataclass
from typing import Any

from mcp_coder.llm.types import StreamEvent
from tests.llm.providers.langchain.approval_harness import (
    Gate,
    make_blocking_tool,
    make_fake_chat_model,
    require_real_langchain,
    wait_for,
)

#: Generous upper bound on how long the unwind may take to reach the sentinel.
_DRAIN_TIMEOUT = 5.0


@dataclass
class _ProbeResult:
    """Everything the probe observed about one cancelled turn.

    Attributes:
        model: The fake chat model, for its ``invoke_count``.
        thread: The agent thread, after the production ``join(timeout=5)``.
        events: The stream events that reached the consumer before the sentinel.
        caught: What ``_run``'s ``except Exception`` saw. Expected empty —
            ``CancelledError`` is a ``BaseException``.
        escaped: What propagated out of ``asyncio.run``. Production lets this
            kill the daemon thread; the probe records it instead.
        sentinel_seen: Whether the drain ended on the ``None`` sentinel rather
            than on its own timeout.
    """

    model: Any
    thread: threading.Thread
    events: list[StreamEvent]
    caught: list[Exception]
    escaped: list[BaseException]
    sentinel_seen: bool


def _run_cancel_probe() -> _ProbeResult:
    """Cancel a pending tool call on the real agent path and report the fallout.

    Starts the agent thread, waits until the blocking tool is parked on its
    Future, cancels that Future from *this* thread through the direct
    engine->loop channel (``call_soon_threadsafe``), drains the queue to the
    sentinel and joins with production's 5s budget.

    Returns:
        The observations, as a :class:`_ProbeResult`.
    """
    require_real_langchain("langchain_core", "langgraph")

    from mcp_coder.llm.providers.langchain.agent import run_agent_stream

    model = make_fake_chat_model()
    gate = Gate()
    tool = make_blocking_tool(gate)

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
        # Production runs a bare ``asyncio.run(_run())`` and lets a BaseException
        # end the daemon thread. The probe needs to *see* what escaped, so it
        # records it here; the recording is the only deviation from production.
        try:
            asyncio.run(_run())
        except BaseException as exc:  # pylint: disable=broad-except
            escaped.append(exc)

    thread = threading.Thread(target=_thread_main, daemon=True)
    thread.start()

    assert wait_for(lambda: gate.fired), "the tool never reached its await"
    loop = gate.loop
    future = gate.future
    assert loop is not None and future is not None

    # The DIRECT engine->loop cancel channel. None of the three generic cancel
    # paths can reach a parked interceptor (they are all gated on an event
    # arriving from the generator, and a parked tool emits none), which is
    # exactly why the engine owns this one.
    loop.call_soon_threadsafe(future.cancel)

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
