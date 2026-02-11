# Implementation Task: Implement `_build_cached_issues_by_repo()` helper function

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

Current task from TASK_TRACKER.md: Implement `_build_cached_issues_by_repo()` helper function

Please implement this task step by step.

## LLM Response:
I'll implement the task step by step. Let me start by reading the task tracker to understand the current step.Now let me read the step 2 details to understand what needs to be implemented:Now let me read the current orchestrator file to understand the existing code structure:Now I can see the current state of the code. Let me check the current task - I need to implement the `_build_cached_issues_by_repo()` helper function. Let me create a todo list to track progress:Now let me implement the `_build_cached_issues_by_repo()` helper function. Based on the step_2.md file, I need to add this function before `restart_closed_sessions()`. Let me find a good location to insert it:Perfect! The `_build_cached_issues_by_repo()` helper function has been implemented. Now let me mark this sub-task as complete and update the task tracker:Now let me update the TASK_TRACKER.md to mark the sub-task as complete:Perfect! I have successfully implemented the `_build_cached_issues_by_repo()` helper function as specified in the task tracker. 

## Summary

I've completed the sub-task: **Implement `_build_cached_issues_by_repo()` helper function**

### What was implemented:

The helper function was added to `src/mcp_coder/workflows/vscodeclaude/orchestrator.py:821-866` with the following functionality:

1. **Groups sessions by repo**: Uses `defaultdict(list)` to organize session issue numbers by repository
2. **Fetches cached issues for each repo**: Calls `get_all_cached_issues()` with the `additional_issues` parameter containing all session issue numbers
3. **Converts to dict format**: Returns a dict mapping `repo_full_name -> {issue_number: IssueData}`
4. **Includes debug logging**: Logs the number of repos for which cache was built

The implementation follows the exact specifications from `pr_info/steps/step_2.md`, including:
- Proper type annotations
- Grouping sessions by repository to minimize API calls
- Using the `additional_issues` parameter to ensure closed session issues are included
- Converting the issue list to a dict for fast lookup
- Adding debug logging

The task has been marked as complete in `pr_info/TASK_TRACKER.md`.

---
Generated on: 2026-02-11T23:49:57.350896