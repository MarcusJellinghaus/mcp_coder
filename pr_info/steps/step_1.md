# Step 1: Delete the dead `TaskTrackerStatus` enum

> **LLM prompt**
>
> Read `pr_info/steps/summary.md` first, then implement this step. This is a
> single atomic commit: a pure deletion of the unused `TaskTrackerStatus` enum
> across three files. All three edits must land together so the build never
> passes through a broken-import state. Do **not** touch the five
> `tests/cli/commands/test_check_branch_status*.py` files — their upstream import
> is correct. After editing, run pylint, pytest (fast unit subset), and mypy;
> all must pass. Use the exact commit message given at the bottom of this file.

## Why this is one commit (not TDD, not split)

There is no new behaviour to test-drive — the change is subtraction only. The
"test" involved is the *pinning* test being deleted. The three files form one
atomic unit: deleting the class while `__init__.py` still imports it would raise
`ImportError` and fail every test, so the edits cannot be committed separately.

## WHERE

1. `src/mcp_coder/workflow_utils/task_tracker.py`
2. `src/mcp_coder/workflow_utils/__init__.py`
3. `tests/workflow_utils/test_task_tracker.py`

## WHAT / HOW

### 1. `src/mcp_coder/workflow_utils/task_tracker.py`

- **Delete the `TaskTrackerStatus` class** (currently ~lines 73–79):

  ```python
  class TaskTrackerStatus(str, Enum):
      """Status of the task tracker."""

      COMPLETE = "COMPLETE"
      INCOMPLETE = "INCOMPLETE"
      N_A = "N/A"
      ERROR = "ERROR"
  ```

  Remove the class and its now-orphaned surrounding blank line so the file reads
  cleanly from `TaskInfo` to `TaskTrackerError`.

- **Delete the now-unused import** (line 10):

  ```python
  from enum import Enum
  ```

  `Enum` is used *only* by `TaskTrackerStatus` in this module (verified: the sole
  two `Enum` matches are this import and the class). Leaving it trips ruff F401.

### 2. `src/mcp_coder/workflow_utils/__init__.py`

- In the `from .task_tracker import ( ... )` block, **remove** the line:

  ```python
      TaskTrackerStatus,
  ```

- In `__all__`, **remove** the entry:

  ```python
      "TaskTrackerStatus",
  ```

### 3. `tests/workflow_utils/test_task_tracker.py`

- In the `from mcp_coder.workflow_utils.task_tracker import ( ... )` block (line
  14), **remove**:

  ```python
      TaskTrackerStatus,
  ```

  Otherwise the module fails at **collection**, not assertion.

- **Delete the `TestTaskTrackerStatusEnum` class and its section banner**
  (currently ~lines 1679–1699):

  ```python
  # ============================================================================
  # TaskTrackerStatus enum tests
  # ============================================================================


  class TestTaskTrackerStatusEnum:
      """Tests for the TaskTrackerStatus enum."""

      def test_task_tracker_status_enum_values(self) -> None:
          ...

      def test_task_tracker_status_is_str(self) -> None:
          ...
  ```

  Stop **before** the next section banner (`# get_task_counts() tests` /
  `class TestGetTaskCounts`) — that class stays. Leave a clean two-blank-line gap
  between the preceding class and the `get_task_counts()` banner.

## ALGORITHM

Not applicable — this step contains no logic, only deletions.

## DATA

No new data structures or return values. Net effect: `TaskTrackerStatus` no longer
exists in this repository, and `mcp_coder.workflow_utils.__all__` no longer lists
it.

## Verification (all must pass)

1. `mcp__tools-py__run_pylint_check`
2. `mcp__tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
3. `mcp__tools-py__run_mypy_check`
4. Search the repo for `TaskTrackerStatus`; the **only** remaining hits must be the
   five `tests/cli/commands/test_check_branch_status*.py` files importing it from
   `mcp_workspace.workflows.task_tracker`.

## Commit message

```
Remove dead local TaskTrackerStatus enum from workflow_utils

TaskTrackerStatus had zero production consumers; the only task-tracker
status in use (BranchStatusReport.tasks_status) is upstream-typed against
mcp_workspace.workflows.task_tracker.TaskTrackerStatus. The local copy was
a duplicate whose N_A value ("N/A") diverged from upstream ("N_A") -- a
latent trap under a shared-looking name.

This removes TaskTrackerStatus from the public
mcp_coder.workflow_utils.__all__ surface (a small, intentional API removal),
deletes the unused `from enum import Enum` import, and drops the pinning
test. No behavioural change. Refs #1104.
```
