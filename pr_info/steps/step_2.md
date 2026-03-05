# Step 2: Add `session_id` to `log_llm_response()` and Call `end_run()`

## Context
See [summary.md](summary.md) for the full design.
Step 1 must be complete before this step (it provides `end_run(session_id=...)` and
`has_session()`).

This step contains the **actual bug fix**: `log_llm_response()` now closes the MLflow
run immediately after logging metrics. The next `log_llm_request()` call will find no
open run, so `start_run()` no longer collides.

---

## WHERE

| Role | Path |
|------|------|
| Tests | `tests/llm/providers/claude/test_logging_utils.py` — add tests to `TestLogLLMResponse` |
| Implementation | `src/mcp_coder/llm/providers/claude/logging_utils.py` |

---

## WHAT

### Changed function signature

```python
def log_llm_response(
    method: str,
    duration_ms: int,
    session_id: str | None = None,    # NEW — optional, defaults to None
    cost_usd: float | None = None,
    usage: dict[str, Any] | None = None,
    num_turns: int | None = None,
) -> None:
```

### What changes inside the function

At the **end** of the existing MLflow block (after the existing metrics logging),
add one call:

```python
mlflow_logger.end_run("FINISHED", session_id=session_id)
```

Remove the comment that previously said:
```python
# Note: Run will be ended after full conversation is logged in prompt.py
```

That comment is now obsolete — the run IS ended here.

---

## HOW

### Integration points
- `session_id` is a new keyword-only compatible parameter with default `None`
- All existing call sites (`log_llm_response(method="cli", duration_ms=...)`) remain
  valid — they will call `end_run("FINISHED", session_id=None)`, which ends the run
  but skips the mapping (correct behaviour for existing callers until Step 3)
- `log_llm_error()` already calls `end_run("FAILED")` — no change needed there

---

## ALGORITHM

```
def log_llm_response(method, duration_ms, session_id=None, ...):
    [existing debug log lines — unchanged]
    if mlflow not available: return
    mlflow_logger = get_mlflow_logger()
    log metrics: duration_ms, cost_usd, num_turns  [unchanged]
    log usage metrics if provided              [unchanged]
    mlflow_logger.end_run("FINISHED", session_id=session_id)   # NEW — the fix
```

That's the entire change in this function. One new line; remove the stale comment.

---

## DATA

- `session_id` flows in from the caller (Step 3 wires this up from Claude's response)
- When `session_id` is a string: `end_run()` stores `{session_id: active_run_id}` in
  the LRU map before ending the run
- When `session_id` is `None`: `end_run()` closes the run but stores nothing

---

## TESTS — additions to `TestLogLLMResponse`

Write these tests **first**, then implement.

### Test 1 — `log_llm_response` with `session_id` calls `end_run` with that session_id
```
mock get_mlflow_logger
mock mlflow_logger = Mock()

log_llm_response(method="cli", duration_ms=1000, session_id="sid-1")

mlflow_logger.end_run.assert_called_once_with("FINISHED", session_id="sid-1")
```

### Test 2 — `log_llm_response` with `session_id=None` calls `end_run` without session
```
mock get_mlflow_logger
mock mlflow_logger = Mock()

log_llm_response(method="cli", duration_ms=1000, session_id=None)

mlflow_logger.end_run.assert_called_once_with("FINISHED", session_id=None)
# Mapping is intentionally skipped — verified by MLflowLogger tests in Step 1
```

### Test 3 — `log_llm_response` with default (omitted) `session_id` also calls `end_run`
```
# Verify backward-compatible: existing call sites still close the run
log_llm_response(method="cli", duration_ms=500)

mlflow_logger.end_run.assert_called_once_with("FINISHED", session_id=None)
```

### Test 4 — Existing tests still pass (regression guard)
```
# Re-run TestLogLLMResponse existing tests — all should pass unchanged.
# The only observable difference: end_run is now called (previously was not).
# Existing tests did not assert that end_run was NOT called, so no breakage.
```

---

## LLM Prompt

```
You are implementing Step 2 of GitHub issue #491 "Fix MLflow 'already active run' warning".

Read pr_info/steps/summary.md for full context and design.
Step 1 (MLflowLogger changes) must already be complete.

Your task: modify `src/mcp_coder/llm/providers/claude/logging_utils.py` and add
new tests to `tests/llm/providers/claude/test_logging_utils.py`.

Follow TDD: write the 3 new tests in TestLogLLMResponse FIRST, then implement.

Changes to logging_utils.py — `log_llm_response()` only:
1. Add `session_id: str | None = None` as a new parameter after `duration_ms`.
2. At the end of the existing MLflow try-block (after all metrics are logged),
   add exactly one line:
       mlflow_logger.end_run("FINISHED", session_id=session_id)
3. Remove the stale comment "Note: Run will be ended after full conversation is
   logged in prompt.py" — it is now incorrect.

Do NOT change log_llm_request(), log_llm_error(), or any other function.
Do NOT change the function's debug log lines or metrics logging logic.

The new parameter has a default of None, so all existing call sites remain valid
without modification.

Run the tests after implementation:
    pytest tests/llm/providers/claude/test_logging_utils.py -v
```
