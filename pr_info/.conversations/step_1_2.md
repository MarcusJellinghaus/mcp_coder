# Implementation Task: Add `COMMIT_MESSAGE_FILE` constant to `src/mcp_coder/workflows/implement/task_processing.py`

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

Current task from TASK_TRACKER.md: Add `COMMIT_MESSAGE_FILE` constant to `src/mcp_coder/workflows/implement/task_processing.py`

Please implement this task step by step.

## LLM Response:
**Sub-task completed: Add `COMMIT_MESSAGE_FILE` constant to `src/mcp_coder/workflows/implement/task_processing.py`**

I added the constant `COMMIT_MESSAGE_FILE = "pr_info/.commit_message.txt"` to the constants section of `task_processing.py` at line 31, right after the existing `CONVERSATIONS_DIR` constant.

The task tracker has been updated to mark this sub-task as complete (`[x]`).

---
Generated on: 2026-01-19T16:26:22.515951