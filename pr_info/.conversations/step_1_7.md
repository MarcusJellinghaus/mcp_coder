# Implementation Task: Add helper function `_attempt_rebase()` to `src/mcp_coder/workflows/implement/core.py`

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

Current task from TASK_TRACKER.md: Add helper function `_attempt_rebase()` to `src/mcp_coder/workflows/implement/core.py`

Please implement this task step by step.

## LLM Response:
## Summary

I have successfully completed the sub-task: **Add helper function `_attempt_rebase()` to `src/mcp_coder/workflows/implement/core.py`**

### Changes Made:

1. **Added `_attempt_rebase()` function** (`src/mcp_coder/workflows/implement/core.py:94-109`):
   - Takes `project_dir: Path` as argument
   - Returns `bool` - True if rebase succeeded (for subsequent force_with_lease push)
   - Calls `_get_rebase_target_branch()` to detect the parent branch
   - If target detected, calls `rebase_onto_branch()` and logs the action
   - Never fails the workflow - returns False on any failure or skip

2. **Integrated into `run_implement_workflow()`** (`src/mcp_coder/workflows/implement/core.py:337-338`):
   - Called after prerequisites check (Step 1) but before `prepare_task_tracker()` (Step 2)
   - Result stored in `_rebase_succeeded` variable (to be used in next sub-task for force_with_lease)

### Quality Checks:
- **Pylint**: No errors/fatal issues
- **Mypy**: No type errors

### Task Tracker Updated:
- Marked sub-task `- [x] Add helper function _attempt_rebase() to src/mcp_coder/workflows/implement/core.py` as complete

---
Generated on: 2026-01-15T22:23:34.093874