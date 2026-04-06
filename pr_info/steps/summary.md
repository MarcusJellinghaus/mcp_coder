# Issue #676: branch-status — empty task tracker reports COMPLETE instead of N/A

## Problem

`_collect_task_status()` in `branch_status.py` returns a `bool`. When no tasks exist (empty tracker, no pr_info folder, no TASK_TRACKER.md), `has_incomplete_work()` returns `False`, which gets inverted to `tasks_complete = True` — displaying "✅ COMPLETE" when nothing was actually completed.

## Design Changes

### New enum: `TaskTrackerStatus`

Added to `task_tracker.py`. Replaces the boolean with four explicit states:

- `COMPLETE` — all tasks marked done
- `INCOMPLETE` — some tasks remain
- `N_A` — no tasks to track (various sub-reasons)
- `ERROR` — could not read/parse tracker

### New function: `get_task_counts()`

Added to `task_tracker.py`. Returns `tuple[int, int]` (total, completed). Reuses existing `_read_task_tracker`, `_find_implementation_section`, `_parse_task_lines`. Lets exceptions propagate so callers can distinguish sub-reasons (file not found vs section not found).

### Updated dataclass: `BranchStatusReport`

- `tasks_complete: bool` → `tasks_status: TaskTrackerStatus`
- New field: `tasks_reason: str` (follows existing `rebase_reason` pattern)
- New field: `tasks_is_blocking: bool` — whether task status blocks merging

### Updated function: `_collect_task_status()`

Returns `tuple[TaskTrackerStatus, str, bool]` instead of `bool`. Maps each filesystem/parser scenario to the correct status+reason+is_blocking triple. Checks `pr_info/steps/` for files to determine whether N/A is a blocker.

### Updated formatters and recommendations

- Icons depend on status and blocker context (`➖` non-blocking N/A, `⚠️` blocking N/A/ERROR, `✅`/`❌`)
- Reason shown inline: `Task Tracker: ❌ INCOMPLETE (3 of 5 tasks complete)`
- `_generate_recommendations()` handles N/A blocker logic and ERROR state

### New enum: `CIStatus`

Added to `branch_status.py`. Replaces `CI_PASSED`/`CI_FAILED`/`CI_NOT_CONFIGURED`/`CI_PENDING` string constants with a `CIStatus(str, Enum)`.

### What is NOT changing

- `has_incomplete_work()` — kept as-is for backward compatibility; new code uses `get_task_counts()`

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | Add `TaskTrackerStatus` enum, `get_task_counts()` |
| `src/mcp_coder/workflow_utils/__init__.py` | Export new symbols |
| `src/mcp_coder/checks/branch_status.py` | Add `CIStatus` enum, update `BranchStatusReport`, `_collect_task_status()`, formatters, recommendations |
| `tests/workflow_utils/test_task_tracker.py` | Tests for `TaskTrackerStatus`, `get_task_counts()` |
| `tests/checks/test_branch_status.py` | Update all `tasks_complete` refs → `tasks_status`/`tasks_reason`, new scenario tests |
| `tests/checks/test_branch_status_pr_fields.py` | Update `tasks_complete` refs → `tasks_status`/`tasks_reason` |
| `tests/cli/commands/test_check_branch_status.py` | Update fixture `tasks_complete` refs |
| `tests/cli/commands/test_check_branch_status_auto_fixes.py` | Update fixture `tasks_complete` refs |
| `tests/cli/commands/test_check_branch_status_pr_waiting.py` | Update `_make_report` helper |
| `tests/cli/commands/test_check_branch_status_ci_waiting.py` | Update fixture `tasks_complete` refs |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Update `CI_PENDING` import to `CIStatus` |

## Implementation Steps

1. **Step 1**: Add `TaskTrackerStatus` enum and `get_task_counts()` to `task_tracker.py` (with tests)
2. **Step 2**: Update `BranchStatusReport` dataclass and `_collect_task_status()` in `branch_status.py`, add `CIStatus` enum, fix all tests referencing `tasks_complete`
3. **Step 3**: Update formatters (`format_for_human`, `format_for_llm`) and `_generate_recommendations()` with new N/A/ERROR logic (with tests)
