# Implementation Task: Update `src/mcp_coder/workflows/vscodeclaude/cleanup.py` to use `safe_delete_folder()`

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

Current task from TASK_TRACKER.md: Update `src/mcp_coder/workflows/vscodeclaude/cleanup.py` to use `safe_delete_folder()`

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current state and find the task to implement.I can see I need to work on **Step 2**, and the first unchecked sub-task is:
- **Update `src/mcp_coder/workflows/vscodeclaude/cleanup.py` to use `safe_delete_folder()`**

Let me read the step details and the current cleanup.py file to understand what needs to be done.I can see:
1. The `safe_delete_folder` is already exported from `utils/__init__.py` (that sub-task is already marked as complete)
2. Now I need to update `cleanup.py` to use `safe_delete_folder()` instead of `shutil.rmtree()`

According to the step details, I need to:
1. Add import for `safe_delete_folder`
2. Remove `import shutil` (since it won't be needed)
3. Replace `shutil.rmtree(folder_path)` with `safe_delete_folder(folder_path)` and handle the return value

Let me update the cleanup.py file:Now I need to update the `delete_session_folder` function to use `safe_delete_folder()` instead of `shutil.rmtree()`:The changes are complete. Let me verify the updated file looks correct:The file has been updated correctly. Now let me mark this sub-task as complete in the task tracker:I've completed the sub-task. Here's a summary of what was done:

## Completed: Update `cleanup.py` to use `safe_delete_folder()`

**Changes made to `src/mcp_coder/workflows/vscodeclaude/cleanup.py`:**

1. **Removed import:** `import shutil` (no longer needed)

2. **Added import:** `from ...utils.folder_deletion import safe_delete_folder`

3. **Updated `delete_session_folder()` function:**
   - Changed docstring from "Uses shutil.rmtree for folder deletion" to "Uses safe_delete_folder for robust folder deletion"
   - Replaced `shutil.rmtree(folder_path)` with `safe_delete_folder(folder_path)`
   - Added proper handling for the boolean return value - if `safe_delete_folder()` returns `False`, the function logs an error and returns `False` immediately

The next unchecked sub-task in Step 2 is: **Add integration test to `tests/workflows/vscodeclaude/test_cleanup.py`**

---
Generated on: 2026-02-09T23:05:18.172601