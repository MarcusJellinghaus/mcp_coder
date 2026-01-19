# Implementation Task: Implement `_cleanup_commit_message_file()` helper function

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

Current task from TASK_TRACKER.md: Implement `_cleanup_commit_message_file()` helper function

Please implement this task step by step.

## LLM Response:
I have completed the current sub-task. Here's a summary:

## Completed: Implement `_cleanup_commit_message_file()` helper function

**What was done:**
- Added the `_cleanup_commit_message_file()` helper function to `src/mcp_coder/workflows/implement/task_processing.py` (line 531-536)

**Implementation:**
```python
def _cleanup_commit_message_file(project_dir: Path) -> None:
    """Remove stale commit message file from previous failed runs."""
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
    if commit_msg_path.exists():
        commit_msg_path.unlink()
        logger.debug("Cleaned up stale commit message file")
```

**Key features:**
- Uses the `COMMIT_MESSAGE_FILE` constant (`pr_info/.commit_message.txt`)
- Safely checks if file exists before attempting deletion
- Uses `Path.unlink()` to remove the file
- Logs cleanup action at debug level

**Next sub-task in Step 2:** Call cleanup function at start of `process_single_task()`

---
Generated on: 2026-01-19T16:28:15.972560