# Implementation Task: Part D: Update `src/mcp_coder/workflows/create_pr/core.py` - change branches to readers

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

Current task from TASK_TRACKER.md: Part D: Update `src/mcp_coder/workflows/create_pr/core.py` - change branches to readers

Please implement this task step by step.

## LLM Response:
I have completed **Step 3, Part D**. 

## Summary

**Task completed:** Update `src/mcp_coder/workflows/create_pr/core.py` - change branches to readers

**Change made:**
- Changed import from:
  ```python
  from mcp_coder.utils.git_operations.branches import extract_issue_number_from_branch
  ```
- To:
  ```python
  from mcp_coder.utils.git_operations.readers import extract_issue_number_from_branch
  ```

The sub-task has been marked as complete `[x]` in the task tracker. The next sub-task in Step 3 is **Part E: Update `src/mcp_coder/cli/commands/set_status.py` - change branches to readers**.

---
Generated on: 2026-01-23T06:52:04.931008