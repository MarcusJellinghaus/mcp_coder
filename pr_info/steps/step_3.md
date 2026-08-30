# Step 3 — Real-path `CancelledError` probe (decision gate)

**Depends on:** nothing. **Must run before any engine code** (Steps 1–2 are behaviour-neutral
prep and can land in any order relative to this one).

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
  Steps 7/11 reuse this harness from the same directory;
* that directory's `conftest.py` has an **autouse `_tmp_home` fixture** redirecting `Path.home()`
  to `tmp_path`, which already satisfies **R12** (`run_agent_stream` writes session history to
  `~/.mcp_coder/sessions/langchain/` unconditionally) — no extra isolation code needed.

`approval_harness.py` is not named `test_*`, so pytest does not collect it.

## WHAT

```python
# tests/llm/providers/langchain/approval_harness.py

def make_fake_chat_model() -> Any:
    """Build a two-invoke fake model: one tool_call, then plain text 'done'.

    langchain is imported and `BaseChatModel` is subclassed *inside* this
    function — see HOW for why neither may happen at module scope.
    """
    pytest.importorskip("langchain_core")

    from langchain_core.language_models.chat_models import BaseChatModel

    class _FakeChatModel(BaseChatModel):  # type: ignore[misc]
        invoke_count: int = 0
        def bind_tools(self, tools: Any, **kw: Any) -> "_FakeChatModel": ...
        async def _agenerate(self, messages, stop=None, run_manager=None, **kw): ...
        def _generate(self, messages, stop=None, run_manager=None, **kw): ...
        @property
        def _llm_type(self) -> str: ...

    return _FakeChatModel()

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

* **Every `pytest.importorskip` and every langchain import goes *inside* a function, and
  `BaseChatModel` is subclassed inside one too.** Follow the working precedent at
  `tests/icoder/test_icoder_permission_wiring.py` — read it first — which does exactly this:
  `importorskip` calls, then function-local `from langchain_core… import …`, then
  `class _ScriptedModel(BaseChatModel):  # type: ignore[misc]`. Two CI jobs make the obvious
  module-scope version fail:
  * `isort --check --profile=black --float-to-top` **floats imports above module-level
    statements**, so a module-level `importorskip` would end up *below* the langchain import it
    was meant to guard, and would guard nothing. No module in this repo uses one.
  * the `mypy` job installs only `.[typecheck]`, so langchain is absent, `BaseChatModel` resolves
    to `Any`, and a module-scope subclass trips `disallow_subclassing_any` under `--strict`. The
    `# type: ignore[misc]` on the class line is what the precedent uses.

  The directory conftest injects `MagicMock` modules when langchain is genuinely absent, and this
  test needs the **real** packages — hence `importorskip` rather than a plain import. No
  credentials and no network are needed, so the test stays **unmarked** and runs in the fast suite.
* The fake model must implement the **async** `_agenerate` (FINDINGS gotcha 3):
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

* The fake model's `invoke_count` — `1` after a cancelled run (the model is never re-invoked),
  which is the discriminator for "the turn did not re-plan".
* The probe records what `_run`'s `except Exception` sees. **Expected: nothing** —
  `CancelledError` is a `BaseException`. Assert that the caught-exception list is empty and that
  the escaping exception is `asyncio.CancelledError`.
* `run_agent_stream` yields `done` unconditionally on the *backstop* path but **not** here: under
  hard cancel the yield is never reached (F15, as corrected in #1045's round-2 addendum). Do not
  assert on the presence/absence of `done`.

## GATE — read before proceeding

* **Probe passes** → continue to Step 4 as planned.
* **Probe fails** (langgraph absorbs or converts the `CancelledError`; CPython 3.11 marks a task
  CANCELLED when it ends with `CancelledError` while un-cancelled) → switch to the
  **pre-authorised fallback**, no new decision needed:
  resolve the Future with a `"cancelled"` outcome, return a deny-shaped `ToolMessage`, and rely on
  the `cancel_event` backstop to break the loop (demonstrated by
  `spikes/i3-1-approval/tier_b_cancel.py::scenario_backstop`). Record the switch at the top of
  `pr_info/steps/summary.md` and adjust Steps 4, 7 and 9 accordingly (R7's `_run` catch and R16's
  cancelled-flag gate become unnecessary; the `done` event then *is* yielded).

## CHECKS

`run_pylint_check`, `run_mypy_check`, `run_pytest_check` (fast selection) — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially §2.3 and §2.10) and `pr_info/steps/step_3.md`, then
> implement Step 3 only.
>
> Write the shared typed harness `tests/llm/providers/langchain/approval_harness.py` and the probe
> `tests/llm/providers/langchain/test_approval_cancel_path.py`. Prove that a `CancelledError`
> raised in a tool coroutine (via `loop.call_soon_threadsafe(future.cancel)` from another thread)
> escapes `ToolNode` / `astream_events` / the `_run` drainer intact, that the agent thread is dead
> after the existing 5s join (`thread.is_alive() is False`), and that the model was not re-invoked.
>
> Constraints: use MCP tools only; `mypy --strict` must pass (the spike code this is modelled on
> was never type-checked — rewrite, do not copy); implement the **async** `_agenerate`; use a
> no-argument blocking tool; leave the test unmarked. Do not touch any production file.
>
> Put **every** `pytest.importorskip("langgraph")` / `("langchain_core")`, every langchain import
> and the `BaseChatModel` subclass **inside a function**, following
> `tests/icoder/test_icoder_permission_wiring.py` (read it first) — including its
> `# type: ignore[misc]` on the class line. A module-level guard does not work here: CI's
> `isort --float-to-top` floats imports above module-level statements so the guard would land
> below the import, and the CI mypy job installs no langchain, so a module-scope
> `class X(BaseChatModel)` trips `disallow_subclassing_any` under `--strict`.
>
> Report the probe outcome explicitly. If it fails, stop and report — do not improvise; the
> fallback is specified in the step's GATE section.
>
> Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` all green, then one commit.

---

## Implementation note (written after the step landed)

Both files were written as specified: `approval_harness.py` holds `make_fake_chat_model`, `Gate`,
`make_blocking_tool` and `wait_for` (plus one extra guard, below); `test_approval_cancel_path.py`
holds `test_cancelled_error_escapes_the_agent_stream` and
`test_cancel_leaves_no_error_and_kills_the_thread`, driven by a local `_run_cancel_probe()` that
reproduces `_ask_agent_stream`'s thread + `asyncio.run` + `queue.Queue` + sentinel +
`join(timeout=5)` topology. Every `importorskip`, every langchain import and the `BaseChatModel`
subclass are inside functions, with `# type: ignore[misc]` on the class line. Both tests are
unmarked. No production file was touched.

### 1. `pytest.importorskip` alone does not guard this directory

HOW says "the directory conftest injects `MagicMock` modules when langchain is genuinely absent,
and this test needs the **real** packages — hence `importorskip` rather than a plain import". That
is only half a guard: `importorskip` resolves through `sys.modules`, so it finds the conftest's
`MagicMock` and does **not** skip. Observed directly — the first run of the probe failed with
`ModuleNotFoundError: No module named 'langchain_core.language_models'; 'langchain_core' is not a
package`, i.e. it ran against the mock.

The harness therefore exports one extra symbol beyond the four in WHAT:
`require_real_langchain(*packages)`, which calls `pytest.importorskip` and then skips if the
returned module `isinstance(..., unittest.mock.Mock)`. It is used by `make_fake_chat_model`,
`make_blocking_tool` and `_run_cancel_probe`. Checking a not-mocked submodule name instead
(`langgraph.prebuilt.chat_agent_executor`) would work too, but pins a langgraph internal.

### 2. GATE: the probe could **not** be executed in this environment — outcome unknown

**No langchain distribution is installed in the venv the checkers run**
(`langchain-core`, `langgraph`, `langchain-mcp-adapters`, `langchain-openai` all report
`PackageNotFoundError`; verified with `importlib.metadata.version`, which reads distribution
metadata and is therefore immune to the conftest's `sys.modules` mocks). Both probe tests
consequently **skip** here — cleanly, which is why the checks are green, but a green run is *not*
evidence for the gate.

So the decision gate is **still open**. The probe is written, typed and lint-clean; it has to be
run once on an environment with the real `langchain-core` + `langgraph` (the CI
`langchain-integration` job's install set, or a local `pip install -e .[langchain]`) before Step 4
starts. Steps 4/7/9 depend on the answer:

* **passes** → continue as planned;
* **fails** → take the pre-authorised fallback in GATE above (resolve with a `"cancelled"` outcome
  + deny-shaped `ToolMessage` + `cancel_event` backstop) and adjust Steps 4, 7 and 9.

### 3. Local environment caveats for the checks (both pre-existing, both unrelated)

1. The stale installed `mcp_workspace` of Steps 1–2 still breaks collection of every test; the
   pytest runs below used `PYTHONPATH` pointed at a current `mcp-workspace` checkout.
2. `tests/llm` under the fast selection has four failures that predate this step and touch nothing
   it changed: three `tests/llm/providers/copilot/test_copilot_integration.py` tests (real
   `copilot.CMD` subprocess, exit status 1) and
   `test_langchain_exceptions.py::test_connection_errors_contains_httpx_connect_error` (asserts on
   `httpx.ConnectError`, and `httpx` is mocked because it is not installed either). The full-repo
   fast selection exceeds the 300s tool timeout, so `tests/llm` was run as the affected subset.

`run_pylint_check` on the two new files, `run_mypy_check` (strict) and `run_lint_imports_check`
(21 contracts kept) are all clean.
