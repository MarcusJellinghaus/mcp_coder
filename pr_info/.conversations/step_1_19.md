# Implementation Task: Remove duplicate templates from `commands.py` and `core.py`

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

Current task from TASK_TRACKER.md: Remove duplicate templates from `commands.py` and `core.py`

Please implement this task step by step.

## LLM Response:
## Summary

I completed the task **"Remove duplicate templates from `commands.py` and `core.py`"** from Step 6.

### Changes Made:

1. **`src/mcp_coder/cli/commands/coordinator/core.py`**:
   - Removed duplicate `WORKFLOW_MAPPING` definition (was already imported from `workflow_constants.py`)
   - Removed duplicate Windows command templates (`CREATE_PLAN_COMMAND_WINDOWS`, `IMPLEMENT_COMMAND_WINDOWS`, `CREATE_PR_COMMAND_WINDOWS`)
   - Removed duplicate Linux command templates (`CREATE_PLAN_COMMAND_TEMPLATE`, `IMPLEMENT_COMMAND_TEMPLATE`, `CREATE_PR_COMMAND_TEMPLATE`)
   - These templates are now used only from the imports at the top of the file from `command_templates.py`

2. **`src/mcp_coder/cli/commands/coordinator/commands.py`**:
   - Updated import of `WORKFLOW_MAPPING` to come from `workflow_constants.py` instead of `core.py`

3. **`src/mcp_coder/cli/commands/coordinator/__init__.py`**:
   - Updated import of `WORKFLOW_MAPPING` to come from `workflow_constants.py` instead of `core.py`

### Quality Checks:
- **Pylint**: ✅ No issues found
- **Mypy**: ✅ No type errors found

---
Generated on: 2026-01-06T23:50:57.831904