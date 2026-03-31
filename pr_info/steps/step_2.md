# Step 2: Refactor implement workflow to use shared failure handling

## Context
See `pr_info/steps/summary.md` for full issue context. This step migrates the
implement workflow from its private failure handling functions to the shared module
created in Step 1.

## WHERE
- **Modify:** `src/mcp_coder/workflows/implement/constants.py`
- **Modify:** `src/mcp_coder/workflows/implement/core.py`

## WHAT

### `constants.py` changes:
- **Remove** the `WorkflowFailure` dataclass (replaced by shared `workflow_utils.failure_handling.WorkflowFailure`)
- **Keep** `FailureCategory` enum (implement-specific, maps to 3 different failure labels)
- **Keep** all other constants unchanged

### `core.py` changes:
- **Remove** `_get_diff_stat()` — now imported from `workflow_utils.failure_handling.get_diff_stat`
- **Remove** `_format_elapsed_time()` — now imported from `workflow_utils.failure_handling.format_elapsed_time`
- **Keep** `_format_failure_comment()` — implement-specific formatting (uses tasks_completed, tasks_total, build_url, diff_stat)
- **Replace** `_handle_workflow_failure()` — thin wrapper that:
  1. Builds implement-specific comment via `_format_failure_comment()`
  2. Calls shared `handle_workflow_failure()` with the formatted comment

### Updated `_handle_workflow_failure` signature (implement-specific wrapper):
```python
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_labels: bool = False,
    # implement-specific context for comment formatting:
    tasks_completed: int = 0,
    tasks_total: int = 0,
    build_url: str | None = None,
) -> None:
```

**Wait — simpler approach:** Keep the existing `_handle_workflow_failure` signature
but adapt its internals. The function already receives a `WorkflowFailure`. We just
need to:
1. Change it to call `get_diff_stat` and `format_elapsed_time` from the shared module
2. Call `handle_workflow_failure()` from shared module for label + comment posting
3. Keep `_format_failure_comment()` local for implement-specific comment body

### Actual minimal change to `_handle_workflow_failure`:
```python
def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_labels: bool = False,
) -> None:
    diff_stat = get_diff_stat(project_dir)        # shared import
    comment_body = _format_failure_comment(failure, diff_stat)  # local
    handle_workflow_failure(                        # shared import
        failure=SharedWorkflowFailure(
            category=failure.category.value,
            stage=failure.stage,
            message=failure.message,
            elapsed_time=failure.elapsed_time,
        ),
        comment_body=comment_body,
        project_dir=project_dir,
        from_label_id="implementing",
        update_labels=update_labels,
    )
```

### `_format_failure_comment` stays unchanged
It still receives the implement-local `WorkflowFailure` (which has `tasks_completed`,
`tasks_total`, `build_url`) and formats the implement-specific comment.

## HOW
- Add imports: `from mcp_coder.workflow_utils.failure_handling import (WorkflowFailure as SharedWorkflowFailure, handle_workflow_failure, get_diff_stat, format_elapsed_time)`
- The implement-local `WorkflowFailure` in constants.py is removed; a new local
  version is created as a dataclass with implement-specific fields + the shared fields
- OR simpler: keep the implement `WorkflowFailure` as-is in constants.py but rename to
  `ImplementWorkflowFailure` to avoid confusion

**Simplest approach:** Keep `WorkflowFailure` in `implement/constants.py` unchanged
(it has implement-specific fields). Import the shared one with an alias. The wrapper
function maps from implement's dataclass to the shared one for the handler call.

## ALGORITHM — refactored `_handle_workflow_failure`:
```
1. Get diff_stat via shared get_diff_stat()
2. Build comment via local _format_failure_comment(failure, diff_stat)
3. Create shared WorkflowFailure from implement's WorkflowFailure
4. Call shared handle_workflow_failure(shared_failure, comment, project_dir, "implementing", update_labels)
```

## DATA
- No new data structures
- Implement `WorkflowFailure` stays in constants.py (has category, stage, message, tasks_completed, tasks_total, build_url, elapsed_time)
- Shared `WorkflowFailure` only has (category: str, stage, message, elapsed_time)

## Verification
- All existing implement tests must pass (behavior unchanged)
- Run pylint, mypy, pytest

## Commit
One commit: "Refactor implement workflow to use shared failure handling utilities"
