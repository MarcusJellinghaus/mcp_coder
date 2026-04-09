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

### Step 1: Move FINALISATION_PROMPT to prompts.md
- [x] Implementation: add prompt section to prompts.md, update `run_finalisation` to load via `get_prompt_with_substitutions`, delete constant
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Extract CI operations to ci_operations.py
- [x] Implementation: create `ci_operations.py` with 9 moved symbols, update `core.py` imports, update `test_ci_check.py` patch paths, fix `_poll_for_ci_completion` import in `test_core.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move CI test classes to test_ci_operations.py
- [x] Implementation: create `test_ci_operations.py` with `TestPollForCiCompletionHeartbeat`, update patch paths and caplog logger names, clean up `test_core.py` imports
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps completed, no regressions
- [ ] PR summary prepared
