# Implementation Task: Update `run_create_plan_workflow()` to use new functions

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Update `run_create_plan_workflow()` to use new functions

Please implement this task step by step.

## LLM Response:
**Step 4 is now complete!** Here's a summary of what was accomplished:

## Summary

All sub-tasks in Step 4 have been completed:

1. **✅ Update `run_create_plan_workflow()` to use new functions**
   - Changed Step 3 from calling `verify_steps_directory()` to calling `check_pr_info_not_exists()` followed by `create_pr_info_structure()`
   - Updated log messages accordingly

2. **✅ Remove `verify_steps_directory()` function**
   - Deleted the entire function from `src/mcp_coder/workflows/create_plan.py`

3. **✅ Remove obsolete tests**
   - Updated all 10 tests in `tests/workflows/create_plan/test_main.py` to mock `check_pr_info_not_exists` and `create_pr_info_structure` instead of `verify_steps_directory`
   - Replaced `test_main_steps_directory_not_empty` with two new tests: `test_main_pr_info_exists` and `test_main_create_pr_info_structure_fails`
   - Removed the entire `TestVerifyStepsDirectory` class (12 tests) from `tests/workflows/create_plan/test_branch_management.py`
   - Removed the obsolete import of `verify_steps_directory`

4. **✅ Run quality checks and fix any issues**
   - Pylint: No issues found
   - Mypy: No type errors found

The commit message has been written to `pr_info/.commit_message.txt`.

---
Generated on: 2026-01-31T14:42:36.822967