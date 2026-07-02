# Step 5 — Categorize timeout / MCP-unavailable at implement + mypy-fix

**Reference:** See [summary.md](./summary.md) (Decision 9). Apply the Step-4 helper at two of the
four autonomous sites and fix the pre-existing mypy-fix timeout hole. Depends on Steps 2 & 4.

## WHERE
- `src/mcp_coder/workflows/implement/task_processing.py` — `process_single_task` (LLM call) and
  `check_and_fix_mypy`.
- `src/mcp_coder/workflows/implement/core.py` — reason→category mapping in the task loop; wrap the
  final-mypy `check_and_fix_mypy` call (`core.py` ~line 690).
- Tests: `tests/workflows/implement/test_task_processing.py`, `test_core.py`.

## WHAT
- `process_single_task(...) -> tuple[bool, str]` — reason may now also be `"mcp_unavailable"`.
- `check_and_fix_mypy(...) -> bool` — **stops swallowing** `LLMTimeoutError` /
  `McpServersUnavailableError`; they propagate to callers.
- `core.py` task-loop: add an `mcp_unavailable` branch mirroring the existing `timeout` branch
  (→ `FailureCategory.MCP_UNAVAILABLE`). Wrap final-mypy call to categorize both exceptions.

## HOW
- In `process_single_task`, before the existing generic `except Exception` around the LLM call,
  add: `except (LLMTimeoutError, McpServersUnavailableError) as e: return False, llm_failure_reason(e)`
  (replaces/augments the current `except LLMTimeoutError → "timeout"`).
- `check_and_fix_mypy`: narrow its inner/outer `except Exception` so the two LLM exceptions are
  re-raised (`except (LLMTimeoutError, McpServersUnavailableError): raise` before the generic
  catch). Its step-7 call inside `process_single_task` is covered by that function's new handler;
  the final-mypy call in `core.py` gets its own `try/except → _handle_workflow_failure(...); return 1`.
- Map reason→category in `core.py` via `REASON_TO_CATEGORY` (or an explicit `if reason ==
  "mcp_unavailable"` block matching the `timeout` block).

## ALGORITHM
```
# core.py task loop (after process_task_with_retry)
if not success and reason in ("timeout", "mcp_unavailable"):
    _handle_workflow_failure(WorkflowFailure(category=REASON_TO_CATEGORY[reason], ...))
    return 1
# core.py final mypy
try:
    check_and_fix_mypy(...)
except (LLMTimeoutError, McpServersUnavailableError) as e:
    _handle_workflow_failure(WorkflowFailure(category=REASON_TO_CATEGORY[llm_failure_reason(e)], ...))
    return 1
```

## DATA
- `process_single_task` reason ∈ `{completed, no_tasks, no_changes, error, timeout, mcp_unavailable}`.
- `mcp_unavailable` → `FailureCategory.MCP_UNAVAILABLE` → `mcp_unavailable` label.

## TESTS (write first)
- `process_single_task`: an `McpServersUnavailableError` from `prompt_llm` → `(False,
  "mcp_unavailable")`; `LLMTimeoutError` → `(False, "timeout")`.
- `check_and_fix_mypy`: a timeout / MCP-unavailable during its LLM call now **propagates** (not
  swallowed to `False`) — fixes the pre-existing hole.
- `core.py`: reason `mcp_unavailable` → `MCP_UNAVAILABLE` failure handling; final-mypy timeout →
  `LLM_TIMEOUT`; MCP-unavailable → `MCP_UNAVAILABLE`.

## LLM PROMPT
> Implement Step 5 from `pr_info/steps/step_5.md` (see `pr_info/steps/summary.md`). Using
> `llm_failure_reason` / `REASON_TO_CATEGORY` from Step 4, categorize `LLMTimeoutError` and
> `McpServersUnavailableError` at the implement site (`process_single_task` returns
> `"timeout"`/`"mcp_unavailable"`) and the mypy-fix site (stop swallowing the two exceptions in
> `check_and_fix_mypy`; handle them at both its call sites — inside `process_single_task` and the
> final-mypy call in `core.py`). Add the `mcp_unavailable` reason→category branch in the `core.py`
> task loop mirroring `timeout`. Write tests first, including one proving the previously-swallowed
> mypy-fix timeout now reaches `llm_timeout`. pylint/pytest(`-n auto`)/mypy green, one commit.
