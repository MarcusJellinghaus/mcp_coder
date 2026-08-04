# Step 2 — Tier B (cancel): real bridge, three inert cancel paths, 5s join

**Commit:** `spike(i3.1): Tier B cancel — inert generic paths, direct resolve, thread death`

Read `pr_info/steps/summary.md` first. This step reconstructs the **real** thread+queue bridge
(a verbatim copy of `llm/providers/langchain/__init__.py:479-534`) driven by a fake model and a
tool that blocks on a cross-thread Future. It proves gotcha **#3** and **D2**: the three generic
cancel paths are unobservable while blocked, a direct engine-side resolve unblocks, and the agent
thread **actually terminates** after the real 5s join.

## WHERE

- Create `spikes/i3-1-approval/tier_b_cancel.py` (self-contained).

## WHAT — functions / signatures

```python
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

class FakeChatModel(BaseChatModel):
    """1st invoke -> AIMessage with one tool_call; 2nd invoke -> AIMessage('done')."""
    def _generate(self, messages, stop=None, run_manager=None, **kw): ...
    @property
    def _llm_type(self) -> str: return "fake"

# module-level handoff the driver thread uses to reach the agent loop:
class Gate:
    loop: asyncio.AbstractEventLoop | None = None
    future: asyncio.Future[str] | None = None
    fired: bool = False

async def blocking_tool(text: str) -> str:
    """Tool coroutine: capture agent loop via get_running_loop(), publish it, await Future."""

def run_bridge(gen_factory) -> tuple[list, threading.Thread]:
    """VERBATIM copy of __init__.py:479-534 thread+queue+join(5). Returns (events, thread)."""

def scenario_inert() -> None:    # generic paths do nothing while blocked
def scenario_direct() -> None:   # direct resolve unblocks; thread.is_alive() is False
def scenario_backstop() -> None: # after resolve, re-armed cancel_event DOES fire (backstop)
```

## HOW — integration points

- Build the agent generator with the **real** `run_agent_stream` from
  `mcp_coder.llm.providers.langchain.agent`, passing `chat_model=FakeChatModel()`,
  `tools=[StructuredTool.from_function(coroutine=blocking_tool, name="ping", ...)]`,
  `mcp_config_path=""`, a dummy `session_id`, and a real `threading.Event` as `cancel_event`.
- `run_bridge` is a **labelled verbatim reconstruction** of the production consumer so the spike
  owns the `thread` object (§10.3). Keep the copied line range in a comment header.
- `blocking_tool` publishes `Gate.loop = asyncio.get_running_loop()` and
  `Gate.future = Gate.loop.create_future()`, sets `Gate.fired = True`, then `await Gate.future`.
- The driver (main thread) resolves via `Gate.loop.call_soon_threadsafe(Gate.future.set_result, ...)`.

## ALGORITHM — inert paths (scenario_inert, #3)

```
start run_bridge in the normal way; wait until Gate.fired (tool is blocked in await)
set cancel_event  -> no effect (astream_events checks it only BETWEEN events; none flow)
gen.close()/GeneratorExit -> cancel.set() fires but tool still stuck; no event emitted
# Third generic path: the TUI _cancel_event (ui/app.py:290) is checked only AFTER an event
# arrives from the generator (set at :243). Model a minimal UI-consumer loop that polls the
# events list and would check a tui_cancel Event only on each new event:
set tui_cancel_event  -> the UI-consumer never wakes (no event arrived), so it is never checked
assert no new events arrived and the bridge thread is still alive  # all THREE generic paths inert
# "no new events arrived" IS the proof the TUI path cannot fire: it is gated on event arrival.
```

## ALGORITHM — direct resolve + join (scenario_direct, D2)

```
start bridge; wait for Gate.fired
Gate.loop.call_soon_threadsafe(Gate.future.set_result, "cancel")   # PUSH, not poll
tool returns -> fake model returns 'done' -> generator drains -> join(timeout=5)
assert thread.is_alive() is False        # AC: thread actually terminates, not "join returned"
```

## ALGORITHM — post-resolution backstop (scenario_backstop, D2 part (c))

Proves the mirror image of `scenario_inert`: once the Future is resolved, events flow again,
so the generic paths that were inert while blocked become **live** and function as a backstop.

To make an event-boundary exist *after* the tool returns, configure `FakeChatModel` to emit a
**second tool_call** to an instant non-blocking tool on its 2nd invoke (3rd invoke -> `'done'`),
so `astream_events` iterates at least once more after the first tool result.

```
start bridge; wait for Gate.fired
Gate.loop.call_soon_threadsafe(Gate.future.set_result, "resolve")   # unblock: events resume
wait until the first tool_result event has been observed (Future resolved, blocking over)
set cancel_event                          # now checked BETWEEN astream_events iterations (:572)
generator stops early via the generic path -> consumer drains -> join(timeout=5)
assert cancel was observed (stream ended before the final 'done' event)   # backstop DID fire
assert thread.is_alive() is False         # backstop still terminates the thread
```

## DATA

- `Gate` is the cross-thread handoff (loop handle + future + fired flag).
- `run_bridge` returns `(events: list[StreamEvent], thread: threading.Thread)`.
- Prints `PASS: generic-paths-inert`, `PASS: direct-resolve-unblocks`,
  `PASS: thread-terminated`, `PASS: backstop-fires-after-resolve`; exits 0.

## Notes

- Windows: `asyncio.run` inside the bridge thread uses the default Proactor loop — fine for the
  in-process tool (no subprocess here; subprocess is Tier C).
- If the fake model must return a plain final message after the tool result, gate it on a call
  counter so the second invocation yields `AIMessage("done")` and the agent halts deterministically.

## Definition of done

- `python spikes/i3-1-approval/tier_b_cancel.py` exits 0, all PASS lines, repeatable.
- Standard `src`/`tests` fast unit suite still green.
