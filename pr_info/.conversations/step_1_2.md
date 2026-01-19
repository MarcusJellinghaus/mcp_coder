# Implementation Task: Add `run_finalisation()` function to `src/mcp_coder/workflows/implement/core.py`

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

Current task from TASK_TRACKER.md: Add `run_finalisation()` function to `src/mcp_coder/workflows/implement/core.py`

Please implement this task step by step.

## LLM Response:
I have completed the first sub-task of Step 2. Here's a summary of what was implemented:

## Summary

**Task Completed:** Add `run_finalisation()` function to `src/mcp_coder/workflows/implement/core.py`

### Changes Made:

1. **Added new imports** at line 22-26:
   - `TaskTrackerFileNotFoundError` from `mcp_coder.workflow_utils.task_tracker`
   - `has_incomplete_work` from `mcp_coder.workflow_utils.task_tracker`

2. **Added new constants** at lines 44-63:
   - `COMMIT_MESSAGE_FILE = ".commit_message.txt"`
   - `LLM_FINALISATION_TIMEOUT_SECONDS = 600`
   - `FINALISATION_PROMPT` - the prompt used to instruct the LLM to complete remaining tasks

3. **Added `run_finalisation()` function** at lines 328-394:
   - Function signature matches specification with parameters: `project_dir`, `provider`, `method`, `mcp_config`, `execution_dir`, `auto_push`
   - Returns `bool` indicating success
   - Algorithm:
     1. Checks for incomplete tasks using `has_incomplete_work()`
     2. Returns `True` early if no incomplete tasks
     3. Handles `TaskTrackerFileNotFoundError` gracefully
     4. Calls LLM with the finalisation prompt
     5. Returns `False` if LLM response is empty
     6. Pushes changes if `auto_push=True` and there are pending changes

The sub-task has been marked as complete in `pr_info/TASK_TRACKER.md`. The next sub-task in Step 2 is "Integrate finalisation call into `run_implement_workflow()` after final mypy check".

---
Generated on: 2026-01-19T17:16:19.384960