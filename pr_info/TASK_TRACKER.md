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

### Step 1: Exception summary helpers — `llm/error_summary.py` + `failure_handling.exception_summary`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: tests (`tests/llm/test_error_summary.py`, `tests/workflow_utils/test_failure_handling.py`) + `summarize_exception`, `comment_safe`, `exception_summary`
- [x] Quality checks: pylint, pytest, mypy, lint-imports, tach — fix all issues
- [x] Commit message prepared

### Step 2: `_fail(exc=)` and the three core.py catch sites
See [step_2.md](./steps/step_2.md)

- [x] Implementation: tests (`test_core_failure_detail.py`, extend `test_core.py`) + `_fail(exc=)` in `handoff.py` + `exc=exc` at reviewer, supervisor and fix-task catch sites
- [x] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
- [x] Commit message prepared

### Step 3: Details for the three "general" failures without an exception
See [step_3.md](./steps/step_3.md)

- [ ] Implementation: parametrized test in `test_core_failure_detail.py` + `details=` for empty report, unparseable verdict, no session id
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4: CI gate — log the exception and return a comment-ready detail
See [step_4.md](./steps/step_4.md)

- [ ] Implementation: tests (`test_steps.py`, `test_core_after_steps.py`, `test_core_failure_detail.py`) + `_after_steps` 3-tuple with logging + both core.py callers
- [ ] Quality checks: pylint, pytest, mypy, lint-imports — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review full branch diff against `main`, address findings
- [ ] PR summary prepared
