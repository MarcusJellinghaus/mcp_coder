# Implementation Task: Modify `restart_closed_sessions()` to call helper if cache not provided

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

Current task from TASK_TRACKER.md: Modify `restart_closed_sessions()` to call helper if cache not provided

Please implement this task step by step.

## LLM Response:
I'll help you implement this task. Let me start by reading the task tracker to understand what needs to be done.Now let me read the step 2 details to understand the specific requirements:Now let me read the summary to get more context:Perfect! Now I understand the task. I need to work on **Step 2, sub-task: "Modify `restart_closed_sessions()` to call helper if cache not provided"**. Let me first read the current orchestrator.py file to see the implementation:Perfect! I can see that the `_build_cached_issues_by_repo()` helper function has already been implemented (lines 786-827), and I need to modify `restart_closed_sessions()` to call this helper if the cache is not provided.

Looking at the current code, I can see that `restart_closed_sessions()` starts at line 830. I need to add the logic to call `_build_cached_issues_by_repo()` if `cached_issues_by_repo` is None, right after loading the sessions.

Let me now implement this change:Excellent! The change has been successfully applied. Now I need to mark this sub-task as complete in the TASK_TRACKER.md file:Perfect! The task has been completed successfully. Let me summarize what was done:

## Task Complete ✓

I successfully implemented the sub-task: **"Modify `restart_closed_sessions()` to call helper if cache not provided"**

### Changes Made:

**File**: `src/mcp_coder/workflows/vscodeclaude/orchestrator.py:892-895`

Added logic to build the cache with session issues if not provided externally:

```python
# Build cache with session issues if not provided
if cached_issues_by_repo is None:
    cached_issues_by_repo = _build_cached_issues_by_repo(store["sessions"])
```

This change was inserted right after loading the sessions and before initializing the restarted list. The implementation:

1. **Checks if cache is provided**: If `cached_issues_by_repo` parameter is `None`, it builds the cache internally
2. **Calls the helper function**: Uses the previously implemented `_build_cached_issues_by_repo()` helper to build the cache with all session issue numbers (including closed issues)
3. **Maintains backward compatibility**: If a cache is provided externally, it uses that cache as-is
4. **Enables the fix**: This ensures that closed issues from existing sessions are available in the cache for proper filtering

The task tracker has been updated to mark this sub-task as complete (`[x]`).

---
Generated on: 2026-02-11T23:50:55.408159