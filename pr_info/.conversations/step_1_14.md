# Implementation Task: Update `tests/conftest.py` - 2 calls → 1 batch

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

Current task from TASK_TRACKER.md: Update `tests/conftest.py` - 2 calls → 1 batch

Please implement this task step by step.

## LLM Response:
## Summary

**Completed sub-task**: Update `tests/conftest.py` - 2 calls → 1 batch

**Changes made to `tests/conftest.py`**:

1. **Updated import** (line 226):
   - Before: `from mcp_coder.utils.user_config import get_config_file_path, get_config_value`
   - After: `from mcp_coder.utils.user_config import get_config_file_path, get_config_values`

2. **Refactored config retrieval** in `github_test_setup` fixture (lines 236-245):
   - Before: 2 separate `get_config_value()` calls
   - After: 1 batch `get_config_values()` call that retrieves both values in a single disk read

The refactoring follows the pattern specified in `step_4.md`, only loading config when at least one value is missing from environment variables.

---
Generated on: 2026-01-15T15:27:19.244624