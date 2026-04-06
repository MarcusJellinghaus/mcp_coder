# Step 1: Add `TaskTrackerStatus` enum and `get_task_counts()` to task_tracker.py

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context. This step adds the `TaskTrackerStatus` enum and `get_task_counts()` function to the task tracker module. Write tests first, then implement. Run all quality checks after.

## WHERE

- `src/mcp_coder/workflow_utils/task_tracker.py` — add enum and function
- `src/mcp_coder/workflow_utils/__init__.py` — export new symbols
- `tests/workflow_utils/test_task_tracker.py` — add tests

## WHAT

### `TaskTrackerStatus` enum

```python
class TaskTrackerStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    N_A = "N_A"
    ERROR = "ERROR"
```

Inherits from `str` so it serializes cleanly in formatted output.

### `get_task_counts()` function

```python
def get_task_counts(folder_path: str = "pr_info") -> tuple[int, int]:
    """Get total and completed task counts from TASK_TRACKER.md.

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md

    Returns:
        Tuple of (total_tasks, completed_tasks)

    Raises:
        TaskTrackerFileNotFoundError: If TASK_TRACKER.md doesn't exist
        TaskTrackerSectionNotFoundError: If Tasks section not found
    """
```

### Pseudocode

```
content = _read_task_tracker(folder_path)        # raises FileNotFoundError
section = _find_implementation_section(content)   # raises SectionNotFoundError
tasks = _parse_task_lines(section)
total = len(tasks)
completed = sum(1 for t in tasks if t.is_complete)
return (total, completed)
```

## HOW

- Import `Enum` from `enum` (already available in stdlib)
- `get_task_counts()` reuses existing private functions — no new parsing logic
- Exceptions propagate to caller (this is intentional — caller maps them to status)
- Export `TaskTrackerStatus` and `get_task_counts` from `__init__.py`

## DATA

- `TaskTrackerStatus`: 4-value string enum
- `get_task_counts()` returns `tuple[int, int]` — (total, completed)
- Raises `TaskTrackerFileNotFoundError` or `TaskTrackerSectionNotFoundError` on structural issues

## TESTS

Tests to add in `tests/workflow_utils/test_task_tracker.py`:

1. **`test_task_tracker_status_enum_values`** — verify all 4 enum values exist and are strings
2. **`test_get_task_counts_all_complete`** — tracker with all `[x]` → `(N, N)`
3. **`test_get_task_counts_some_incomplete`** — mixed → `(total, completed)` where completed < total
4. **`test_get_task_counts_empty_section`** — Tasks section with no checkboxes → `(0, 0)`
5. **`test_get_task_counts_file_not_found`** — raises `TaskTrackerFileNotFoundError`
6. **`test_get_task_counts_section_not_found`** — raises `TaskTrackerSectionNotFoundError`

## COMMIT

```
feat(task-tracker): add TaskTrackerStatus enum and get_task_counts()

Part of #676 — provides richer task status reporting. The enum
replaces boolean task status, and get_task_counts() exposes
total/completed counts for formatted output.
```
