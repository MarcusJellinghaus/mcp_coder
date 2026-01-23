# Implementation Task: Implement `test_execute_set_status_dirty_directory_fails` test

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

Current task from TASK_TRACKER.md: Implement `test_execute_set_status_dirty_directory_fails` test

Please implement this task step by step.

## LLM Response:
I have completed the task. Here's a summary:

## Task Completed: Implement `test_execute_set_status_dirty_directory_fails` test

**What was done:**
- Added the `test_execute_set_status_dirty_directory_fails` test to `tests/cli/commands/test_set_status.py:378-413`

**Test details:**
- The test mocks `is_working_directory_clean` to return `False` (simulating a dirty working directory)
- Creates args with `status_label="status-05:plan-ready"`, `issue=123`, and `force=False`
- Calls `execute_set_status(args)`
- Asserts the function returns exit code `1`
- Asserts the error message contains "uncommitted changes"

**Note:** This is a TDD test - it tests behavior that will be implemented in Step 2. The test will initially fail when run because the `is_working_directory_clean` check and the `force` argument are not yet implemented in the `execute_set_status` function.

---
Generated on: 2026-01-23T07:16:36.151207