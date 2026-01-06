# Implementation Task: Create `coordinator/workflow_constants.py` with WORKFLOW_MAPPING

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

Current task from TASK_TRACKER.md: Create `coordinator/workflow_constants.py` with WORKFLOW_MAPPING

Please implement this task step by step.

## LLM Response:
I have completed the current sub-task from Step 6:

## Summary

**Task Completed:** Create `coordinator/workflow_constants.py` with WORKFLOW_MAPPING

**What was done:**
- Created new file: `src/mcp_coder/cli/commands/coordinator/workflow_constants.py`
- Defined `WorkflowConfig` TypedDict with proper type annotations and docstring
- Moved `WORKFLOW_MAPPING` dictionary with all three workflow configurations:
  - `status-02:awaiting-planning` → `create-plan` workflow
  - `status-05:plan-ready` → `implement` workflow  
  - `status-08:ready-pr` → `create-pr` workflow
- Added module-level documentation explaining the purpose
- Updated task tracker to mark sub-task as complete (`- [x]`)

**Next sub-task in Step 6:** Update `commands.py` to import from `command_templates.py`

---
Generated on: 2026-01-06T23:42:16.048833