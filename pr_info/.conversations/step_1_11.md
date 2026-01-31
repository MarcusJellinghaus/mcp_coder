# Implementation Task: Simplify `cleanup_repository()` to use new function

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

Current task from TASK_TRACKER.md: Simplify `cleanup_repository()` to use new function

Please implement this task step by step.

## LLM Response:
**Step 3 is now complete.** Here's a summary of what was accomplished:

## Summary

I completed **Step 3: Simplify create_pr/core.py Cleanup** with all sub-tasks:

### Changes Made:

1. **Simplified `cleanup_repository()`** (`src/mcp_coder/workflows/create_pr/core.py`):
   - Changed from calling 4 separate functions (`delete_steps_directory`, `truncate_task_tracker`, `clean_profiler_output`, `delete_conversations_directory`)
   - Now calls only 2 functions: `delete_pr_info_directory()` + `clean_profiler_output()`

2. **Removed obsolete functions** from `core.py`:
   - `delete_steps_directory()`
   - `delete_conversations_directory()`
   - `truncate_task_tracker()`

3. **Removed obsolete tests** from `tests/workflows/create_pr/test_file_operations.py`:
   - Removed `TestDeleteStepsDirectory` class
   - Removed `TestTruncateTaskTracker` class
   - Updated imports and docstring

4. **Fixed integration tests** in `tests/workflows/test_create_pr_integration.py`:
   - Updated `test_repository_cleanup_operations` to use `delete_pr_info_directory()`
   - Updated `test_workflow_handles_permission_errors` to use `delete_pr_info_directory()`
   - Fixed `test_workflow_handles_missing_files_gracefully` to expect `True` (no-op success)

5. **Quality checks**:
   - Pylint: Passed ✓
   - Mypy: Passed ✓

6. **Commit message** written to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T14:25:11.219428