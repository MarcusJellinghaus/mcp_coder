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

### Step 1: Update `log_utils.py` — remove NOTICE monkey-patch, add threshold-only comment
> [Detail](./steps/step_1.md) — `src/mcp_coder/utils/log_utils.py`, `tests/utils/test_log_utils.py`

- [ ] Implementation: remove `_notice()` function and monkey-patch, add threshold comment, remove test
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 2: Revert CLI command files from NOTICE logging to INFO logging
> [Detail](./steps/step_2.md) — 7 CLI command files

- [ ] Implementation: revert `logger.log(NOTICE, ...)` → `logger.info(...)` and remove NOTICE imports in all 7 files
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Revert workflow and utility files from NOTICE logging to INFO logging
> [Detail](./steps/step_3.md) — 11 workflow/utility files

- [ ] Implementation: revert `logger.log(NOTICE, ...)` → `logger.info(...)` and remove NOTICE imports in all 11 files
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps complete, no regressions
- [ ] PR summary prepared
