# Step 1 — Lazy named thread target in `_ask_agent_stream` (production)

> Read `pr_info/steps/summary.md` first. This step implements the **Stream (`_run`) leak —
> production hardening** described there.

## Goal

Eliminate the `_ask_agent_stream.<locals>._run` coroutine leak at its source by constructing
the coroutine lazily inside a named thread target, instead of eagerly as a `Thread`
argument. Production behaviour is otherwise unchanged.

## WHERE

- File: `src/mcp_coder/llm/providers/langchain/__init__.py`
- Function: `_ask_agent_stream` (thread creation, around line 503)
- Guard test (already exists, must keep passing):
  `tests/llm/providers/langchain/test_langchain_agent_timeout.py::TestAgentStreamInactivityTimeout::test_agent_stream_inactivity_timeout`

## WHAT

No signature changes. Introduce a nested named function and use it as the thread target.

```python
def _thread_main() -> None:
    asyncio.run(_run())

thread = threading.Thread(target=_thread_main, daemon=True)
```

## HOW (integration)

- Replace the single line
  `thread = threading.Thread(target=asyncio.run, args=(_run(),), daemon=True)`
  with the `_thread_main` definition followed by
  `thread = threading.Thread(target=_thread_main, daemon=True)`.
- Place `_thread_main` immediately after the existing `async def _run()` block and before
  `thread.start()`.
- Use a **named local function**, not a `lambda`, so it appears in tracebacks/profiles.
- No other lines change: `thread.start()`, the queue loop, timeout handling, and
  `thread.join(timeout=5)` in the `finally` all remain as-is.

## ALGORITHM (core logic)

```
# unchanged: async def _run() builds/consumes run_agent_stream, puts events on q
def _thread_main():          # runs inside the background thread
    asyncio.run(_run())      # _run() coroutine created here, so only when awaited
thread = threading.Thread(target=_thread_main, daemon=True)
thread.start()               # queue loop + timeout logic unchanged below
```

## DATA

- No changes to return values or data structures. `_ask_agent_stream` still yields
  `StreamEvent` dicts and raises `TimeoutError` on inactivity.

## TDD note

This is a leak fix that is not deterministically unit-testable (the warning is a GC-timing
artifact). No new test is added. The existing `test_agent_stream_inactivity_timeout` is the
guard: it patches `threading.Thread` to a no-op, and with the lazy target `_run()` is no
longer constructed, so the test passes with no leaked coroutine. Do **not** modify that test.

## LLM prompt

> Implement Step 1 as described in `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). In `src/mcp_coder/llm/providers/langchain/__init__.py`, inside
> `_ask_agent_stream`, replace
> `thread = threading.Thread(target=asyncio.run, args=(_run(),), daemon=True)` with a named
> nested function `_thread_main()` that calls `asyncio.run(_run())`, and create the thread
> with `target=_thread_main`. Change nothing else. Then run pylint, mypy, and the unit pytest
> subset (excluding integration markers, `-n auto`) and confirm all pass — in particular
> `test_langchain_agent_timeout.py`. Use MCP tools only. Commit as one commit.
