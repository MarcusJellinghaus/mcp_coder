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
- `src/mcp_coder/cli/commands/check_branch_status.py` — update `CI_PENDING` import to `CIStatus`, change comparison to `report.ci_status == CIStatus.PENDING`

## WHAT

### `CIStatus` enum

```python
class CIStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PENDING = "PENDING"
```

Replaces the `CI_PASSED`/`CI_FAILED`/`CI_NOT_CONFIGURED`/`CI_PENDING` string constants.

Remove old `CI_*` constants and replace all references with `CIStatus.*` members. Since `CIStatus(str, Enum)` compares equal to the string values, no behavioral change occurs.

### `BranchStatusReport` changes

```python
@dataclass(frozen=True)
class BranchStatusReport:
    # ... existing fields ...
    tasks_status: TaskTrackerStatus   # was: tasks_complete: bool
    tasks_reason: str                 # NEW (follows rebase_reason pattern)
    tasks_is_blocking: bool           # NEW — whether task status blocks merging
    # ... rest unchanged ...
```

### `_collect_task_status()` new signature

```python
def _collect_task_status(project_dir: Path) -> tuple[TaskTrackerStatus, str, bool]:
```

The third element (`bool`) indicates whether the status blocks merging.

### Pseudocode for `_collect_task_status()`

```
pr_info_path = project_dir / "pr_info"
if not pr_info_path.exists():
    return (N_A, "no pr_info folder", False)

steps_path = pr_info_path / "steps"
has_steps_files = steps_path.is_dir() and any(f.is_file() for f in steps_path.iterdir())

try:
    total, completed = get_task_counts(str(pr_info_path))
except TaskTrackerFileNotFoundError:
    if has_steps_files:
        return (N_A, "implementation plan exists but no TASK_TRACKER.md", True)
    return (N_A, "no implementation plan", False)
except TaskTrackerSectionNotFoundError:
    return (N_A, "TASK_TRACKER.md has no Tasks section", has_steps_files)
except Exception as e:
    return (ERROR, f"could not read task tracker: {e}", True)

if total == 0:
    return (N_A, "task tracker is empty", has_steps_files)
if completed == total:
    return (COMPLETE, f"all {total} tasks complete", False)
return (INCOMPLETE, f"{completed} of {total} tasks complete", True)
```

Blocking logic: N/A is blocking when `has_steps_files` is True. INCOMPLETE and ERROR are always blocking. COMPLETE is never blocking.

### `collect_branch_status()` wiring

```python
tasks_status, tasks_reason, tasks_is_blocking = _collect_task_status(project_dir)

report_data = {
    "ci_status": ci_status,
    "rebase_needed": rebase_needed,
    "tasks_status": tasks_status,       # was tasks_complete
    "tasks_reason": tasks_reason,       # new
    "tasks_is_blocking": tasks_is_blocking,  # new
    ...
}
```

### `create_empty_report()` update

```python
tasks_status=TaskTrackerStatus.N_A,
tasks_reason="Unknown",
tasks_is_blocking=False,
```

## HOW

- Import `TaskTrackerStatus`, `get_task_counts`, `TaskTrackerFileNotFoundError`, `TaskTrackerSectionNotFoundError` from `task_tracker`
- Remove import of `has_incomplete_work` (no longer needed in this file)
- `_collect_task_status` checks filesystem first, then calls `get_task_counts()`
- `_collect_task_status` returns `tasks_is_blocking` bool directly — no keyword-based detection needed
- The `tasks_reason` and `tasks_is_blocking` fields are added to `report_data` dict

## DATA

- `_collect_task_status()` returns `tuple[TaskTrackerStatus, str, bool]`
- `BranchStatusReport.tasks_status`: `TaskTrackerStatus` enum value
- `BranchStatusReport.tasks_reason`: human-readable string
- `BranchStatusReport.tasks_is_blocking`: whether this status blocks merging

## TESTS

### New tests in `tests/checks/test_branch_status.py`

1. **`test_collect_task_status_no_pr_info`** — no pr_info dir → `(N_A, "no pr_info folder")`
2. **`test_collect_task_status_no_steps_no_tracker`** — pr_info exists, no steps, no tracker → `(N_A, ...)`
3. **`test_collect_task_status_steps_exist_no_tracker`** — pr_info/steps/ has files, no TASK_TRACKER.md → `(N_A, ...)`
4. **`test_collect_task_status_empty_tasks`** — TASK_TRACKER.md with 0 tasks → `(N_A, "task tracker is empty")`
5. **`test_collect_task_status_all_complete`** — all done → `(COMPLETE, "all N tasks complete", False)`
6. **`test_collect_task_status_some_incomplete`** — partial → `(INCOMPLETE, "X of Y tasks complete", True)`
7. **`test_collect_task_status_read_error`** — unexpected exception → `(ERROR, ..., True)`
8. **`test_collect_task_status_section_not_found`** — missing section → `(N_A, ..., <depends on has_steps_files>)`
9. **`test_collect_task_status_tasks_is_blocking`** — verify `tasks_is_blocking` is correct in each scenario

### CIStatus enum value tests

10. **`test_ci_status_enum_values`** — verify `CIStatus.PASSED == "PASSED"`, `CIStatus.FAILED == "FAILED"`, etc. Confirms `str` mixin equality so migration is safe.
11. **`test_ci_status_replaces_constants`** — test expectations that previously referenced `CI_PASSED`, `CI_FAILED`, etc. now use `CIStatus.PASSED`, `CIStatus.FAILED`, etc.

### Updated existing tests

All test files that construct `BranchStatusReport` with `tasks_complete=True/False` must change to `tasks_status=TaskTrackerStatus.COMPLETE/INCOMPLETE/N_A` and add `tasks_reason="..."`. This is a mechanical find-and-replace across:

- `tests/checks/test_branch_status.py`
- `tests/checks/test_branch_status_pr_fields.py`
- `tests/cli/commands/test_check_branch_status.py`
- `tests/cli/commands/test_check_branch_status_auto_fixes.py`
- `tests/cli/commands/test_check_branch_status_pr_waiting.py`
- `tests/cli/commands/test_check_branch_status_ci_waiting.py`

**Pattern**: `tasks_complete=True` → `tasks_status=TaskTrackerStatus.COMPLETE, tasks_reason="all tasks complete", tasks_is_blocking=False` and `tasks_complete=False` → `tasks_status=TaskTrackerStatus.INCOMPLETE, tasks_reason="tasks incomplete", tasks_is_blocking=True`

Also update `CI_*` constant imports to `CIStatus.*` members in test files that import them directly (test_branch_status_pr_fields.py, test_check_branch_status_pr_waiting.py).

## NOTE on formatters

This step updates formatters minimally — just enough to not break. No icon mapping logic here (that belongs in step 3).

- `format_for_human`: use `tasks_status.value` as display text where `tasks_complete` was used
- `format_for_llm`: `Tasks={tasks_status.value}`
- `_generate_recommendations()`: `not tasks_complete` → `tasks_status == TaskTrackerStatus.INCOMPLETE` (no N/A/ERROR handling yet — that's step 3)
- `tasks_complete` in the 'Ready to merge' check maps to `tasks_status == TaskTrackerStatus.COMPLETE`. N/A won't show 'Ready to merge' in step 2 — step 3 fixes this by using `not tasks_is_blocking`.

## COMMIT

```
refactor(branch-status): replace tasks_complete bool with TaskTrackerStatus enum

Part of #676 — BranchStatusReport now uses tasks_status (enum) and
tasks_reason (str) instead of tasks_complete (bool). _collect_task_status
returns rich status covering all edge cases: no pr_info, no tracker,
empty tracker, complete, incomplete, and read errors.
```
