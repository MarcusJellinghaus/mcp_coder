# Implementation Task: Move `DUPLICATE_PROTECTION_SECONDS` constant to `src/mcp_coder/constants.py`

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

Current task from TASK_TRACKER.md: Move `DUPLICATE_PROTECTION_SECONDS` constant to `src/mcp_coder/constants.py`

Please implement this task step by step.

## LLM Response:
## Summary

**Completed sub-task:** Move `DUPLICATE_PROTECTION_SECONDS` constant to `src/mcp_coder/constants.py`

**Changes made:**
- Added `DUPLICATE_PROTECTION_SECONDS = 50.0` to `src/mcp_coder/constants.py` with the original comment explaining its purpose (buffer for Jenkins ~60s scheduler variance)

**Note:** The constant still exists in `workflow_constants.py` - per Step 2, that file will be updated to import from `constants.py` instead. This avoids breaking existing code during the incremental refactoring process.

The sub-task has been marked as complete `[x]` in the task tracker.

---
Generated on: 2026-01-18T23:04:25.011665