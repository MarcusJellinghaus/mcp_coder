# Step 1 — Tier A: pure-asyncio microscope

**Commit:** `spike(i3.1): Tier A — loop identity, cross-thread Future, registry probe`

Read `pr_info/steps/summary.md` first. This step builds the fast, deterministic core that
settles the *mechanism* (a bare thread resolving a Future created on the agent loop) in
isolation — no MCP, no langchain. It proves gotcha **#1** (Future affinity) and **D5/D6**.

## WHERE

- Create `spikes/i3-1-approval/tier_a.py` (single self-contained script).

## WHAT — functions / signatures

```python
from dataclasses import dataclass, field
import asyncio, threading

@dataclass
class Approval:
    future: asyncio.Future[str]
    loop_id: int | None = None          # id() of the loop seen INSIDE the coroutine

Registry = dict[str, Approval]          # approval_id -> Approval

async def interceptor(approval_id: str, registry: Registry) -> str:
    """Record the running-loop identity, then await the cross-thread Future."""

def resolve_from_thread(loop: asyncio.AbstractEventLoop, registry: Registry,
                        approval_id: str, decision: str) -> None:
    """Simulated UI thread body: look the Future up in the REGISTRY (inside the
    thread), then push the decision onto the agent loop.

    Takes ``approval_id``, never a ``Future`` — mirroring #1045's production
    entry point ``resolve_pending(approval_id, decision)``. Handing the Future
    in directly would make the D5 probe pass green against a completely
    cross-wired registry, since it would only prove that two independent
    Futures resolve independently.
    """

async def scenario_single() -> None:      # round-trip + identity (D6, #1)
async def scenario_deny_cancel() -> None: # deny decision + Future.cancel() path
async def scenario_registry() -> None:    # two approvals, reverse-order resolve (D5)

async def main() -> None:                 # runs all scenarios, prints PASS lines
```

## HOW — integration points

- `main()` is launched via `asyncio.run(main())` — this loop is the **agent-loop analog**;
  record `id(asyncio.get_running_loop())` in `main()` as `agent_loop_id`.
- Inside `interceptor`, capture `loop = asyncio.get_running_loop()` and store `id(loop)` in
  `registry[approval_id].loop_id` **before** awaiting — this is the D6 fact.
- The resolver runs on a bare `threading.Thread` (configurable think-time via `time.sleep`),
  handed the loop object plus the **registry and an `approval_id`**. It does the
  `registry[approval_id].future` lookup **inside the thread**, then calls
  `loop.call_soon_threadsafe(fut.set_result, decision)`. The lookup-in-thread is what makes the
  D5 probe able to catch a cross-wired registry.

## ALGORITHM — single round-trip (scenario_single)

```
agent_loop = get_running_loop(); fut = agent_loop.create_future()
registry["a"] = Approval(fut)
task = create_task(interceptor("a", registry))     # records loop_id, awaits fut
Thread(target=resolve_from_thread, args=(agent_loop, registry, "a", "approve")).start()
decision = await task
assert registry["a"].loop_id == id(agent_loop)      # D6: identity, not just success
assert decision == "approve"                         # #1: cross-thread resolve worked
```

## ALGORITHM — registry probe (scenario_registry, D5)

```
make Approval "A" and "B", each with its own future + its own interceptor task
resolve B first, then A (REVERSE order), each from its own thread with distinct decisions:
    Thread(target=resolve_from_thread, args=(agent_loop, registry, "B", decision_B)).start()
    ... then the same for "A"
# each thread resolves BY approval_id — the registry lookup happens inside the thread,
# so a cross-wired registry hands the wrong Future the wrong decision and the asserts fail
assert task_A result == decision_A and task_B result == decision_B   # no cross-wiring
```

- `scenario_deny_cancel`: resolve one future with `"deny"` (assert the coroutine returns
  `"deny"`); for a second future call `fut.cancel()` from the loop and assert the awaiting
  coroutine raises `asyncio.CancelledError` (proves cancel must be *pushed*, D2 groundwork).

## DATA

- `Registry` = `dict[str, Approval]`; each `Approval` carries the `Future`, the captured
  `loop_id`, and (implicitly) its resolved decision string.
- Decisions are plain strings: `"approve"` | `"deny"` (cancel via `Future.cancel()`).
- Script prints `PASS: loop-identity`, `PASS: cross-thread-resolve`, `PASS: deny`,
  `PASS: cancel`, `PASS: registry-no-cross-wiring`; exits 0.

## Definition of done

- `python spikes/i3-1-approval/tier_a.py` exits 0, all PASS lines printed, repeatable.
- Standard `src`/`tests` fast unit suite still green (no production files touched).
