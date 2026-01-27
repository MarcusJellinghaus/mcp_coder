# Implementation Task: Add status and cleanup functions to vscodeclaude.py

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

Current task from TASK_TRACKER.md: Add status and cleanup functions to vscodeclaude.py

Please implement this task step by step.

## LLM Response:
## Summary

I have completed **Step 8: Status Display & Cleanup** of the VSCodeClaude feature. Here's what was implemented:

### Files Modified:

1. **`src/mcp_coder/cli/commands/coordinator/vscodeclaude.py`** - Added status and cleanup functions:
   - `get_issue_current_status()` - Get current status label for an issue via GitHub API
   - `is_session_stale()` - Check if session's issue status has changed
   - `check_folder_dirty()` - Check if folder has uncommitted git changes using `git status --porcelain`
   - `get_next_action()` - Determine next action for a session (active/restart/delete/manual cleanup)
   - `display_status_table()` - Print formatted status table to stdout
   - `get_stale_sessions()` - Get list of stale sessions with dirty status
   - `delete_session_folder()` - Delete session folder and remove from store
   - `cleanup_stale_sessions()` - Clean up stale session folders with dry-run support

2. **`tests/cli/commands/coordinator/test_vscodeclaude.py`** - Added test classes:
   - `TestStatusDisplay` - Tests for status table and display functions
   - `TestCleanup` - Tests for cleanup functions

### Task Tracker Updated:
All sub-tasks for Step 8 are now marked complete:
- [x] Add status and cleanup functions to vscodeclaude.py
- [x] Add status and cleanup tests to test_vscodeclaude.py
- [x] Run pylint on Step 8 code and fix all issues
- [x] Run pytest on Step 8 tests and ensure all pass
- [x] Run mypy on Step 8 code and fix all type issues
- [x] Prepare git commit message for Step 8

### Commit Message:
Written to `pr_info/.commit_message.txt` with detailed description of all changes.

---
Generated on: 2026-01-27T11:34:37.604941