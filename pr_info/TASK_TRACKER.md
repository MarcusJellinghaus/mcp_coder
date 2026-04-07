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

### Step 1: Add FailureCategory enum value, label entry, retry constant, and static prompt change
See [step_1.md](./steps/step_1.md)
- [x] Implementation: enum value, constant, label entry, prompt rule, and test updates
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Change `process_single_task` return contract and add `attempt` parameter
See [step_2.md](./steps/step_2.md)
- [x] Implementation: signature change, dynamic retry reminder, zero-changes return change, and test updates
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Add `process_task_with_retry` wrapper function
See [step_3.md](./steps/step_3.md)
- [x] Implementation: retry wrapper function and TestProcessTaskWithRetry test class
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Wire `process_task_with_retry` into `core.py` and add failure routing
See [step_4.md](./steps/step_4.md)
- [x] Implementation: import change, call site change, reason routing, and test in test_core.py
- [x] Quality checks pass: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [ ] PR review: all steps complete, all checks green
- [ ] PR summary prepared
