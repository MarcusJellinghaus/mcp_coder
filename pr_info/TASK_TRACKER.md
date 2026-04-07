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

### Step 1: Create `crash_logging.py` module with unit tests
- [x] Implementation: create `src/mcp_coder/utils/crash_logging.py` and `tests/utils/test_crash_logging.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add stderr faulthandler safety net to CLI entry point
- [x] Implementation: modify `src/mcp_coder/cli/main.py` and add test in `tests/cli/test_main.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Wire `enable_crash_logging` into long-running CLI commands
- [x] Implementation: modify `implement.py`, `create_plan.py`, `create_pr.py` and add wiring tests
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Add subprocess integration test for real crash capture
- [x] Implementation: add `test_crash_log_captures_real_segfault` to `tests/utils/test_crash_logging.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [ ] PR review completed
- [ ] PR summary prepared
