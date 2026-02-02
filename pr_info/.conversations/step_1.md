# Implementation Task: Add `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with comment

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

Current task from TASK_TRACKER.md: Add `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with comment

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current state and find the task to implement.I can see the first unchecked task is in Step 1: "Add `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with comment". Let me read the step details file to understand exactly what needs to be done.Now I understand the task. I need to add the `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with its comment to `src/mcp_coder/workflow_utils/base_branch.py`. Let me first read the current file to see where to add it.Now I can see the file structure. I need to add the constant `MERGE_BASE_DISTANCE_THRESHOLD = 20` with the comment after the imports and before the `detect_base_branch` function. Let me add it:The constant has been added. Now let me verify the change by reading the file:The constant has been added correctly. Now I need to mark this sub-task as complete in the task tracker:I have completed the first sub-task. Let me write the commit message to the designated file:I have completed the sub-task. Here's a summary of what was done:

## Task Completed: Add `MERGE_BASE_DISTANCE_THRESHOLD = 20` constant with comment

**File modified:** `src/mcp_coder/workflow_utils/base_branch.py:23-27`

**Changes made:**
- Added the constant `MERGE_BASE_DISTANCE_THRESHOLD = 20` with a descriptive comment explaining:
  - It defines the maximum commits between merge-base and candidate branch HEAD
  - Higher values are more permissive but risk selecting wrong branches
  - Lower values may miss valid parents that have moved forward since branching

**Task tracker updated:** Marked the sub-task as `[x]` complete

**Commit message written to:** `pr_info/.commit_message.txt`

---
Generated on: 2026-02-02T14:29:26.033561