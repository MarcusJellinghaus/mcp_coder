# Step 5 — Provider plumbing: bridge param, pause, `CancelledError` catch, transient events

**Depends on:** Step 2 (the `ApprovalBridge` Protocol).

Threads the bridge down to where `q` lives, makes the consumer survive a human pause, stops a
cancel from printing a traceback onto a live Textual screen, and keeps `approval_request` out of
the two persistence sinks.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/types.py` | **modify** — `_TRANSIENT_EVENT_TYPES`, `ResponseAssembler.add`, StreamEvent docs |
| `src/mcp_coder/llm/interface.py` | **modify** — optional `approval_bridge` param |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | **modify** — `ask_langchain_stream`, `_ask_agent_stream` |
| `tests/llm/providers/langchain/test_approval_stream_bridge.py` | **create** |
| `tests/llm/test_types.py` *(or the existing assembler test module)* | **modify** |

## WHAT

```python
# llm/types.py
_TRANSIENT_EVENT_TYPES: frozenset[str] = frozenset({"raw_line", "approval_request"})
"""Event types that are neither persisted nor replayed (R5)."""
# ResponseAssembler.add: `if event_type != "raw_line"` -> `if event_type not in _TRANSIENT_EVENT_TYPES`

# llm/interface.py
def prompt_llm_stream(..., approval_bridge: "ApprovalBridge | None" = None) -> Iterator[StreamEvent]

# llm/providers/langchain/__init__.py
def ask_langchain_stream(..., approval_bridge: ApprovalBridge | None = None) -> Iterator[StreamEvent]
def _ask_agent_stream(..., approval_bridge: ApprovalBridge | None = None) -> Iterator[StreamEvent]
```

## HOW

* **`llm/types.py`** — export `_TRANSIENT_EVENT_TYPES` (module-private by name but imported by
  `AppCore` in Step 7; add it to `__all__` only if the project's convention requires it). Extend
  the `StreamEvent` docstring with three entries: the new `approval_request` event, the existing
  **undocumented** `tool_call_id` (model's `call_N` id on `tool_result`, langgraph `run_id` on
  `tool_use_start`), and `tool_run_id` (Step 6 adds it; document it here in one pass).
* **`llm/interface.py`** — annotate the new parameter under `if TYPE_CHECKING:` with a string
  annotation so the module-level import of the langchain package is **not** made eager (the
  existing `ask_langchain_stream` import is deliberately function-local). Document it exactly like
  the neighbouring `tools` parameter: *"langchain provider only"*. Forward it only in the
  `provider == "langchain"` branch.
* **`ask_langchain_stream`** — forward to `_ask_agent_stream`; the `_ask_text_stream` branch
  ignores it entirely (**no-op**, R13: non-iCoder CLI callers pass nothing and must keep working).
* **`_ask_agent_stream`** — three edits:
  1. `approval_bridge.attach(q.put)` immediately after `q` is created, inside the existing
     `try`; `approval_bridge.detach()` in the existing `finally` (next to `thread.join`). That
     `finally` runs on normal completion **and** on `GeneratorExit`, which is the cancel path —
     one lifecycle site, per summary §2.10.
  2. Pause: on `queue.Empty`, `continue` while `approval_bridge.pending() > 0`, accumulating
     `paused += timeout`; compare the overall cap against `(time.monotonic() - start) - paused`.
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
start, paused = time.monotonic(), 0.0
while True:
    try:
        event = q.get(timeout=timeout)
    except queue.Empty as exc:
        if approval_bridge is not None and approval_bridge.pending() > 0:
            paused += timeout          # legitimate human pause -> re-wait
            continue
        cancel.set(); raise TimeoutError(...) from exc
    if event is None: break
    if (time.monotonic() - start) - paused > _AGENT_OVERALL_TIMEOUT:
        cancel.set(); raise TimeoutError(...)
    yield event
```

## DATA

* `approval_bridge.attach(q.put)` — `q` is `queue.Queue[StreamEvent | None]`, so `q.put`
  satisfies `Callable[[StreamEvent], None]` (contravariant parameter, extra params have defaults).
* `paused` is a float in seconds; the inactivity `timeout` is iCoder's **300s**
  (`ICODER_LLM_TIMEOUT_SECONDS`), not the 30s default — tests must monkeypatch both it and
  `_AGENT_OVERALL_TIMEOUT` to small values.
* Yielded events are unchanged; `approval_request` passes through the generator like any other.

## TESTS (write first)

Reuse `tests/llm/providers/langchain/approval_harness.py` from Step 1.

1. **Pause defeats both timeouts:** a tool that blocks for longer than *both* a small
   monkeypatched `timeout` and a small monkeypatched `_AGENT_OVERALL_TIMEOUT` still completes when
   a bridge reports `pending() > 0`.
2. **Negative control:** the same setup with `approval_bridge=None` raises `TimeoutError` — proves
   the pause is load-bearing, not vacuous.
3. **Attach/detach lifecycle:** `attach` is called with a callable that puts onto *this* turn's
   queue; `detach` is called on normal completion **and** on generator close (cancel path). Two
   consecutive turns never share a queue (the stale-`q` failure mode).
4. **`CancelledError` in `_run`:** `error_holder` stays empty, the sentinel is still put, the
   generator ends normally, and nothing is re-raised.
5. **No-op on the text branch:** `ask_langchain_stream` without `mcp_config` and with a bridge
   ignores it and never calls `attach`.
6. **`ResponseAssembler`:** an `approval_request` event is absent from
   `result()["raw_response"]["events"]`; `raw_line` exclusion still holds; all other event types
   still accumulate.

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check` — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.3, §2.7, §2.10) and `pr_info/steps/step_5.md`, then implement
> Step 5 only.
>
> Thread an optional `approval_bridge: ApprovalBridge | None = None` through
> `prompt_llm_stream` → `ask_langchain_stream` → `_ask_agent_stream` (a no-op on the
> `_ask_text_stream` branch). In `_ask_agent_stream`: `attach(q.put)` right after `q` is created
> and `detach()` in the existing `finally` next to `thread.join` — **one** lifecycle site; make the
> consumer treat `queue.Empty` as "re-wait" while `pending() > 0`, accumulating `paused`, and
> compare `_AGENT_OVERALL_TIMEOUT` against `elapsed − paused`; add `except asyncio.CancelledError`
> to `_run` that does not append to `error_holder` while the `finally` still puts the sentinel.
>
> In `llm/types.py`, add `_TRANSIENT_EVENT_TYPES = frozenset({"raw_line", "approval_request"})`,
> use it in `ResponseAssembler.add` in place of the `!= "raw_line"` literal, and document
> `approval_request`, `tool_call_id` and `tool_run_id` in the `StreamEvent` docstring. In
> `llm/interface.py` annotate the new parameter under `TYPE_CHECKING` so no eager langchain import
> is introduced, and document it as "langchain provider only" like the neighbouring `tools` param.
>
> Write the six test cases listed in the step first, reusing the Step 1 harness; monkeypatch both
> timeouts to small values. Carry the "pause not keepalives" and "CancelledError is a
> BaseException" rationale into code comments.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` and
> `run_lint_imports_check` all green, then one commit.
