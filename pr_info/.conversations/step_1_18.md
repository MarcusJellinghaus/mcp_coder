# Implementation Task: Update `core.py` to import from both new modules

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

Current task from TASK_TRACKER.md: Update `core.py` to import from both new modules

Please implement this task step by step.

## LLM Response:
I've completed the task: **Update `core.py` to import from both new modules**

## Summary

I added imports to `core.py` from both new constant modules:

1. **From `command_templates.py`:**
   - `CREATE_PLAN_COMMAND_TEMPLATE`
   - `CREATE_PLAN_COMMAND_WINDOWS`
   - `CREATE_PR_COMMAND_TEMPLATE`
   - `CREATE_PR_COMMAND_WINDOWS`
   - `IMPLEMENT_COMMAND_TEMPLATE`
   - `IMPLEMENT_COMMAND_WINDOWS`

2. **From `workflow_constants.py`:**
   - `WORKFLOW_MAPPING`

The imports were added after the `get_config_file_path` import at `src/mcp_coder/cli/commands/coordinator/core.py:30-38`.

**Note:** The duplicate template definitions still exist locally in `core.py`. The next sub-task "Remove duplicate templates from `commands.py` and `core.py`" will handle removing those local definitions since we're now importing them from the dedicated modules.

---
Generated on: 2026-01-06T23:47:40.406106