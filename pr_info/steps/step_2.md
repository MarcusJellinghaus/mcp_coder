# Step 2 — Tier B (cancel): real bridge, three inert cancel paths, 5s join

**Commit:** `spike(i3.1): Tier B cancel — inert generic paths, direct resolve, thread death`

Read `pr_info/steps/summary.md` first. This step reconstructs the **real** thread+queue bridge
(a verbatim copy of `llm/providers/langchain/__init__.py:479-534`) driven by a fake model and a
tool that blocks on a cross-thread Future. It proves gotcha **#3** and **D2**: the three generic
cancel paths are unobservable while blocked, a direct engine-side resolve unblocks, and the agent
thread **actually terminates** after the real 5s join.

## WHERE

- Create `spikes/i3-1-approval/_common.py` — the **shared harness**, imported by Step 3 and Step 5:
  `FakeChatModel`, the blocking-tool factory + per-scenario `Gate`, and the **verbatim
  `__init__.py:479-534` bridge copy** (`run_bridge` / `BridgeRun`). One copy only: the bridge copy's
  fidelity to production is load-bearing (§10.3) and three hand-maintained duplicates cannot stay
  faithful. Steps stay one-commit-each and sequential, so importing does not cost independence.
- Create `spikes/i3-1-approval/tier_b_cancel.py` — the Step 2 scenarios; imports from `_common.py`.

## WHAT — functions / signatures

In `_common.py` (shared with Steps 3 and 5):

```python
from dataclasses import dataclass
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

class FakeChatModel(BaseChatModel):
    """Replays a caller-supplied script of AIMessages, one per invoke.

    ``responses`` is the script; invoke N returns ``responses[N-1]``. The
    DEFAULT script is the 2-entry one Steps 3 and 5 use: 1st invoke ->
    AIMessage with one tool_call; 2nd invoke -> AIMessage('done').
    ``scenario_backstop`` passes its own 3-entry script (see below) — there is
    no separate knob, the script IS the configuration.

    Must be usable by ``create_react_agent`` (agent.py:549), which calls
    ``model.bind_tools(tools)`` — ``BaseChatModel.bind_tools`` raises
    ``NotImplementedError``, so override it (return ``self``, ignoring the
    tools).

    Implement the ASYNC method ``_agenerate``, not ``_generate``. The agent
    path is ``astream_events``, and ``BaseChatModel``'s default ``_agenerate``
    delegates to ``run_in_executor(None, self._generate, ...)`` — a model that
    implements only ``_generate`` therefore runs on a THREAD-POOL thread with
    no running loop, where ``asyncio.get_running_loop()`` raises
    ``RuntimeError`` and ``loop_id`` (below) is destroyed. ``_generate`` may
    stay unimplemented / raising. ``_agenerate`` must return a ``ChatResult``
    (a ``ChatGeneration`` wrapping the ``AIMessage``), never a bare
    ``AIMessage``.

    Records, per invoke (inside ``_agenerate``): ``loop_id`` =
    ``id(asyncio.get_running_loop())`` (the independent agent-loop reference
    Step 5's D6 check needs) and the ``messages`` list it was handed (Step 5
    asserts on the post-``ToolNode`` ``ToolMessage`` present in the 2nd
    invoke's list).
    """
    def __init__(self, responses: list[AIMessage] | None = None, **kw): ...  # None -> default 2-entry script
    def bind_tools(self, tools, **kw) -> "FakeChatModel": return self
    async def _agenerate(self, messages, stop=None, run_manager=None, **kw): ...  # -> ChatResult
    @property
    def _llm_type(self) -> str: return "fake"

# PER-SCENARIO handoff the driver thread uses to reach the agent loop.
# NOT module/class-level state: `scenario_inert` deliberately never resolves, so a shared
# `fired` flag stays True forever; the next scenario's wait-for-fired would then pass
# immediately — possibly before the new tool coroutine has published its loop/future — and
# resolve against the STALE loop/future. That breaks the determinism AC. One fresh instance
# per scenario, bound into the tool by closure.
@dataclass
class Gate:
    loop: asyncio.AbstractEventLoop | None = None
    future: asyncio.Future[str] | None = None
    fired: bool = False

def make_blocking_tool(gate: Gate):
    """Factory -> tool coroutine closed over THIS scenario's `gate`.

    The coroutine captures the agent loop via get_running_loop(), publishes it plus a fresh
    Future onto `gate`, sets `gate.fired = True`, then awaits the Future.
    """

class BridgeRun:
    """Handle for a running bridge so the main thread can poke it mid-block.

    A verbatim copy of __init__.py:479-534 is a *generator* (it ``yield``s) and
    cannot ``return`` a tuple, and a blocking calling-thread consumer cannot be
    poked (`cancel_event`, `gen.close()`) while the tool is still blocked — which
    scenario_inert/direct/backstop all require. So the copied consumer generator
    runs inside a **worker thread** here; this handle exposes what the scenarios
    assert on while the agent thread is still blocked.
    """
    events: list          # filled live by the worker as events are yielded
    agent_thread: threading.Thread   # the agent asyncio.run thread (for is_alive)
    error: BaseException | None      # exception raised by the copied consumer ON THE WORKER
                                     # THREAD, captured for the main thread. Without this there
                                     # is no error channel at all and Step 3's negative control
                                     # (F5) can never see the TimeoutError it must assert.
    close(self) -> None   # ATTEMPTS gen.close() on the copied consumer (the :530 path). CPython
                          # refuses close() while the generator frame is executing, and the worker
                          # thread sitting in `q.get(...)` IS executing it — so this raises
                          # ValueError("generator already executing"). Capture and expose that
                          # outcome; do not swallow it (scenario_inert asserts on it).
    join(self, timeout: float | None = None) -> None   # wait for the worker to drain

def run_bridge(gen_factory, inactivity_timeout: float = 300.0,
               overall_cap: float = 3600.0) -> BridgeRun:
    """Start the VERBATIM copy of __init__.py:479-534 (thread+queue+join(5)).

    The copied consumer generator is driven on a worker thread so the main
    thread stays free to set `cancel_event`, call `.close()`, or resolve the
    Future while the tool is blocked. Returns immediately with a `BridgeRun`
    handle exposing the live events list and the agent thread.

    `inactivity_timeout` feeds the copied `q.get(timeout=…)` (:515) and
    `overall_cap` the copied `_AGENT_OVERALL_TIMEOUT` check (:524). Defaults
    match production so `scenario_inert` — whose tool never resolves — is not
    killed by a short hardcoded value; Step 3's negative control passes its
    own short values instead.
    """
```

In `tier_b_cancel.py` (each scenario builds its **own** `Gate` + tool via `make_blocking_tool`):

```python
def scenario_inert() -> None:    # generic paths do nothing while blocked
def scenario_direct() -> None:   # direct resolve unblocks; thread.is_alive() is False
def scenario_backstop() -> None: # after resolve, re-armed cancel_event DOES fire (backstop)
```

## HOW — integration points

- Build the agent generator with the **real** `run_agent_stream` from
  `mcp_coder.llm.providers.langchain.agent`, passing `chat_model=FakeChatModel()`,
  `tools=[StructuredTool.from_function(coroutine=make_blocking_tool(gate), name="ping", ...)]`,
  `mcp_config_path=""`, a dummy `session_id`, and a real `threading.Event` as `cancel_event`.
- Each scenario constructs a **fresh `Gate()`** and passes it to `make_blocking_tool` — no shared
  state survives between scenarios (see the `Gate` comment above; determinism AC).
- `run_bridge` is a **labelled verbatim reconstruction** of the production consumer, driven on a
  worker thread and returning a `BridgeRun` handle so the spike owns the agent `thread` object and
  the main thread can poke it mid-block (§10.3). Keep the copied line range in a comment header,
  and add "navigate by symbol, line numbers drift" to that header.
- The tool coroutine publishes `gate.loop = asyncio.get_running_loop()` and
  `gate.future = gate.loop.create_future()`, sets `gate.fired = True`, then `await gate.future`.
- The driver (main thread) resolves via `gate.loop.call_soon_threadsafe(gate.future.set_result, ...)`.

## ALGORITHM — inert paths (scenario_inert, #3)

```
gate = Gate()                                    # fresh per scenario
run = run_bridge(...); wait until gate.fired (tool is blocked in await)   # consumer on worker thread
set cancel_event  -> no effect (checked only BETWEEN astream_events iterations, agent.py:569-570;
                                no events flow while blocked)
run.close() -> assert it raises ValueError("generator already executing"): GeneratorExit is not
               merely inert, it is UNREQUESTABLE from another thread. CPython refuses gen.close()
               while the frame is executing, and the only thread that could close the generator is
               the worker thread itself — which is stuck inside next()/q.get(). So the :530
               GeneratorExit path (and its cancel.set()) is unreachable while blocked.
# Third generic path: the TUI _cancel_event (ui/app.py:290) is checked only AFTER an event
# arrives from the generator (set at :243). Model a minimal UI-consumer loop that polls the
# events list and would check a tui_cancel Event only on each new event:
set tui_cancel_event  -> the UI-consumer never wakes (no event arrived), so it is never checked
assert no new events in run.events and run.agent_thread.is_alive()  # all THREE generic paths inert
# "no new events arrived" IS the proof the TUI path cannot fire: it is gated on event arrival.
```

## ALGORITHM — direct resolve + join (scenario_direct, D2)

```
gate = Gate()                                    # fresh per scenario — never the inert one's
run = run_bridge(...); wait for gate.fired
gate.loop.call_soon_threadsafe(gate.future.set_result, "cancel")   # PUSH, not poll
tool returns -> fake model returns 'done' -> generator drains -> join(timeout=5); run.join()
assert run.agent_thread.is_alive() is False   # AC: thread actually terminates, not "join returned"
```

## ALGORITHM — post-resolution backstop (scenario_backstop, D2 part (c))

Proves the mirror image of `scenario_inert`: once the Future is resolved, events flow again,
so the generic paths that were inert while blocked become **live** and function as a backstop.

To make an event-boundary exist *after* the tool returns, this scenario passes its **own 3-entry
script** to the shared fake — `FakeChatModel(responses=[tool_call(blocking), tool_call(instant),
AIMessage("done")])` — so the 2nd invoke emits a **second tool_call** to an instant non-blocking
tool and `astream_events` iterates at least once more after the first tool result. Steps 3 and 5
keep the default 2-entry script; the scripts do not collide because each scenario constructs its
own model.

```
gate = Gate()                                    # fresh per scenario
run = run_bridge(...); wait for gate.fired
gate.loop.call_soon_threadsafe(gate.future.set_result, "resolve")   # unblock: events resume
wait until the first tool_result event has been observed (Future resolved, blocking over)
set cancel_event      # now checked BETWEEN astream_events iterations (agent.py:569-570; the
                      # astream_events call itself is at agent.py:564)
generator stops early via the generic path -> consumer drains -> join(timeout=5); run.join()
assert cancel was observed (stream ended before the final 'done' event)   # backstop DID fire
assert run.agent_thread.is_alive() is False   # backstop still terminates the thread
```

## DATA

- `Gate` is the cross-thread handoff (loop handle + future + fired flag), **one instance per
  scenario**, bound into the tool coroutine by `make_blocking_tool`.
- `run_bridge(gen_factory, inactivity_timeout=300.0, overall_cap=3600.0)` returns a `BridgeRun`
  handle (`.events: list[StreamEvent]`, `.agent_thread: threading.Thread`,
  `.error: BaseException | None`, `.close()`, `.join()`); the consumer runs on a worker thread.
- Prints `PASS: generic-paths-inert`, `PASS: direct-resolve-unblocks`,
  `PASS: thread-terminated`, `PASS: backstop-fires-after-resolve`; exits 0.

## Notes

- Windows: `asyncio.run` inside the bridge thread uses the default Proactor loop — fine for the
  in-process tool (no subprocess here; subprocess is Tier C).
- The fake's plain final message after the tool result comes from the `responses` script indexed by
  an invoke counter — the last entry is `AIMessage("done")`, so the agent halts deterministically.

## Definition of done

- `python spikes/i3-1-approval/tier_b_cancel.py` exits 0, all PASS lines, repeatable.
- Standard `src`/`tests` fast unit suite still green.
