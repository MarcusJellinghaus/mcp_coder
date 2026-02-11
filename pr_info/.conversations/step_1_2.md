# Implementation Task: Add `additional_issues` parameter to `get_all_cached_issues()` function signature

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

Current task from TASK_TRACKER.md: Add `additional_issues` parameter to `get_all_cached_issues()` function signature

Please implement this task step by step.

## LLM Response:
I'll implement this task step by step. Let me start by reading the task tracker to understand the current state.Now let me read the detailed instructions for Step 1 to understand the task better.Perfect! Now let me read the current implementation file to understand what I'm working with.Perfect! Now I understand the current implementation. Let me work on the current task: **Add `additional_issues` parameter to `get_all_cached_issues()` function signature**.

According to the task tracker, I need to:
1. Add the `additional_issues` parameter to the function signature
2. This is just step 3 in the checklist (the first two tasks - writing tests and running them - are already complete)

Let me first check the test file to understand what's expected:Great! Now I can see the tests are already written. Looking at the task tracker, the current task is:

**"Add `additional_issues` parameter to `get_all_cached_issues()` function signature"**

Let me now implement this change to the function signature:Good! Now I need to update the docstring to document the new parameter. Let me update it:Perfect! Now let me mark this sub-task as complete in the task tracker:Perfect! I've successfully completed the task: **Add `additional_issues` parameter to `get_all_cached_issues()` function signature**.

## Summary

I've implemented the following changes to `src/mcp_coder/utils/github_operations/issues/cache.py`:

1. **Added the `additional_issues` parameter** to the `get_all_cached_issues()` function signature with type annotation `list[int] | None = None` and default value `None`

2. **Updated the docstring** to document the new parameter, explaining that it's an optional list of issue numbers to fetch even if closed, and that these are fetched via individual API calls and merged into cache

The changes ensure:
- **Backward compatibility**: Default value of `None` means existing calls will work unchanged
- **Type safety**: Proper type annotation using modern Python union syntax
- **Documentation**: Clear docstring explaining the parameter's purpose and behavior

The task has been marked as complete in the task tracker at `pr_info/TASK_TRACKER.md:28`.

---
Generated on: 2026-02-11T23:25:22.229804