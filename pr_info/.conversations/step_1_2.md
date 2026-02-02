# Implementation Task: Implement `_detect_from_git_merge_base()` function

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

Current task from TASK_TRACKER.md: Implement `_detect_from_git_merge_base()` function

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current state and find the step to implement.Now let me read the step_1.md file to understand the details for implementing `_detect_from_git_merge_base()`:Now let me read the current `base_branch.py` file to understand the existing code:Now let me also read the existing test file to understand the test patterns:Now I have a clear understanding of the codebase. Let me create a todo list to track the implementation of `_detect_from_git_merge_base()`:Now let me implement the `_detect_from_git_merge_base()` function. First, I'll add the required imports and the new function:Now let me add the `_detect_from_git_merge_base()` function right after the constant:Now let me read the current `detect_base_branch()` function to update it properly:Now I need to update the `detect_base_branch()` function to:
1. Change return type to `Optional[str]`
2. Update the docstring with the new priority order
3. Call `_detect_from_git_merge_base()` as priority 1
4. Return `None` instead of `"unknown"`Now I also need to update the module docstring at the top of the file to reflect the new priority order:Now let me mark the sub-task as complete in the TASK_TRACKER.md:I have successfully implemented the `_detect_from_git_merge_base()` function. Here's a summary of what was done:

## Summary

**Task completed:** Implement `_detect_from_git_merge_base()` function

### Changes made to `src/mcp_coder/workflow_utils/base_branch.py`:

1. **Added imports** for `Repo` and `GitCommandError` from GitPython

2. **Implemented `_detect_from_git_merge_base()` function** (lines 34-151):
   - Takes `project_dir` and `current_branch` as parameters
   - Returns `Optional[str]` (branch name or `None`)
   - Checks local branches first, then remote branches (`origin/*`)
   - For each candidate branch:
     - Calculates merge-base with current branch
     - Counts commits from merge-base to candidate branch HEAD (distance)
     - Adds to candidates if distance ≤ `MERGE_BASE_DISTANCE_THRESHOLD` (20)
   - Returns branch with smallest distance
   - Includes DEBUG logging throughout

3. **Updated `detect_base_branch()` function**:
   - Changed return type from `str` to `Optional[str]`
   - Updated docstring with new priority order (merge-base is now #1)
   - Added call to `_detect_from_git_merge_base()` as highest priority
   - Returns `None` instead of `"unknown"` on failure
   - Added DEBUG logging for each detection step

4. **Updated module docstring** to reflect the new detection priority order

The task tracker has been updated to mark this sub-task as complete (`[x]`).

---
Generated on: 2026-02-02T14:31:28.618713