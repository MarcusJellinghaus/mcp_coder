# Implementation Task: Part C: Update `src/mcp_coder/utils/github_operations/issue_manager.py` - change branches to readers

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

Current task from TASK_TRACKER.md: Part C: Update `src/mcp_coder/utils/github_operations/issue_manager.py` - change branches to readers

Please implement this task step by step.

## LLM Response:
I have completed **Part C** of Step 3.

## Summary

**Task Completed:** Part C: Update `src/mcp_coder/utils/github_operations/issue_manager.py` - change branches to readers

**Change Made:**
- Updated the import statement at line 13-16 from:
  ```python
  from mcp_coder.utils.git_operations.branches import (
      extract_issue_number_from_branch,
      get_current_branch_name,
  )
  ```
  to:
  ```python
  from mcp_coder.utils.git_operations.readers import (
      extract_issue_number_from_branch,
      get_current_branch_name,
  )
  ```

The task tracker has been updated to mark this sub-task as complete. The next sub-task in Step 3 is **Part D: Update `src/mcp_coder/workflows/create_pr/core.py` - change branches to readers**.

---
Generated on: 2026-01-23T06:51:25.778195