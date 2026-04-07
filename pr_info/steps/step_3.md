# Step 3: Add `process_task_with_retry` wrapper function

**References:** [summary.md](summary.md), Issue #711

## Overview

Add the retry orchestration wrapper `process_task_with_retry()` in `task_processing.py`, next to `process_single_task`. This function calls `process_single_task` up to `MAX_NO_CHANGE_RETRIES` times, retrying only on `"no_changes"`. Tests first.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `tests/workflows/implement/test_task_processing.py`

## WHAT

### task_processing.py — new function

```python
def process_task_with_retry(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
) -> tuple[bool, str]:
    """Process a single task with bounded retry on zero-change results.

    Calls process_single_task up to MAX_NO_CHANGE_RETRIES times.
    Retries only on "no_changes" reason. Timeouts and errors propagate immediately.

    Returns:
        Tuple of (success, reason) where reason may be:
        - 'completed' | 'no_tasks' | 'error' | 'timeout' (from process_single_task)
        - 'no_changes_after_retries' (exhausted all retry attempts)
    """
```

### task_processing.py — import addition

```python
from .constants import (
    ...,
    MAX_NO_CHANGE_RETRIES,
)
```

### test_task_processing.py — new test class `TestProcessTaskWithRetry`

1. **`test_retry_succeeds_on_second_attempt`** — First call returns `(False, "no_changes")`, second returns `(True, "completed")`. Verify wrapper returns `(True, "completed")` and `process_single_task` was called twice with `attempt=1` then `attempt=2`.

2. **`test_retry_exhausted_returns_no_changes_after_retries`** — All 3 calls return `(False, "no_changes")`. Verify wrapper returns `(False, "no_changes_after_retries")`.

3. **`test_timeout_propagates_immediately`** — First call returns `(False, "timeout")`. Verify wrapper returns `(False, "timeout")` and `process_single_task` was called exactly once.

4. **`test_error_propagates_immediately`** — First call returns `(False, "error")`. Verify wrapper returns `(False, "error")` and `process_single_task` was called exactly once.

5. **`test_no_tasks_propagates_immediately`** — First call returns `(False, "no_tasks")`. Verify wrapper returns `(False, "no_tasks")`.

6. **`test_success_on_first_attempt_no_retry`** — First call returns `(True, "completed")`. Verify no retry happens.

7. **`test_timeout_on_second_attempt_propagates`** — First call `(False, "no_changes")`, second call `(False, "timeout")`. Verify returns `(False, "timeout")`, called twice total (timeout does not consume retry budget — it propagates).

## HOW

- The wrapper is placed right after `process_single_task` in `task_processing.py`.
- It imports `MAX_NO_CHANGE_RETRIES` from constants.
- Tests mock `process_single_task` via `patch` and verify call count + `attempt` argument.

## ALGORITHM

```python
for attempt in range(1, MAX_NO_CHANGE_RETRIES + 1):
    success, reason = process_single_task(..., attempt=attempt)
    if reason != "no_changes":
        return success, reason
    logger.warning(f"No changes on attempt {attempt}/{MAX_NO_CHANGE_RETRIES}")
return False, "no_changes_after_retries"
```

## DATA

- Input: same as `process_single_task` minus `attempt` (managed internally)
- Output: `tuple[bool, str]` — same contract as `process_single_task` plus new `"no_changes_after_retries"` reason
- Retry budget: `MAX_NO_CHANGE_RETRIES` (3) — only `"no_changes"` triggers retry

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3: Add process_task_with_retry wrapper function in task_processing.py with tests. Write tests first, then implementation.

Files to modify:
- tests/workflows/implement/test_task_processing.py (add TestProcessTaskWithRetry class)
- src/mcp_coder/workflows/implement/task_processing.py (add process_task_with_retry function, import MAX_NO_CHANGE_RETRIES)

Follow the step file exactly. Run pylint, pytest, mypy after changes. Mark sub-tasks [x] in TASK_TRACKER.md.
```
