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

### Step 1: Add `FailureCategory` enum and `WorkflowFailure` dataclass
- [x] Implementation: tests in `test_constants.py` + production code in `constants.py` and `__init__.py` exports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Return `"timeout"` from `process_single_task()` on `TimeoutExpired`
- [x] Implementation: test in `test_task_processing.py` + catch `TimeoutExpired` in `task_processing.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Remove `update_labels` parameter from CLI and workflow
- [ ] Implementation: remove from `parsers.py`, `commands/implement.py`, `core.py` + update tests in `test_implement.py` and `test_core.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: Add `_handle_workflow_failure()` and wire into `run_implement_workflow()`
- [ ] Implementation: tests in `test_core.py` + add `_get_diff_stat()`, `_format_failure_comment()`, `_handle_workflow_failure()` to `core.py`, wire into all error exits, add unconditional success label transition, remove post-error progress display
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all acceptance criteria from step_4.md checklist
- [ ] PR summary prepared
