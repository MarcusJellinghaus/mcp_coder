# Implementation Task: Implement Step 2: Update Linux templates to use `--extra types` instead of `--extra dev`

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

Current task from TASK_TRACKER.md: Implement Step 2: Update Linux templates to use `--extra types` instead of `--extra dev`

Please implement this task step by step.

## LLM Response:
## Step 2 Complete

All sub-tasks for Step 2 have been completed:

### Summary of changes:

1. **Linux templates updated** (`command_templates.py`):
   - `DEFAULT_TEST_COMMAND`: `uv sync --extra dev` → `uv sync --extra types`
   - `CREATE_PLAN_COMMAND_TEMPLATE`: `uv sync --extra dev` → `uv sync --extra types`
   - `IMPLEMENT_COMMAND_TEMPLATE`: `uv sync --extra dev` → `uv sync --extra types`
   - `CREATE_PR_COMMAND_TEMPLATE`: `uv sync --extra dev` → `uv sync --extra types`

2. **Windows templates updated** (`command_templates.py`):
   Added the following block to all 4 Windows templates (before command execution):
   ```batch
   echo Install type stubs in project environment ====================
   uv sync --project %WORKSPACE%\repo --extra types
   ```

3. **Unit tests added** (`test_commands.py`):
   - `TestLinuxTemplatesUseTypesExtra` class (4 tests)
   - `TestWindowsTemplatesInstallTypeStubs` class (4 tests)

4. **Quality checks passed**: Pylint clean, mypy issues are pre-existing (unrelated to changes)

5. **Commit message prepared**: Saved to `pr_info/commit_message_step2.txt`

---
Generated on: 2026-01-07T22:09:35.080084