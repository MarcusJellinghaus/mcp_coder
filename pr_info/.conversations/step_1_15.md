# Implementation Task: Update `tests/utils/jenkins_operations/test_integration.py` - 4 calls → 1 batch

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

Current task from TASK_TRACKER.md: Update `tests/utils/jenkins_operations/test_integration.py` - 4 calls → 1 batch

Please implement this task step by step.

## LLM Response:
I've completed **Step 4** of the task tracker. Here's a summary of what was done:

## Summary of Completed Tasks

### Sub-task: Update `tests/utils/jenkins_operations/test_integration.py` - 4 calls → 1 batch
- Changed the import from `get_config_value` to `get_config_values`
- Replaced 4 individual `get_config_value()` calls with a batch pattern:
  - Build `missing_keys` list based on which values need to be fetched
  - Call `get_config_values(missing_keys)` once if any keys are missing
  - Extract values from the result dictionary

### Sub-task: Verify no references to `get_config_value` remain
- Verified all Step 4 files have been migrated to `get_config_values`
- The only remaining references are in `tests/utils/test_user_config_integration.py` which will be updated in Step 5

### Sub-task: Run quality checks and fix issues
- Fixed **pylint** issue: Updated `coordinator/__init__.py` to export `get_config_values` instead of `get_config_value`
- Fixed **mypy** issues: Added type annotations for `config` variables in:
  - `src/mcp_coder/utils/jenkins_operations/client.py:77`
  - `tests/conftest.py:237`
  - `tests/utils/jenkins_operations/test_integration.py:69`

### Sub-task: Prepare git commit message for Step 4
- Added commit message to the task tracker

**Step 4 is now complete!** The next step (Step 5) will update the test files `test_user_config.py` and `test_user_config_integration.py`.

---
Generated on: 2026-01-15T15:34:36.553299