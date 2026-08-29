# Step 1 — Real-path `CancelledError` probe (decision gate)

**Depends on:** nothing. **Must run first.**

R7 adopts *hard cancel* (`Future.cancel()` → `CancelledError` unwinds the turn), but #1044 only
demonstrated that in **Tier A (pure asyncio)**. Every real-langgraph spike scenario resolved with
`set_result`. Before any engine code is written, prove that a `CancelledError` raised inside a tool
coroutine escapes `ToolNode` → `astream_events` → `_run` intact.

This is **not** throwaway work: it is the harness and the regression test that the
"cancel-while-pending … `thread.is_alive() is False`" acceptance criterion requires.

---

## WHERE

| Path | Action |
|---|---|
| `tests/llm/providers/langchain/approval_harness.py` | **create** — shared typed fixture module |
| `tests/llm/providers/langchain/test_approval_cancel_path.py` | **create** — the probe |

Both live under `tests/llm/providers/langchain/` on purpose:

* `test_module_independence` in `.importlinter` forbids `tests.icoder` ↔ `tests.llm` imports, and
  Steps 5/8 reuse this harness from the same directory;
* that directory's `conftest.py` has an **autouse `_tmp_home` fixture** redirecting `Path.home()`
  to `tmp_path`, which already satisfies **R12** (`run_agent_stream` writes session history to
  `~/.mcp_coder/sessions/langchain/` unconditionally) — no extra isolation code needed.

`approval_harness.py` is not named `test_*`, so pytest does not collect it.

## WHAT

```python
# tests/llm/providers/langchain/approval_harness.py

class FakeChatModel(BaseChatModel):
    """Two-invoke fake: first emits one tool_call, then plain text 'done'."""
    invoke_count: int
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult: ...
    @property
    def _llm_type(self) -> str: ...

@dataclass
class Gate:
    """Captures the agent loop + the Future a blocking tool awaits."""
    loop: asyncio.AbstractEventLoop | None = None
    future: asyncio.Future[str] | None = None
    fired: bool = False

def make_blocking_tool(gate: Gate, name: str = "ping") -> Any:
    """StructuredTool whose coroutine captures the loop and awaits gate.future."""

def wait_for(pred: Callable[[], bool], timeout: float = 5.0) -> bool:
    """Poll *pred* until true or *timeout*; returns whether it became true."""
```

```python
# tests/llm/providers/langchain/test_approval_cancel_path.py

def test_cancelled_error_escapes_the_agent_stream() -> None: ...
def test_cancel_leaves_no_error_and_kills_the_thread() -> None: ...
```

## HOW

* Module-level `pytest.importorskip("langgraph")` and `pytest.importorskip("langchain_core")` —
  the directory conftest injects `MagicMock` modules when langchain is genuinely absent, and this
  test needs the **real** packages. No credentials and no network are needed, so the test stays
  **unmarked** and runs in the fast suite.
* `FakeChatModel` must implement the **async** `_agenerate` (FINDINGS gotcha 3):
  `BaseChatModel`'s default delegates to `run_in_executor`, a thread with no running loop, where
  `asyncio.get_running_loop()` raises and the loop reference is destroyed.
* Tool args must satisfy the tool schema or `ToolNode` rejects the call **before** the coroutine
  runs (FINDINGS gotcha 2). The blocking tool takes **no** arguments and the fake emits `args={}`.
* Drive `run_agent_stream(...)` through a local copy of the `_ask_agent_stream` consumer shape
  (thread + `asyncio.run(_run())` + `queue.Queue` + sentinel), so the probe measures the real
  production topology.

## ALGORITHM

```
start agent thread: asyncio.run(_run())   # _run drains run_agent_stream into q
wait_for(gate.fired)                      # tool coroutine is parked on await gate.future
gate.loop.call_soon_threadsafe(gate.future.cancel)   # the direct cancel channel
consume q until the None sentinel
thread.join(timeout=5)
assert thread.is_alive() is False and no exception was recorded other than CancelledError
```

## DATA

* `FakeChatModel.invoke_count` — `1` after a cancelled run (the model is never re-invoked),
  which is the discriminator for "the turn did not re-plan".
* The probe records what `_run`'s `except Exception` sees. **Expected: nothing** —
  `CancelledError` is a `BaseException`. Assert that the caught-exception list is empty and that
  the escaping exception is `asyncio.CancelledError`.
* `run_agent_stream` yields `done` unconditionally on the *backstop* path but **not** here: under
  hard cancel the yield is never reached (F15, as corrected in #1045's round-2 addendum). Do not
  assert on the presence/absence of `done`.

## GATE — read before proceeding

* **Probe passes** → continue to Step 2 as planned.
* **Probe fails** (langgraph absorbs or converts the `CancelledError`; CPython 3.11 marks a task
  CANCELLED when it ends with `CancelledError` while un-cancelled) → switch to the
  **pre-authorised fallback**, no new decision needed:
  resolve the Future with a `"cancelled"` outcome, return a deny-shaped `ToolMessage`, and rely on
  the `cancel_event` backstop to break the loop (demonstrated by
  `spikes/i3-1-approval/tier_b_cancel.py::scenario_backstop`). Record the switch at the top of
  `pr_info/steps/summary.md` and adjust Steps 2, 5 and 8 accordingly (R7's `_run` catch and R16's
  cancelled-flag gate become unnecessary; the `done` event then *is* yielded).

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially §2.3 and §2.10) and `pr_info/steps/step_1.md`, then
> implement Step 1 only.
>
> Write the shared typed harness `tests/llm/providers/langchain/approval_harness.py` and the probe
> `tests/llm/providers/langchain/test_approval_cancel_path.py`. Prove that a `CancelledError`
> raised in a tool coroutine (via `loop.call_soon_threadsafe(future.cancel)` from another thread)
> escapes `ToolNode` / `astream_events` / the `_run` drainer intact, that the agent thread is dead
> after the existing 5s join (`thread.is_alive() is False`), and that the model was not re-invoked.
>
> Constraints: use MCP tools only; `mypy --strict` must pass (the spike code this is modelled on
> was never type-checked — rewrite, do not copy); implement the **async** `_agenerate`; use a
> no-argument blocking tool; guard the module with `pytest.importorskip` for the real
> `langgraph`/`langchain_core`; leave the test unmarked. Do not touch any production file.
>
> Report the probe outcome explicitly. If it fails, stop and report — do not improvise; the
> fallback is specified in the step's GATE section.
>
> Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` all green, then one commit.
