# Step 2: Update `BranchStatusReport` and `_collect_task_status()`, fix all test references

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context. This step changes the `BranchStatusReport` dataclass from `tasks_complete: bool` to `tasks_status: TaskTrackerStatus` + `tasks_reason: str`, rewrites `_collect_task_status()`, and updates all tests that reference `tasks_complete`. Write tests first, then implement. Run all quality checks after.

## WHERE

- `src/mcp_coder/checks/branch_status.py` — update dataclass and `_collect_task_status()`
- `tests/checks/test_branch_status.py` — update existing tests, add new scenario tests
- `tests/checks/test_branch_status_pr_fields.py` — update `tasks_complete` → `tasks_status`/`tasks_reason`
- `tests/cli/commands/test_check_branch_status.py` — update fixture field names
- `tests/cli/commands/test_check_branch_status_auto_fixes.py` — update fixture field names
- `tests/cli/commands/test_check_branch_status_pr_waiting.py` — update `_make_report` helper

## WHAT

### `BranchStatusReport` changes

```python
@dataclass(frozen=True)
class BranchStatusReport:
    # ... existing fields ...
    tasks_status: TaskTrackerStatus   # was: tasks_complete: bool
    tasks_reason: str                 # NEW (follows rebase_reason pattern)
    # ... rest unchanged ...
```

### `_collect_task_status()` new signature

```python
def _collect_task_status(project_dir: Path) -> tuple[TaskTrackerStatus, str]:
```

### Pseudocode for `_collect_task_status()`

```
pr_info_path = project_dir / "pr_info"
if not pr_info_path.exists():
    return (N_A, "no pr_info folder")

steps_path = pr_info_path / "steps"
has_steps_files = steps_path.is_dir() and any(steps_path.iterdir())

try:
    total, completed = get_task_counts(str(pr_info_path))
except TaskTrackerFileNotFoundError:
    if has_steps_files:
        return (N_A, "implementation plan exists but no TASK_TRACKER.md")  # blocker
    return (N_A, "no implementation plan")  # non-blocker
except TaskTrackerSectionNotFoundError:
    return (N_A, "TASK_TRACKER.md has no Tasks section")  # blocker if has_steps_files
except Exception as e:
    return (ERROR, f"could not read task tracker: {e}")

if total == 0:
    return (N_A, "task tracker is empty")  # blocker if has_steps_files
if completed == total:
    return (COMPLETE, f"all {total} tasks complete")
return (INCOMPLETE, f"{completed} of {total} tasks complete")
```

### `collect_branch_status()` wiring

```python
tasks_status, tasks_reason = _collect_task_status(project_dir)

report_data = {
    "ci_status": ci_status,
    "rebase_needed": rebase_needed,
    "tasks_status": tasks_status,    # was tasks_complete
    "tasks_reason": tasks_reason,    # new
    ...
}
```

### `create_empty_report()` update

```python
tasks_status=TaskTrackerStatus.N_A,
tasks_reason="Unknown",
```

## HOW

- Import `TaskTrackerStatus`, `get_task_counts`, `TaskTrackerFileNotFoundError`, `TaskTrackerSectionNotFoundError` from `task_tracker`
- Remove import of `has_incomplete_work` (no longer needed in this file)
- `_collect_task_status` checks filesystem first, then calls `get_task_counts()`
- Store `has_steps_files` bool for N/A blocker logic (used in step 3 for recommendations)
- The `tasks_reason` field is added to `report_data` dict for use by `_generate_recommendations` (step 3)

## DATA

- `_collect_task_status()` returns `tuple[TaskTrackerStatus, str]`
- `BranchStatusReport.tasks_status`: `TaskTrackerStatus` enum value
- `BranchStatusReport.tasks_reason`: human-readable string

## TESTS

### New tests in `tests/checks/test_branch_status.py`

1. **`test_collect_task_status_no_pr_info`** — no pr_info dir → `(N_A, "no pr_info folder")`
2. **`test_collect_task_status_no_steps_no_tracker`** — pr_info exists, no steps, no tracker → `(N_A, ...)`
3. **`test_collect_task_status_steps_exist_no_tracker`** — pr_info/steps/ has files, no TASK_TRACKER.md → `(N_A, ...)`
4. **`test_collect_task_status_empty_tasks`** — TASK_TRACKER.md with 0 tasks → `(N_A, "task tracker is empty")`
5. **`test_collect_task_status_all_complete`** — all done → `(COMPLETE, "all N tasks complete")`
6. **`test_collect_task_status_some_incomplete`** — partial → `(INCOMPLETE, "X of Y tasks complete")`
7. **`test_collect_task_status_read_error`** — unexpected exception → `(ERROR, ...)`
8. **`test_collect_task_status_section_not_found`** — missing section → `(N_A, ...)`

### Updated existing tests

All test files that construct `BranchStatusReport` with `tasks_complete=True/False` must change to `tasks_status=TaskTrackerStatus.COMPLETE/INCOMPLETE/N_A` and add `tasks_reason="..."`. This is a mechanical find-and-replace across:

- `tests/checks/test_branch_status.py`
- `tests/checks/test_branch_status_pr_fields.py`
- `tests/cli/commands/test_check_branch_status.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`
- `tests/cli/commands/test_check_branch_status_pr_waiting.py`

**Pattern**: `tasks_complete=True` → `tasks_status=TaskTrackerStatus.COMPLETE, tasks_reason="all tasks complete"` and `tasks_complete=False` → `tasks_status=TaskTrackerStatus.INCOMPLETE, tasks_reason="tasks incomplete"`

## NOTE on formatters

This step updates `format_for_human()` and `format_for_llm()` minimally — just enough to not break (use `tasks_status.value` where `tasks_complete` was used as text). Full formatter logic with icons and inline reasons is in step 3.

Specifically, temporary formatter logic:
- `format_for_human`: `tasks_icon = "✅" if tasks_status == COMPLETE else "❌"`, display `tasks_status.value`
- `format_for_llm`: `Tasks={tasks_status.value}`

Similarly, `_generate_recommendations()` is updated minimally:
- `not tasks_complete` → `tasks_status == TaskTrackerStatus.INCOMPLETE`

Full N/A/ERROR recommendation logic is in step 3.

## COMMIT

```
refactor(branch-status): replace tasks_complete bool with TaskTrackerStatus enum

Part of #676 — BranchStatusReport now uses tasks_status (enum) and
tasks_reason (str) instead of tasks_complete (bool). _collect_task_status
returns rich status covering all edge cases: no pr_info, no tracker,
empty tracker, complete, incomplete, and read errors.
```
