# Implementation Task: Call cleanup function at start of `process_single_task()`

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

Current task from TASK_TRACKER.md: Call cleanup function at start of `process_single_task()`

Please implement this task step by step.

## LLM Response:
I have completed the task:

## Summary

**Task Completed:** Call cleanup function at start of `process_single_task()`

**Change Made:** Added a call to `_cleanup_commit_message_file(project_dir)` at the very start of the `process_single_task()` function in `src/mcp_coder/workflows/implement/task_processing.py:560-561`.

This ensures that any stale commit message file from a previous failed run is cleaned up before starting a new task processing cycle, preventing old commit messages from being accidentally used.

**Updated Task Tracker:** Marked the sub-task as complete `[x]`.

---
Generated on: 2026-01-19T16:29:05.359470