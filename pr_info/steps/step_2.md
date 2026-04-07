# Step 2: Change `process_single_task` return contract and add `attempt` parameter

**References:** [summary.md](summary.md), Issue #711

## Pre-flight

- Run a workspace search for `process_single_task(` to confirm `core.py` is the only caller; update any other call sites or test mocks that depend on the old `(True, "completed")` no-changes return.

## Overview

Modify `process_single_task` to: (a) accept an `attempt` parameter, (b) append a dynamic retry reminder when `attempt > 1`, and (c) return `(False, "no_changes")` instead of `(True, "completed")` when zero files change. Update existing tests in lock-step.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `tests/workflows/implement/test_task_processing.py`

## WHAT

### task_processing.py — signature change

```python
def process_single_task(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
    attempt: int = 1,  # NEW: 1-based attempt number
) -> tuple[bool, str]:
```

### task_processing.py — dynamic reminder (in the `full_prompt` f-string section)

```python
# After building full_prompt from template + task context:
RETRY_REMINDER = (
    "\n\n⚠️ Previous attempt produced NO file changes. "
    "If the task is already complete, you MUST tick the checkbox "
    "[ ] → [x] in pr_info/TASK_TRACKER.md — that file edit IS the deliverable. "
    "If the task genuinely needs code, do the work now."
)

if attempt > 1:
    full_prompt += RETRY_REMINDER
```

### task_processing.py — zero-changes return change

Replace:
```python
return True, "completed"  # Consider it successful but skip commit
```
With:
```python
return False, "no_changes"
```

### test_task_processing.py — update existing test

In `test_process_single_task_no_changes`, change assertions:
```python
assert success is False  # was True
assert reason == "no_changes"  # was "completed"
```

### test_task_processing.py — new tests

1. **`test_process_single_task_attempt_appends_reminder`** — When `attempt=2`, verify the prompt passed to `prompt_llm` contains the retry reminder text.
2. **`test_process_single_task_attempt_1_no_reminder`** — When `attempt=1` (default), verify the prompt does NOT contain the reminder text.

## HOW

- `attempt` defaults to `1` so all existing callers (core.py, tests) are unaffected without changes.
- The `RETRY_REMINDER` constant is defined at module level in `task_processing.py` for testability.
- The return value change from `(True, "completed")` to `(False, "no_changes")` is the key contract break — this makes zero-changes a failure signal that the retry wrapper (Step 3) will act on.

## ALGORITHM

```
build full_prompt from template + task context
if attempt > 1:
    full_prompt += RETRY_REMINDER
call LLM with full_prompt
check git status for changes
if no changes:
    return (False, "no_changes")  # was (True, "completed")
# ... rest of existing flow unchanged
```

## DATA

- New return tuple: `(False, "no_changes")` when zero files changed
- All other return tuples unchanged: `(True, "completed")`, `(False, "error")`, `(False, "timeout")`, `(False, "no_tasks")`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2: Modify process_single_task to accept an attempt parameter, append dynamic retry reminder on attempt > 1, and return (False, "no_changes") on zero file changes. Update existing tests and add new ones.

Files to modify:
- src/mcp_coder/workflows/implement/task_processing.py
- tests/workflows/implement/test_task_processing.py

Follow the step file exactly. Run pylint, pytest, mypy after changes. Mark sub-tasks [x] in TASK_TRACKER.md.
```
