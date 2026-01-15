# Implementation Task: Run pylint check on test files

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Run pylint check on test files

Please implement this task step by step.

## LLM Response:
**Sub-task completed: Run pylint check on test files** ✓

Fixed the `import tomllib` issue (moved from inside function to top-level imports) and verified pylint passes with no errors/warnings.

---

**Summary of Step 2 progress:**
- [x] Run pylint check on test files - **COMPLETED** (fixed `import tomllib` placement)
- [ ] Run pytest for `tests/utils/test_data_files.py` with verbose output - *next task*
- [ ] Run pytest with `-n auto` to verify pytest-xdist parallel execution works
- [ ] Run mypy check on test files  
- [ ] Prepare git commit message for Step 2

---
Generated on: 2026-01-15T17:58:14.363639