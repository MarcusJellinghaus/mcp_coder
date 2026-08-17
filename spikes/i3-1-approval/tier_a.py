"""Tier A — pure-asyncio microscope for the I3.1 approval spike (#1044).

Settles the *mechanism* in isolation (no MCP, no langchain): a bare
``threading.Thread`` resolving an ``asyncio.Future`` that was created on the
agent loop, via ``loop.call_soon_threadsafe(...)``.

Proves:
  * gotcha #1 — Future affinity: a Future is bound to the loop that created it,
    and a foreign thread can only resolve it through ``call_soon_threadsafe``.
  * D6 — loop identity **by object**: the loop seen *inside* the interceptor
    coroutine is the same object ``asyncio.run`` created (compared by ``id()``).
  * D5 — registry reverse-order probe: each ``approval_id`` receives its own
    decision with no cross-wiring, because the resolver looks the Future up in
    the registry *inside the thread* (never handed the Future directly).
  * D2 groundwork — deny is just a decision string; cancel must be *pushed*
    onto the awaiting coroutine (``Future.cancel()`` -> ``CancelledError``).

Loop-handle rule: the agent-loop handle is always obtained with
``asyncio.get_running_loop()`` INSIDE the interceptor coroutine — never a
build-time handle. Run directly::

    python spikes/i3-1-approval/tier_a.py

Exits 0 with a ``PASS: <mechanic>`` line per demonstrated mechanic; any failed
assertion raises ``AssertionError`` (non-zero exit).
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass


@dataclass
class Approval:
    """A pending approval: its cross-thread Future plus the loop identity
    captured INSIDE the interceptor coroutine (``None`` until observed)."""

    future: "asyncio.Future[str]"
    loop_id: int | None = None


Registry = dict[str, Approval]  # approval_id -> Approval


async def interceptor(approval_id: str, registry: Registry) -> str:
    """Record the running-loop identity (D6), then await the cross-thread Future.

    The loop handle is obtained here — inside the coroutine that actually runs
    on the agent loop — never captured at build time.
    """
    loop = asyncio.get_running_loop()
    registry[approval_id].loop_id = id(loop)
    return await registry[approval_id].future


def resolve_from_thread(
    loop: asyncio.AbstractEventLoop,
    registry: Registry,
    approval_id: str,
    decision: str,
    think_time: float = 0.05,
) -> None:
    """Simulated UI-thread body.

    Looks the Future up in the REGISTRY (inside this thread), then pushes the
    decision onto the agent loop with ``call_soon_threadsafe``.

    Takes ``approval_id``, never a ``Future`` — mirroring #1045's production
    entry point ``resolve_pending(approval_id, decision)``. Handing the Future
    in directly would make the D5 probe pass green against a completely
    cross-wired registry, since it would only prove that two independent
    Futures resolve independently.
    """
    time.sleep(think_time)  # deterministic think-time; the coroutine is already awaiting
    fut = registry[approval_id].future
    loop.call_soon_threadsafe(fut.set_result, decision)


async def scenario_single() -> None:
    """Round-trip + loop identity by object (D6, gotcha #1)."""
    agent_loop = asyncio.get_running_loop()
    fut: "asyncio.Future[str]" = agent_loop.create_future()
    registry: Registry = {"a": Approval(fut)}

    task = asyncio.create_task(interceptor("a", registry))
    # Let the interceptor reach its await before the thread resolves.
    await asyncio.sleep(0)

    threading.Thread(
        target=resolve_from_thread,
        args=(agent_loop, registry, "a", "approve"),
    ).start()

    decision = await task

    assert registry["a"].loop_id == id(agent_loop), (
        f"D6 loop identity by object failed: "
        f"{registry['a'].loop_id} != {id(agent_loop)}"
    )
    print("PASS: loop-identity")

    assert decision == "approve", f"expected 'approve', got {decision!r}"
    print("PASS: cross-thread-resolve")


async def scenario_deny_cancel() -> None:
    """Deny decision (a plain string) and the Future.cancel() push (D2 groundwork)."""
    agent_loop = asyncio.get_running_loop()

    # --- deny: same round-trip, different decision string ---
    deny_fut: "asyncio.Future[str]" = agent_loop.create_future()
    registry: Registry = {"d": Approval(deny_fut)}
    deny_task = asyncio.create_task(interceptor("d", registry))
    await asyncio.sleep(0)
    threading.Thread(
        target=resolve_from_thread,
        args=(agent_loop, registry, "d", "deny"),
    ).start()
    decision = await deny_task
    assert decision == "deny", f"expected 'deny', got {decision!r}"
    print("PASS: deny")

    # --- cancel: must be pushed onto the awaiting coroutine ---
    cancel_fut: "asyncio.Future[str]" = agent_loop.create_future()
    registry["c"] = Approval(cancel_fut)
    cancel_task = asyncio.create_task(interceptor("c", registry))
    await asyncio.sleep(0)  # ensure the interceptor is awaiting the Future
    cancel_fut.cancel()
    raised = False
    try:
        await cancel_task
    except asyncio.CancelledError:
        raised = True
    assert raised, "cancelling the Future did not propagate CancelledError to the coroutine"
    print("PASS: cancel")


async def scenario_registry() -> None:
    """Two approvals resolved in REVERSE order with distinct decisions (D5).

    A cross-wired registry would hand the wrong Future the wrong decision and
    trip the asserts, because each thread resolves BY approval_id and does the
    registry lookup inside the thread.
    """
    agent_loop = asyncio.get_running_loop()
    fut_a: "asyncio.Future[str]" = agent_loop.create_future()
    fut_b: "asyncio.Future[str]" = agent_loop.create_future()
    registry: Registry = {"A": Approval(fut_a), "B": Approval(fut_b)}

    task_a = asyncio.create_task(interceptor("A", registry))
    task_b = asyncio.create_task(interceptor("B", registry))
    await asyncio.sleep(0)  # both interceptors reach their awaits

    decision_a = "approve-A"
    decision_b = "deny-B"

    # Resolve B FIRST, then A (reverse of creation/registration order).
    t_b = threading.Thread(
        target=resolve_from_thread,
        args=(agent_loop, registry, "B", decision_b),
    )
    t_a = threading.Thread(
        target=resolve_from_thread,
        args=(agent_loop, registry, "A", decision_a),
    )
    t_b.start()
    t_b.join()  # deterministic ordering: B resolves strictly before A is dispatched
    t_a.start()
    t_a.join()

    result_a = await task_a
    result_b = await task_b

    assert result_a == decision_a, f"cross-wiring: task A got {result_a!r}"
    assert result_b == decision_b, f"cross-wiring: task B got {result_b!r}"
    assert registry["A"].loop_id == id(agent_loop) == registry["B"].loop_id, (
        "both interceptors must observe the same agent loop by object"
    )
    print("PASS: registry-no-cross-wiring")


async def main() -> None:
    """Run every scenario on the agent-loop analog created by ``asyncio.run``."""
    agent_loop_id = id(asyncio.get_running_loop())
    await scenario_single()
    await scenario_deny_cancel()
    await scenario_registry()
    # Sanity: the loop never changed identity across scenarios.
    assert agent_loop_id == id(asyncio.get_running_loop())


if __name__ == "__main__":
    asyncio.run(main())
