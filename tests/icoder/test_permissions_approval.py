"""Tests for the runtime approval engine (Step 4 of I3.2, TDD).

Pure asyncio: no langchain, no Textual, no ``AppCore``. The engine's two
cross-thread entry points (``resolve_pending`` / ``cancel_all``) are driven from
a **real** worker thread via ``asyncio.to_thread`` so the ``call_soon_threadsafe``
hand-over is actually exercised, not simulated on the same loop.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from uuid import UUID, uuid4

import pytest

from mcp_coder.icoder.permissions.approval import (
    _DENY_UNAVAILABLE,
    ApprovalDecision,
    ApprovalEngine,
    _PendingApproval,
)
from mcp_coder.llm.providers.langchain.approval_bridge import ApprovalBridge
from mcp_coder.llm.types import StreamEvent


async def _wait_until(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    """Poll *predicate* on the loop until it holds, or fail the test."""
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "condition not reached in time"
        await asyncio.sleep(0.005)


def _ask(
    engine: ApprovalEngine, tool_name: str = "mcp__srv__tool"
) -> "asyncio.Task[ApprovalDecision]":
    """Start one approval request as a task on the running loop.

    ``source`` carries the bare layer name, which is what the only producer
    (``gateway._source_label``) emits for a ``Layer`` — the other two shapes it
    can produce are ``"frame"`` and ``"default"``.
    """
    return asyncio.create_task(
        engine.request_approval(
            tool_name=tool_name, args={"path": "x"}, source="project"
        )
    )


def _teardown_during_insert(
    monkeypatch: pytest.MonkeyPatch, teardown: Callable[[], None]
) -> None:
    """Run *teardown* inside ``request_approval``'s guard-to-insert window.

    Both teardown paths walk the registry from another thread, so either can run
    after ``request_approval``'s opening guard but before the insert that
    follows it — seeing an empty registry, and therefore missing the entry that
    is about to be added. ``uuid4()`` is called in exactly that window, so
    hooking it turns the race into a deterministic interleaving.

    Args:
        monkeypatch: The active monkeypatch fixture.
        teardown: The engine teardown to interleave. Run exactly once, so the
            request's own ``finally`` is not re-entered.
    """
    fired: list[None] = []

    def _hook() -> UUID:
        if not fired:
            fired.append(None)
            teardown()
        return uuid4()

    monkeypatch.setattr("mcp_coder.icoder.permissions.approval.uuid4", _hook)


def _approval_id(event: StreamEvent) -> str:
    """Read the approval id out of an emitted ``approval_request`` event."""
    approval_id = event["approval_id"]
    assert isinstance(approval_id, str)
    return approval_id


async def test_allow_decision_resolved_from_another_thread() -> None:
    """An allow answered off-loop reaches the awaiting coroutine intact."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    task = _ask(engine)
    await _wait_until(lambda: bool(events))

    assert events[0]["type"] == "approval_request"
    assert events[0]["tool_name"] == "mcp__srv__tool"
    assert events[0]["args"] == {"path": "x"}
    assert events[0]["source"] == "project"

    await asyncio.to_thread(
        engine.resolve_pending,
        _approval_id(events[0]),
        ApprovalDecision("allow", "session"),
    )
    decision = await asyncio.wait_for(task, timeout=2)

    assert decision.outcome == "allow"
    assert decision.scope == "session"
    assert engine.pending() == 0


async def test_deny_decision_resolved_from_another_thread() -> None:
    """A deny answered off-loop reaches the awaiting coroutine intact."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    task = _ask(engine)
    await _wait_until(lambda: bool(events))
    await asyncio.to_thread(
        engine.resolve_pending,
        _approval_id(events[0]),
        ApprovalDecision("deny", "once"),
    )
    decision = await asyncio.wait_for(task, timeout=2)

    assert decision.outcome == "deny"
    assert decision.scope == "once"
    assert decision.reason is None


async def test_two_concurrent_asks_emit_one_at_a_time_in_arrival_order() -> None:
    """Only the front approval is emitted; answering it promotes the next."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    first = _ask(engine, "mcp__srv__first")
    second = _ask(engine, "mcp__srv__second")
    await _wait_until(lambda: engine.pending() == 2)

    assert len(events) == 1
    assert events[0]["tool_name"] == "mcp__srv__first"

    arrival = engine.pending_ids()  # arrival order: insertion precedes any await
    assert len(arrival) == 2
    assert arrival[0] == _approval_id(events[0])

    await asyncio.to_thread(
        engine.resolve_pending, arrival[0], ApprovalDecision("allow", "once")
    )
    first_decision = await asyncio.wait_for(first, timeout=2)

    assert first_decision.outcome == "allow"
    await _wait_until(lambda: len(events) == 2)
    assert events[1]["tool_name"] == "mcp__srv__second"
    assert _approval_id(events[1]) == arrival[1]

    await asyncio.to_thread(
        engine.resolve_pending, arrival[1], ApprovalDecision("deny", "once")
    )
    second_decision = await asyncio.wait_for(second, timeout=2)

    assert second_decision.outcome == "deny"
    assert engine.pending() == 0


async def test_pending_count_covers_the_whole_window() -> None:
    """The registry entry exists before the emit and until the answer lands."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    pending_at_emit: list[int] = []

    def _sink(event: StreamEvent) -> None:
        pending_at_emit.append(engine.pending())
        events.append(event)

    engine.attach(_sink)
    assert engine.pending() == 0

    task = _ask(engine)
    await _wait_until(lambda: bool(events))

    assert pending_at_emit == [1]  # inserted *before* the emit (R10, structural)
    assert engine.pending() == 1

    await asyncio.to_thread(
        engine.resolve_pending,
        _approval_id(events[0]),
        ApprovalDecision("allow", "once"),
    )
    await asyncio.wait_for(task, timeout=2)
    assert engine.pending() == 0


async def test_cancel_all_unwinds_every_awaiting_coroutine() -> None:
    """cancel_all raises CancelledError everywhere and emits nothing further."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    first = _ask(engine, "mcp__srv__first")
    second = _ask(engine, "mcp__srv__second")
    await _wait_until(lambda: engine.pending() == 2)
    assert len(events) == 1

    await asyncio.to_thread(engine.cancel_all)

    with pytest.raises(asyncio.CancelledError):
        await first
    with pytest.raises(asyncio.CancelledError):
        await second

    assert engine.cancelled is True
    assert engine.turn_aborted is True  # interceptors were actually unparked
    assert len(events) == 1  # the queued sibling is never promoted
    assert engine.pending() == 0

    engine.attach(events.append)  # the next turn starts clean
    assert engine.turn_aborted is False


def test_cancel_all_with_nothing_pending_does_not_abort_the_turn() -> None:
    """An idle cancel — or the shutdown hook — leaves the turn recordable.

    ``cancelled`` rises either way: it is what stops further emits and unwinds
    later requests. But only a cancel that actually unparked an
    interceptor unwinds the provider generator past its ``done`` event, and only
    that turn must go unrecorded (R16). ``on_unmount`` fires ``cancel_all()`` on
    *every* quit, so conflating the two would discard the session record of a
    turn that finished normally while the user was quitting.
    """
    engine = ApprovalEngine()
    engine.attach(lambda event: None)

    engine.cancel_all()

    assert engine.cancelled is True
    assert engine.turn_aborted is False


async def test_detach_racing_the_insert_cancels_the_new_future(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A teardown that misses the entry must not leave the interceptor parked.

    ``detach()`` runs on the consumer thread and walks the registry, so it can
    land after ``request_approval``'s opening guard and before the insert — it
    then cancels nothing, unbinds the sink, and the entry appears in a registry
    nobody will look at again. Without the post-insert re-check the caller parks
    on a future that no ``resolve_pending``, ``cancel_all`` or ``detach`` can
    reach, and because ``pending()`` is non-zero both streaming timeouts stay
    suspended — so the turn wedges permanently rather than erroring.
    """
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)
    _teardown_during_insert(monkeypatch, engine.detach)

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(_ask(engine), timeout=2)

    assert events == []  # nothing is emitted onto a turn whose sink is gone
    assert engine.pending() == 0  # and no entry is leaked into the registry


async def test_cancel_all_racing_the_insert_cancels_the_new_future(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same window, entered by the direct cancel channel.

    ``cancel_all()`` hands the cancellation to the agent loop, so it walks a
    registry this entry has not reached yet and cannot cancel it. Without the
    re-check the engine goes on to *emit* an ``approval_request`` for a turn the
    user has already cancelled — pushing a modal that must never appear — and
    only unparks the caller later, once the deferred sweep happens to run.
    """
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)
    _teardown_during_insert(monkeypatch, engine.cancel_all)

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(_ask(engine), timeout=2)

    assert events == []
    assert engine.turn_aborted is True  # this turn really was unwound
    assert engine.pending() == 0


async def test_detach_clears_the_registry_and_unbinds_the_sink() -> None:
    """detach drops every pending entry and the per-turn sink."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)
    assert engine.is_attached() is True

    task = _ask(engine)
    await _wait_until(lambda: engine.pending() == 1)

    await asyncio.to_thread(engine.detach)

    assert engine.pending() == 0
    assert engine.pending_ids() == ()
    assert engine.is_attached() is False

    with pytest.raises(asyncio.CancelledError):
        await task


def test_attach_resets_cancelled_but_detach_keeps_it() -> None:
    """The cancelled flag survives detach; AppCore reads it afterwards."""
    engine = ApprovalEngine()
    engine.attach(lambda event: None)
    assert engine.cancelled is False

    engine.cancel_all()
    assert engine.cancelled is True

    engine.detach()
    assert engine.cancelled is True

    engine.attach(lambda event: None)
    assert engine.cancelled is False


async def test_detach_cancels_a_still_pending_approval() -> None:
    """A turn ending mid-approval unwinds the interceptor instead of parking it."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    task = _ask(engine)
    await _wait_until(lambda: engine.pending() == 1)

    await asyncio.to_thread(engine.detach)

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=2)
    assert engine.pending() == 0


def test_detach_on_a_closed_agent_loop_does_not_raise() -> None:
    """detach runs inside a finally that must not raise, closed loop included."""
    engine = ApprovalEngine()
    engine.attach(lambda event: None)

    loop = asyncio.new_event_loop()
    future: asyncio.Future[ApprovalDecision] = loop.create_future()
    loop.close()

    engine._loop = loop
    engine._pending["stale"] = _PendingApproval(future, {"type": "approval_request"})

    engine.detach()

    assert engine.pending() == 0
    assert engine.is_attached() is False


def test_unattached_engine_denies_without_awaiting() -> None:
    """A detached engine fails closed immediately, with its own deny reason."""
    engine = ApprovalEngine()
    coro = engine.request_approval(tool_name="mcp__srv__tool", args={}, source="user")

    with pytest.raises(StopIteration) as excinfo:
        coro.send(None)  # returns on the first step -> it never awaited

    decision: ApprovalDecision = excinfo.value.value
    assert decision.outcome == "deny"
    assert decision.scope == "once"
    assert decision.reason == _DENY_UNAVAILABLE
    assert engine.pending() == 0


def test_cancelled_turn_unwinds_instead_of_denying() -> None:
    """An ``ask`` reached after a cancel raises rather than refusing the call.

    ``_cancelled`` is armed by *every* ``cancel_all()`` and cleared only by
    ``attach()``, so an Escape press with nothing pending leaves it set for the
    rest of the turn while the consumer is still between events. A deny here
    would hand the model "no approval prompt was reachable" and invite it to
    re-plan around a refusal on a turn the user asked to abandon; the designed
    semantics are to unwind (R7), and the gateway propagates ``CancelledError``
    untouched.
    """
    engine = ApprovalEngine()
    engine.attach(lambda event: None)
    engine.cancel_all()

    coro = engine.request_approval(tool_name="mcp__srv__tool", args={}, source="user")
    with pytest.raises(asyncio.CancelledError):
        coro.send(None)  # raises on the first step -> it never awaited

    assert engine.pending() == 0
    # The other early return is unchanged: a *detached* engine still fails
    # closed with the deny reason (#1045 acceptance criterion), and detaching
    # does not clear ``_cancelled``, so the sink must go first.
    engine.attach(lambda event: None)
    engine.detach()

    detached = engine.request_approval(
        tool_name="mcp__srv__tool", args={}, source="user"
    )
    with pytest.raises(StopIteration) as excinfo:
        detached.send(None)

    decision: ApprovalDecision = excinfo.value.value
    assert decision.outcome == "deny"
    assert decision.reason == _DENY_UNAVAILABLE


def test_cancel_all_on_a_closed_agent_loop_does_not_raise() -> None:
    """A quit or Ctrl+C landing after ``asyncio.run`` closed the loop is inert.

    ``_loop`` stays bound until ``detach()`` nulls it, so ``cancel_all()`` can
    reach a closed loop from the Textual thread — uncaught, that is a
    ``RuntimeError`` on a key press or mid-shutdown in ``on_unmount``.
    """
    engine = ApprovalEngine()
    engine.attach(lambda event: None)

    loop = asyncio.new_event_loop()
    future: asyncio.Future[ApprovalDecision] = loop.create_future()
    loop.close()

    engine._loop = loop
    engine._pending["stale"] = _PendingApproval(future, {"type": "approval_request"})

    engine.cancel_all()

    assert engine.cancelled is True


def test_deny_rejects_a_durable_scope() -> None:
    """Deny is once-only in v1."""
    with pytest.raises(ValueError):
        ApprovalDecision("deny", "session")


async def test_deny_reason_round_trips_to_the_caller() -> None:
    """A reason override survives the cross-thread resolve."""
    engine = ApprovalEngine()
    events: list[StreamEvent] = []
    engine.attach(events.append)

    task = _ask(engine)
    await _wait_until(lambda: bool(events))
    await asyncio.to_thread(
        engine.resolve_pending,
        _approval_id(events[0]),
        ApprovalDecision("deny", "once", reason="no UI is attached"),
    )
    decision = await asyncio.wait_for(task, timeout=2)

    assert decision.reason == "no UI is attached"


def test_engine_conforms_to_the_bridge_protocol() -> None:
    """The engine satisfies the provider-side seam Protocol (checked by mypy)."""
    bridge: ApprovalBridge = ApprovalEngine()

    bridge.attach(lambda event: None)
    assert bridge.pending() == 0
    bridge.detach()
