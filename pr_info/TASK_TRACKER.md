# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Move parsing tests to `test_task_tracker_parsing.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: move `TestFindImplementationSection`, `TestParseTaskLines`, `TestNormalizeTaskName` via `move_symbol`; verify imports and counts (24 / 59)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move incomplete-task tests to `test_task_tracker_incomplete_tasks.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: move `TestGetIncompleteTasksInternal`, `TestGetIncompleteTasks`, `TestHasIncompleteWork`, `TestGetIncompleteTasksEdgeCases` via `move_symbol`; verify imports and counts (18 / 41)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move status tests to `test_task_tracker_status.py`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: move `TestGetStepProgress`, `TestIsTaskDone`, `TestGetTaskCounts` via `move_symbol`; delete empty banner; remove base file from `.large-files-allowlist`; verify counts (19 / 22)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Move validation tests to `test_task_tracker_validation.py`
See [step_4.md](./steps/step_4.md)

- [x] Implementation: move `TestValidateTaskTracker`, `TestTaskTrackerTemplate` via `move_symbol`; verify imports, counts (9 / 13) and final verification list
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against base branch
- [ ] PR summary prepared
