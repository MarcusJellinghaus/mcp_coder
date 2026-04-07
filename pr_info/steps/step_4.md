# Step 4: Wire `process_task_with_retry` into `core.py` and add failure routing

**References:** [summary.md](summary.md), Issue #711

## Overview

Update `core.py` to call `process_task_with_retry` instead of `process_single_task`, and add the new `"no_changes_after_retries"` branch in the reason routing logic. Update `test_core.py` with a test for the new failure reason.

## WHERE

- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_core.py`

## WHAT

### core.py — import change

Replace:
```python
from .task_processing import process_single_task
```
With:
```python
from .task_processing import process_task_with_retry
```

(If `process_single_task` is still used elsewhere in core.py — e.g. in type hints or other functions — keep both imports. Check before removing.)

### core.py — call site change

In the task processing loop, replace:
```python
success, reason = process_single_task(
    project_dir, provider, mcp_config, execution_dir
)
```
With:
```python
success, reason = process_task_with_retry(
    project_dir, provider, mcp_config, execution_dir
)
```

### core.py — reason routing

Add a new branch in the existing reason switch (where `"timeout"`, `"error"`, etc. are handled):
```python
elif reason == "no_changes_after_retries":
    # ... create WorkflowFailure with FailureCategory.NO_CHANGES_AFTER_RETRIES
```

Follow the exact pattern of existing branches (e.g., `"timeout"` → `FailureCategory.LLM_TIMEOUT`).

### test_core.py — new test

Add a test that mocks `process_task_with_retry` to return `(False, "no_changes_after_retries")` and verifies the workflow produces a `WorkflowFailure` with `category=FailureCategory.NO_CHANGES_AFTER_RETRIES`. Follow the pattern of existing tests for `"timeout"` routing.

## HOW

- `core.py` already imports from `.task_processing` and `.constants` — just change the imported name and add the routing branch.
- The `FailureCategory.NO_CHANGES_AFTER_RETRIES` was added in Step 1.
- The `WorkflowFailure` dataclass is already used throughout core.py — follow the existing pattern exactly.

## ALGORITHM

```
# In task loop:
success, reason = process_task_with_retry(...)
if not success:
    if reason == "timeout":
        failure = WorkflowFailure(FailureCategory.LLM_TIMEOUT, ...)
    elif reason == "no_changes_after_retries":
        failure = WorkflowFailure(FailureCategory.NO_CHANGES_AFTER_RETRIES, ...)
    elif reason == "error":
        failure = WorkflowFailure(FailureCategory.GENERAL, ...)
    # ... handle failure
```

## DATA

- `"no_changes_after_retries"` reason → `FailureCategory.NO_CHANGES_AFTER_RETRIES` → label `"no_changes_after_retries"` in labels.json
- WorkflowFailure stage: **copy verbatim** from the existing `"timeout"` reason branch in `core.py` — it is `"Task implementation"` (note the capital T and the space). Do NOT invent a new stage string.
- WorkflowFailure message: a clear, descriptive string such as `"Task produced no file changes after N retry attempts"` (substitute the actual retry count from `MAX_NO_CHANGE_RETRIES`). Do not invent new field values; mirror the existing `"timeout"` branch's `WorkflowFailure(...)` construction shape exactly (same `tasks_completed` / `tasks_total` fields).

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4: Wire process_task_with_retry into core.py, add the "no_changes_after_retries" failure routing branch, and add a test in test_core.py.

Files to modify:
- src/mcp_coder/workflows/implement/core.py
- tests/workflows/implement/test_core.py

IMPORTANT: core.py is a large file. Read it carefully to find the exact import line and the task processing loop where process_single_task is called. Also find the reason routing switch to add the new branch. Follow existing patterns exactly.

Follow the step file exactly. Run pylint, pytest, mypy after changes. Mark sub-tasks [x] in TASK_TRACKER.md.
```
