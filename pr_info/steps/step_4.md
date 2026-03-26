# Step 4: Add Timeout and Cancellation Handling

**Commit message:** `feat(langchain): add timeout and cancellation to agent streaming`

**References:** [summary.md](summary.md) — "Timeout Strategy" section

## LLM Prompt

> Implement Step 4 from `pr_info/steps/step_4.md`.
> Read `pr_info/steps/summary.md` for full context (issue #603).
> Read the current code in `src/mcp_coder/llm/providers/langchain/__init__.py` (specifically
> `_ask_agent_stream()` added in Step 3) before making changes.
> Follow TDD: write tests first, then implement, then run all three checks.

## WHERE

- `tests/llm/providers/langchain/test_langchain_streaming.py` — add timeout/cancellation tests
- `src/mcp_coder/llm/providers/langchain/__init__.py` — add timeout logic to `_ask_agent_stream()`

## WHAT — Tests First

Add `TestAskLangchainStreamAgentTimeouts` class:

```python
class TestAskLangchainStreamAgentTimeouts:
    """Timeout and cancellation behavior for agent streaming."""

    def test_no_progress_timeout_raises(self) -> None:
        """If agent produces no events for NO_PROGRESS_TIMEOUT, TimeoutError raised."""
        # Mock run_agent_stream as async generator that blocks forever (asyncio.sleep)
        # Use short timeout override for test speed (e.g., 0.5s)
        # Verify TimeoutError raised

    def test_overall_timeout_raises(self) -> None:
        """If total time exceeds OVERALL_TIMEOUT, TimeoutError raised."""
        # Mock run_agent_stream to yield events slowly (one every 0.3s)
        # Use short overall timeout (e.g., 0.5s)
        # Verify TimeoutError raised after overall cap

    def test_generator_exit_sets_cancel(self) -> None:
        """When consumer stops iterating, cancel_event is set."""
        # Mock run_agent_stream to yield many events
        # Consume only first event, then break (triggers GeneratorExit)
        # Verify cancel_event was set (check thread behavior)
```

## WHAT — Implementation

Modify `_ask_agent_stream()` in `__init__.py`:

**Add module-level constants:**
```python
# Agent streaming timeout constants (seconds)
_AGENT_NO_PROGRESS_TIMEOUT = 600   # 10 minutes
_AGENT_OVERALL_TIMEOUT = 3600      # 60 minutes
```

**Replace the simple `q.get()` loop with timeout-aware version:**

## ALGORITHM

```python
# In _ask_agent_stream, replace the while loop:
start = time.monotonic()

try:
    while True:
        try:
            event = q.get(timeout=_AGENT_NO_PROGRESS_TIMEOUT)
        except queue.Empty:
            cancel.set()
            raise TimeoutError(
                f"Agent produced no output for {_AGENT_NO_PROGRESS_TIMEOUT}s"
            )
        if event is None:
            break
        if time.monotonic() - start > _AGENT_OVERALL_TIMEOUT:
            cancel.set()
            raise TimeoutError(
                f"Agent execution exceeded {_AGENT_OVERALL_TIMEOUT}s overall timeout"
            )
        yield event
except GeneratorExit:
    cancel.set()
finally:
    thread.join(timeout=5)
```

## DATA

- `_AGENT_NO_PROGRESS_TIMEOUT`: `int = 600` — 10 min no-event timeout
- `_AGENT_OVERALL_TIMEOUT`: `int = 3600` — 60 min hard cap
- Both raise `TimeoutError` with descriptive message

## HOW — Integration

- `import time` already present (or add if missing)
- `import queue` already added in Step 3
- Constants are module-level, easily overridable in tests via `patch`
- `cancel.set()` called before raising timeout — signals async thread to stop
- `thread.join(timeout=5)` in finally block — don't hang if thread is stuck

## Testing Notes

For fast tests, patch the timeout constants to small values:
```python
with patch(f"{_MOD_LC}._AGENT_NO_PROGRESS_TIMEOUT", 0.5):
    ...
```

The mock `run_agent_stream` should be an async generator:
```python
async def slow_agent_stream(**kwargs):
    await asyncio.sleep(10)  # blocks forever for no-progress test
    yield  # never reached
```

## Verification

Run all three checks after implementation:
1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with `extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`
