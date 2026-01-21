# Implementation Task: Remove commented-out imports and move imports to top of `test_set_status.py`

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

Current task from TASK_TRACKER.md: Remove commented-out imports and move imports to top of `test_set_status.py`

Please implement this task step by step.

## LLM Response:
I have completed Step 5: Code Review Refactoring. Here's a summary of what was done:

## Step 5 Completed

All sub-tasks have been completed:

1. **Removed commented-out imports and moved imports to top of `test_set_status.py`** - Replaced the commented import block with actual imports at the file level, removed all per-method imports

2. **Simplified `full_labels_config` fixture** - Changed from a verbose inline dictionary (~80 lines) to using `load_labels_config(labels_config_path)` 

3. **Moved `_build_set_status_epilog()` from `main.py` to `set_status.py`** - Added the `build_set_status_epilog()` function to the set_status module

4. **Removed unused imports from `main.py`** - Removed `get_labels_config_path` and `load_labels_config` imports

5. **Updated `main.py` to import `build_set_status_epilog` from `set_status`** - Updated import statement and changed function call from `_build_set_status_epilog()` to `build_set_status_epilog()`

6. **Updated `/implementation_needs_rework.md` description** - Added workflow context with typical workflow steps

7. **Renamed `implementation_tasks.md` to `implementation_new_tasks.md`** - File renamed using move_file

8. **Code checks passed** - Pylint (pre-existing warnings unrelated to this change), mypy passes with no errors

9. **Commit message written** to `pr_info/.commit_message.txt`

---
Generated on: 2026-01-21T19:02:22.592691