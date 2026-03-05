# Summary: Fix MLflow 'Already Active Run' Warning (#491)

## Problem

When the implement workflow executes more than one LLM call, MLflow emits this warning
from the second call onward:

```
mcp_coder.llm.mlflow_logger - WARNING - Failed to start MLflow run:
Run with UUID ... is already active.
```

**Root cause**: `log_llm_request()` calls `mlflow_logger.start_run()` for every LLM
call. `log_llm_response()` never calls `end_run()`. The run stays open, and the next
`start_run()` collides with it.

---

## Solution

**Core fix**: `log_llm_response()` always calls `end_run()` immediately after logging
metrics. Each LLM call gets exactly one complete run (open → log metrics → close).

**Session continuity for `prompt.py`**: After `log_llm_response()` closes the run,
`_log_to_mlflow()` in `prompt.py` needs to add conversation artifacts (prompt.txt,
conversation.json) to the *same* run. This requires knowing the run ID. A small LRU
map (`session_id → run_id`) inside `MLflowLogger` provides this link.

---

## Architectural / Design Changes

### `MLflowLogger` — three additions, two extensions

| Change | Type | Purpose |
|--------|------|---------|
| `_session_run_map: OrderedDict[str, str]` | New instance var | LRU map, max 100 entries |
| `_MAX_SESSION_MAP_SIZE = 100` | New class const | LRU cap |
| `has_session(session_id: str) -> bool` | New method | Check if session is in map |
| `log_conversation_artifacts(prompt, response_data, metadata)` | New method | Log params + artifacts only (no metrics) |
| `start_run(session_id=None, ...)` | Extended | Resume existing run via `run_id` when `session_id` is in map |
| `end_run(status="FINISHED", session_id=None)` | Extended | Store `session_id → active_run_id` in LRU map before clearing it (only if `session_id` is not `None`) |

The LRU update is atomic inside `end_run()`: the mapping is stored **before**
`active_run_id` is set to `None`. This keeps all session-map state management
inside `MLflowLogger` — callers never touch `_session_run_map` directly.

### `logging_utils.py` — one-line change + new parameter

`log_llm_response()` gains an optional `session_id: str | None = None` parameter.
At the end of the function it calls:

```python
mlflow_logger.end_run("FINISHED", session_id=session_id)
```

This single call both ends the run and (conditionally) stores the session mapping.

### `claude_code_cli.py` / `claude_code_api.py` — thread `session_id` through

Both callers already parse the session_id from Claude's response. They now pass
it to `log_llm_response()`.

### `prompt.py` `_log_to_mlflow()` — conditional artifact/full logging

```
response_sid = response_data.get("session_id")
if response_sid is set AND has_session(response_sid):
    start_run(session_id=response_sid)   # resume closed run via run_id
    log_conversation_artifacts(...)      # params + artifacts; metrics already logged
    end_run("FINISHED")
else:
    start_run()                          # fresh run (edge case: no prior metrics)
    log_conversation(...)                # full: params + metrics + artifacts
    end_run("FINISHED")
```

---

## Run Lifecycle After Fix

### Multi-step implement workflow (each call is independent)

```
Call 1: start_run() → Run A (open)
         log_llm_response(session_id="sid-1") → store {"sid-1": "A"}, end_run()
         → Run A (closed, metrics logged)

Call 2: start_run() → Run B   ← no collision ✅
         log_llm_response(session_id="sid-2") → store {"sid-2": "B"}, end_run()
```

### Prompt command workflow (with artifact logging)

```
log_llm_request()  → start_run()                    → Run A (open)
log_llm_response(session_id="sid-1")               → store {"sid-1": "A"}, end_run()
                                                    → Run A (closed, metrics logged)

_log_to_mlflow()   → has_session("sid-1") = True
                   → start_run(session_id="sid-1")  → Run A (resumed)
                   → log_conversation_artifacts()    → params + artifacts added
                   → end_run("FINISHED")             → Run A (closed, complete)
```

---

## Files Modified / Created

| File | Action |
|------|--------|
| `src/mcp_coder/llm/mlflow_logger.py` | **Modified** — LRU map, `has_session()`, `log_conversation_artifacts()`, extend `start_run()` + `end_run()` |
| `src/mcp_coder/llm/providers/claude/logging_utils.py` | **Modified** — add `session_id` param to `log_llm_response()`, call `end_run()` |
| `src/mcp_coder/llm/providers/claude/claude_code_cli.py` | **Modified** — pass `session_id=parsed["session_id"]` to `log_llm_response()` |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | **Modified** — pass `session_id=actual_session_id` to `log_llm_response()` |
| `src/mcp_coder/cli/commands/prompt.py` | **Modified** — conditional `has_session()` path in `_log_to_mlflow()` |
| `tests/llm/test_mlflow_logger.py` | **Modified** — add `TestSessionMapBehavior` class (existing tests untouched) |
| `tests/llm/providers/claude/test_logging_utils.py` | **Modified** — add `session_id` tests to `TestLogLLMResponse` |
| `tests/llm/providers/claude/test_claude_code_cli.py` | **Modified** — add test verifying `session_id` is passed to `log_llm_response()` |
| `tests/llm/providers/claude/test_claude_code_api.py` | **Modified** — add test verifying `session_id` is passed to `log_llm_response()` |
| `tests/cli/commands/test_prompt.py` | **Modified** — add tests for conditional MLflow paths in `_log_to_mlflow()` |

No new files are created.

---

## Implementation Steps

| Step | Scope | TDD Focus |
|------|-------|-----------|
| [Step 1](step_1.md) | `MLflowLogger` — LRU map + new/extended methods | `TestSessionMapBehavior` in `test_mlflow_logger.py` |
| [Step 2](step_2.md) | `logging_utils.py` — `session_id` param + `end_run()` call | `TestLogLLMResponse` additions in `test_logging_utils.py` |
| [Step 3](step_3.md) | Callers — thread `session_id` through CLI and API | New tests in `test_claude_code_cli.py` + `test_claude_code_api.py` |
| [Step 4](step_4.md) | `prompt.py` — conditional `_log_to_mlflow()` | New tests in `test_prompt.py` |
