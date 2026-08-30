# Step 7 — Provider plumbing: bridge param, pause, `CancelledError` catch, transient events

**Depends on:** Step 4 (the `ApprovalBridge` Protocol) and Step 1 (which frees the ~60 lines this
step adds to `llm/providers/langchain/__init__.py` under the 750-line CI gate).

Threads the bridge down to where `q` lives, makes the consumer survive a human pause, stops a
cancel from printing a traceback onto a live Textual screen, and keeps `approval_request` out of
the two persistence sinks.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/types.py` | **modify** — `TRANSIENT_EVENT_TYPES`, `ResponseAssembler.add`, StreamEvent docs |
| `src/mcp_coder/llm/interface.py` | **modify** — optional `approval_bridge` param |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | **modify** — `ask_langchain_stream`, `_ask_agent_stream` |
| `tests/llm/providers/langchain/test_approval_stream_bridge.py` | **create** |
| `tests/llm/test_types.py` *(or the existing assembler test module)* | **modify** |

## WHAT

```python
# llm/types.py
TRANSIENT_EVENT_TYPES: frozenset[str] = frozenset({"raw_line", "approval_request"})
"""Event types that are neither persisted nor replayed (R5)."""
# ResponseAssembler.add: `if event_type != "raw_line"` -> `if event_type not in TRANSIENT_EVENT_TYPES`

# llm/interface.py
def prompt_llm_stream(..., approval_bridge: "ApprovalBridge | None" = None) -> Iterator[StreamEvent]

# llm/providers/langchain/__init__.py
def ask_langchain_stream(..., approval_bridge: ApprovalBridge | None = None) -> Iterator[StreamEvent]
def _ask_agent_stream(..., approval_bridge: ApprovalBridge | None = None) -> Iterator[StreamEvent]
```

## HOW

* **`llm/types.py`** — add `TRANSIENT_EVENT_TYPES`, **public, no leading underscore**: `AppCore`
  imports it cross-module in Step 9, so an underscore name would advertise privacy the code does
  not honour. Add it to `__all__` if the module has one. Extend
  the `StreamEvent` docstring with three entries: the new `approval_request` event, the existing
  **undocumented** `tool_call_id` (model's `call_N` id on `tool_result`, langgraph `run_id` on
  `tool_use_start`), and `tool_run_id` (Step 8 adds it; document it here in one pass).
* **`llm/interface.py`** — annotate the new parameter under `if TYPE_CHECKING:` with a string
  annotation so the module-level import of the langchain package is **not** made eager (the
  existing `ask_langchain_stream` import is deliberately function-local). Document it exactly like
  the neighbouring `tools` parameter: *"langchain provider only"*. Forward it only in the
  `provider == "langchain"` branch.
* **`ask_langchain_stream`** — forward to `_ask_agent_stream`; the `_ask_text_stream` branch
  ignores it entirely (**no-op**, R13: non-iCoder CLI callers pass nothing and must keep working).
* **`_ask_agent_stream`** — three edits:
  1. Attach/detach, **inside one try/finally**. In `_ask_agent_stream`, `q` is created ~32 lines
     above the existing `try:` — navigate by symbol, not by line: Step 1 moves ~220 lines out of
     this file, so every line number in #1045's caveat block is stale by the time this step runs.
     "Right after `q` is created" and "inside the
     existing `try`" therefore cannot both hold. Resolve it by **widening the existing `try` upwards** so
     it starts immediately after `q` is created, then put `approval_bridge.attach(q.put)` as its
     first statement. Everything currently between (`error_holder`, `_run`, `_thread_main`,
     `thread.start()`) moves inside that `try` unchanged. This is what guarantees that a failure
     between attach and the consumer loop — `thread.start()` raising, for instance — still runs
     `detach()` instead of leaving the engine attached to a dead turn.
     In the `finally`, the order is **`approval_bridge.detach()` first, `thread.join(timeout=5)`
     second** — not merely "next to". `detach()` cancels every still-pending future
     (Step 4), which is the only thing that can unpark an interceptor blocked in
     `await fut`; joining first would instead burn the full 5s, expire with the agent thread
     still parked, and break test 5's `thread.is_alive() is False` assertion. Detach-before-join
     is a no-op on the normal-completion path (the registry is already empty) and is what makes
     the join meaningful on the `GeneratorExit`-while-pending path. That `finally` runs on normal
     completion **and** on `GeneratorExit`, which is the cancel path — one lifecycle site, per
     summary §2.10.
     **Guard both `finally` statements — the widening makes them conditional.** `thread` is now
     bound *inside* the `try`, so the `finally` must survive the two failure modes the widening
     exists to cover: `attach(q.put)` raising as the first statement leaves `thread` **unbound**
     (`UnboundLocalError` from the `finally`), and `thread.start()` raising leaves it **created
     but not started** (`RuntimeError: cannot join thread before it is started`). Either one would
     raise out of the `finally` and mask the original exception — the very failure the widening is
     justified by. So each cleanup step is conditioned on its own setup having succeeded:
     `detach()` only when `attach()` returned (a flag set immediately after the attach call, not
     `approval_bridge is not None` — attach may itself have raised), and `thread.join(timeout=5)`
     only when `thread` is bound **and** was started (`thread.ident is not None`, or an explicit
     `thread = None` pre-binding above the `try` plus a started flag). The `finally` must not be
     able to raise.
  2. Pause: a **timestamped pending window**. Sample `approval_bridge.pending()` at every loop
     point (after `q.get` returns *and* on `queue.Empty`); opening the window records
     `pause_began`, closing it credits the real wall time to `paused` **and bumps a
     `pause_epoch` counter**. On `queue.Empty` with the window open, `continue` instead of
     raising the inactivity timeout. The overall cap is
     compared against `elapsed − paused − (the currently open window)`. Do **not** accumulate
     `paused += timeout` in the `queue.Empty` branch only: with a 300s inactivity timeout every
     pause shorter than 300s would produce no `Empty` at all and would be charged in full against
     the 3600s cap.

     **The inactivity budget must be restarted, not merely suspended.** "Re-wait while
     `pending() > 0`" is not sufficient: `q.get(timeout=timeout)` starts a fresh 300s budget on
     every call, and a pause that *opens and closes inside one such wait* still consumes that
     budget. Concretely — the `approval_request` is dequeued at t=0, the user answers at t=250,
     the approved tool then runs quietly for 60s: at t=300 `q.get` raises `Empty` with
     `pending() == 0`, so the window-open check fails and the turn dies with
     `TimeoutError("no response for 300s. Connection closed.")` after only 50s of real
     inactivity. So: snapshot `pause_epoch` immediately **before** each `q.get`, and on
     `queue.Empty` re-wait when the window is open **or** when `pause_epoch` has advanced since
     that snapshot — i.e. any pause overlapping the current wait buys a full fresh `timeout`.
     Only a wait that contained no pause at all may raise the inactivity `TimeoutError`.
     A pause can never go unobserved: the registry entry is created *before* the emit
     (summary §2.2), so `pending()` is already `> 0` on the loop point that dequeues the
     `approval_request`, and the window is always opened there.
  3. `_run` gains `except asyncio.CancelledError:` **before** the `except Exception`, which does
     **not** append to `error_holder`; the `finally` still puts the sentinel.
* **Comments to carry (D9):** why pause and not keepalives — the overall cap is checked *inside*
  the consumer loop after `q.get()` returns, so keepalives **arm** it rather than reset it, and
  they would reach the session `.jsonl` and replay. Why `_run` catches `CancelledError` —
  it is a `BaseException`, so `agent.py`'s and `_run`'s `except Exception` both miss it and
  `_thread_main` is a bare `asyncio.run`, which would put a traceback on stderr, into a live
  Textual screen.

## ALGORITHM

```python
# _ask_agent_stream consumer loop
start, paused, pause_began, pause_epoch = time.monotonic(), 0.0, None, 0

def _sync_pause() -> None:
    """Open/close the pending window from the bridge's count (consumer thread)."""
    nonlocal paused, pause_began, pause_epoch
    waiting = approval_bridge is not None and approval_bridge.pending() > 0
    now = time.monotonic()
    if waiting and pause_began is None:
        pause_began = now                       # window opens
    elif not waiting and pause_began is not None:
        paused += now - pause_began             # window closes, real wall time credited
        pause_began = None
        pause_epoch += 1                        # ... and the inactivity budget is void

def _elapsed() -> float:
    now = time.monotonic()
    open_window = now - pause_began if pause_began is not None else 0.0
    return (now - start) - paused - open_window

while True:
    epoch_at_wait_start = pause_epoch           # snapshot BEFORE the wait
    try:
        event = q.get(timeout=timeout)
    except queue.Empty as exc:
        _sync_pause()
        # Re-wait on a still-open pause, and equally on one that opened and
        # closed inside this wait: `q.get` gives every call a fresh `timeout`,
        # so a pause overlapping the wait would otherwise eat the whole budget
        # and trip the inactivity error moments after the user approved.
        if pause_began is not None or pause_epoch != epoch_at_wait_start:
            continue
        cancel.set(); raise TimeoutError(...) from exc
    _sync_pause()                               # sampled BEFORE the yield blocks on the UI
    if event is None: break
    if _elapsed() > _AGENT_OVERALL_TIMEOUT:
        cancel.set(); raise TimeoutError(...)
    yield event
```

The window opens on the iteration that dequeues the `approval_request` itself — the registry
entry is created *before* the emit (summary §2.2), so `pending()` is already `> 0` there — and
closes on the first event (or `queue.Empty`) that follows the decision. It therefore covers the
whole human wait, including the part spent suspended at `yield` while the UI handles the event,
and works for pauses far shorter than `timeout`.

`pause_epoch` covers the other half: the window feeds the **overall cap**, the epoch protects the
**inactivity budget**. Closing a window voids the `q.get` wait it overlapped, so the consumer
re-waits with a fresh `timeout` instead of raising — which is the only thing standing between a
user who answers late in a wait and a spurious "Connection closed" on the next quiet stretch.

## DATA

* `approval_bridge.attach(q.put)` — `q` is `queue.Queue[StreamEvent | None]`, so `q.put`
  satisfies `Callable[[StreamEvent], None]` (contravariant parameter, extra params have defaults).
* `paused` and `pause_began` are floats in seconds (`pause_began` is `float | None`, `None` when
  no approval is pending); `pause_epoch` is an `int` bumped once per closed window and is only
  ever compared for inequality against a snapshot taken before `q.get`. The inactivity `timeout`
  is iCoder's **300s**
  (`ICODER_LLM_TIMEOUT_SECONDS`), not the 30s default, and `_AGENT_OVERALL_TIMEOUT` is **3600s** —
  tests must monkeypatch both to small values, and must cover a pause **shorter** than the
  inactivity timeout, where no `queue.Empty` ever occurs, **and** a pause that opens and closes
  inside a single `q.get` wait which is then followed by a quiet stretch.
* Yielded events are unchanged; `approval_request` passes through the generator like any other.

## TESTS (write first)

Reuse `tests/llm/providers/langchain/approval_harness.py` from Step 3.

1. **Pause defeats both timeouts:** a tool that blocks for longer than *both* a small
   monkeypatched `timeout` and a small monkeypatched `_AGENT_OVERALL_TIMEOUT` still completes when
   a bridge reports `pending() > 0`.
2. **Sub-inactivity pause is still excluded from the overall cap:** with `timeout` large enough
   that **no `queue.Empty` ever fires** and `_AGENT_OVERALL_TIMEOUT` smaller than the pause, a
   bridge reporting `pending() > 0` across the wait still completes. This is the case the
   `queue.Empty`-only accumulation got wrong; test 1 cannot detect it.
2b. **A pause that ends mid-wait does not consume the inactivity budget:** with a small
   monkeypatched `timeout` (and `_AGENT_OVERALL_TIMEOUT` large), the bridge reports
   `pending() > 0` for ~0.8 × `timeout`, then drops to `0`, and **no event follows for another
   ~0.8 × `timeout`** before the tool finally emits. The turn must complete: the `Empty` raised
   at the end of that first wait sees `pending() == 0` but an advanced `pause_epoch`, so the
   consumer re-waits with a fresh budget. Without the epoch this raises
   `TimeoutError("no response for …")` — the 250s-answer + 60s-tool scenario. Tests 1–3 cannot
   detect it: test 1 keeps `pending() > 0` for the whole wait, test 2 sets `timeout` so no
   `queue.Empty` ever fires, and test 3 has no pause at all.
3. **Negative control:** the same setup with `approval_bridge=None` raises `TimeoutError` — proves
   the pause is load-bearing, not vacuous.
4. **Attach/detach lifecycle:** `attach` is called with a callable that puts onto *this* turn's
   queue; `detach` is called on normal completion **and** on generator close (cancel path). Two
   consecutive turns never share a queue (the stale-`q` failure mode).
5. **Generator closed while an approval is pending:** close the consumer generator at the `yield`
   that delivered `approval_request` (the reachable `GeneratorExit`, summary §2.3). `detach()`
   runs, the pending future is cancelled, and the agent thread is dead after the 5s join
   (`thread.is_alive() is False`) — it does not survive parked on the future.
6. **`CancelledError` in `_run`:** `error_holder` stays empty, the sentinel is still put, the
   generator ends normally, and nothing is re-raised.
7. **No-op on the text branch:** `ask_langchain_stream` without `mcp_config` and with a bridge
   ignores it and never calls `attach`.
8. **`ResponseAssembler`:** an `approval_request` event is absent from
   `result()["raw_response"]["events"]`; `raw_line` exclusion still holds; all other event types
   still accumulate.

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check`, **and the
file-size gate** (`check_file_size(max_lines=750)` must not list
`llm/providers/langchain/__init__.py`) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.3, §2.7, §2.10) and `pr_info/steps/step_7.md`, then implement
> Step 7 only.
>
> Thread an optional `approval_bridge: ApprovalBridge | None = None` through
> `prompt_llm_stream` → `ask_langchain_stream` → `_ask_agent_stream` (a no-op on the
> `_ask_text_stream` branch). In `_ask_agent_stream`: widen the existing `try` so it starts
> right after `q` is created, make `attach(q.put)` its first statement, and in the `finally` call
> `detach()` **before** `thread.join(timeout=5)` (detach cancels the pending futures, which is the
> only thing that unparks a blocked interceptor; joining first burns the full 5s and leaves the
> agent thread alive) — **one** lifecycle site. Guard both `finally` statements, because the
> widening puts `thread` inside the `try`: call `detach()` only when `attach()` returned, and
> `thread.join(timeout=5)` only when the thread is bound and was started, so an `attach(q.put)`
> failure (`UnboundLocalError`) or a `thread.start()` failure (`RuntimeError: cannot join thread
> before it is started`) cannot raise out of the `finally` and mask the original exception. Make the
> consumer treat `queue.Empty` as "re-wait" while `pending() > 0` and track the pause as a
> **timestamped window** (sample `pending()` at every loop point, credit real wall time when the
> window closes, subtract the still-open window in the cap check) — do **not** accumulate
> `paused += timeout` in the `queue.Empty` branch only, or pauses shorter than the 300s inactivity
> timeout are charged in full against the 3600s cap. Also bump a `pause_epoch` counter whenever a
> window **closes**, snapshot it before each `q.get`, and re-wait on `queue.Empty` when the window
> is open **or** the epoch advanced during that wait: `q.get` restarts its full `timeout` on every
> call, so a pause that opens and closes inside one wait would otherwise eat the whole inactivity
> budget and kill the turn with "no response for 300s. Connection closed." moments after the user
> approved. Add `except asyncio.CancelledError`
> to `_run` that does not append to `error_holder` while the `finally` still puts the sentinel.
>
> In `llm/types.py`, add a **public** `TRANSIENT_EVENT_TYPES = frozenset({"raw_line",
> "approval_request"})` — `AppCore` imports it cross-module in Step 9, so it gets no leading
> underscore — use it in `ResponseAssembler.add` in place of the `!= "raw_line"` literal, and document
> `approval_request`, `tool_call_id` and `tool_run_id` in the `StreamEvent` docstring. In
> `llm/interface.py` annotate the new parameter under `TYPE_CHECKING` so no eager langchain import
> is introduced, and document it as "langchain provider only" like the neighbouring `tools` param.
>
> Write the nine test cases listed in the step first (1, 2, 2b, 3–8), reusing the Step 3 harness;
> monkeypatch both
> timeouts to small values, and include the sub-inactivity pause case (no `queue.Empty` at all),
> the pause-ends-mid-wait case (2b — pause, then a quiet stretch, both under one `timeout`) and
> the generator-closed-while-pending case. Carry the "pause not keepalives" and "CancelledError is
> a BaseException" rationale into code comments.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check`,
> `run_lint_imports_check` and `check_file_size(max_lines=750)` all green, then one commit.

---

## Implementation note (written after the step was implemented)

Implemented as specified. The `try` in `_ask_agent_stream` was widened upwards, `attach(q.put)` is
its first statement, both `finally` statements are guarded by their own setup flags (`attached`,
`thread is not None and thread_started`), `detach()` runs **before** `thread.join(timeout=5)`, the
pause is a timestamped window plus a `pause_epoch` counter, and `_run` gained
`except asyncio.CancelledError` ahead of its `except Exception`.

**One micro-deviation from "everything currently between moves inside that `try`".** `error_holder`
and `cancelled` stayed *above* the widened `try`; only `_run`, `_thread_main` and the
`thread = ...; thread.start()` pair moved inside it. Both are read *after* the `finally`
(`if error_holder and not cancelled:`), so binding them inside the `try` is a pylint
`used-before-assignment` hazard for zero benefit — neither is an assignment that can fail, so
neither can leave the engine attached to a dead turn, which is the property the widening exists
for.

**Two test assertions are stronger than the step's wording, because the obvious ones do not
discriminate.**

* Test 6 (`CancelledError` in `_run`) as written — "`error_holder` stays empty, the sentinel is
  still put, the generator ends normally" — passes *without* the new `except` clause: the
  `BaseException` escapes `_run`, but the `finally` still puts the sentinel and `error_holder` is
  still empty, so the consumer ends identically either way. The test therefore records
  `threading.excepthook` and asserts nothing escaped the agent thread. (Asserting on `stderr` via
  `capsys` does **not** work: pytest's `threadexception` plugin installs its own hook, so the
  traceback never reaches `sys.stderr` under pytest.)
* Test 4's "two consecutive turns never share a queue" compares the `__self__` of the two attached
  `q.put` bound methods, recorded by the fake bridge at `attach()` time.

**Every discriminating test was confirmed red first**, against a deliberately broken copy of the
production code: tests 1 and 2 fail with `Agent execution exceeded …s overall timeout` when
`_elapsed()` ignores `paused`/the open window; test 2b fails with
`no response for 1s. Connection closed.` when the `queue.Empty` branch drops the `pause_epoch`
half of its condition; test 5 fails with `agent thread still parked after join(5)` when the
`finally` joins before it detaches; test 6 fails with the recorded `CancelledError` when `_run`
catches something else. Tests 4 and 7 are lifecycle assertions with no interesting broken variant.

**The tests drive a scripted stand-in for `run_agent_stream`, not the real agent.** The step says
to reuse `approval_harness.py`; that harness needs a *real* langchain install, and this venv has
none (Step 3's probe still skips here — its decision gate is unchanged by this step). The pause,
the attach/detach ordering and the `CancelledError` catch are all properties of the consumer loop
in `_ask_agent_stream`, so the new module scripts the producer instead: it is deterministic, it
runs in the langchain-free CI job, and it made the red-first verification above possible. Test 5
reproduces the harness's parked-on-a-Future shape inline (a real `asyncio.Future` on a real agent
thread, cancelled from `detach()` through `call_soon_threadsafe` exactly as the engine does);
`test_approval_cancel_path.py` remains the place where the unwind is proven against real
langgraph. Every provider import still lives inside a function, per the directory's convention.

Timings are bounded below by the provider's `timeout: int` annotation, so the inactivity timeout
in these tests is 1s (a float would be a `mypy --strict` `arg-type` error) and the pauses are
0.7–1.6s; `_AGENT_OVERALL_TIMEOUT` is monkeypatched to sub-second floats. The whole module runs in
~10s.

`prompt_llm_stream`'s three `assert_called_once_with` blocks in `tests/llm/test_interface.py`
gained `approval_bridge=None` — the only existing tests the new parameter touched.

**Checks (all green):** `run_pylint_check`, `run_mypy_check`, `run_ruff_check` and
`run_format_code` on `src/mcp_coder/llm` + `tests/llm`; `run_lint_imports_check` (21 contracts
kept — the new `llm.interface -> llm.providers.langchain.approval_bridge` edge is `TYPE_CHECKING`
only, and `approval_bridge` still imports no langchain); `check_file_size(max_lines=750)` clean,
with `llm/providers/langchain/__init__.py` at ~570 lines after Step 1's extraction. Pytest:
`tests/llm/providers/langchain` + `test_types.py` + `test_interface.py`, and the four wiring
consumers `tests/icoder/test_llm_service.py`, `test_app_core.py`,
`test_icoder_permission_wiring.py`, `tests/cli/commands/test_prompt.py`.

**Pre-existing local failures, unrelated to this step and unchanged by it:**
`test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error` (no `httpx`
installed, so the conftest hands the test a `MagicMock`) and the three
`tests/llm/providers/copilot/test_copilot_integration.py` cases (the real `copilot` CLI exits 1
here). **Environment caveats unchanged from Steps 1–6:** the stale installed `mcp_workspace`
still needs `PYTHONPATH=…/mcp-workspace/src` on every pytest run; whole-repo runs still exceed the
tool's 300s timeout, so verification used the targeted runs listed above; `isort` still prints
`charmap` warnings for files this step did not touch.
