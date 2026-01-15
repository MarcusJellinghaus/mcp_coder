# Implementation Task: Update `client.py` - 3 calls → 1 batch

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

Current task from TASK_TRACKER.md: Update `client.py` - 3 calls → 1 batch

Please implement this task step by step.

## LLM Response:
I've completed the sub-task: **Update `client.py` - 3 calls → 1 batch**

## Summary of changes made to `src/mcp_coder/utils/jenkins_operations/client.py`:

1. **Updated import** (line 35):
   - Changed `from ..user_config import get_config_value` to `from ..user_config import get_config_values`

2. **Refactored `_get_jenkins_config()` function** (lines 76-88):
   - Replaced 3 separate `get_config_value()` calls with a single `get_config_values()` batch call
   - Now retrieves all 3 Jenkins config values (`server_url`, `username`, `api_token`) in one disk read
   - Updated return statement to extract values from the batch result dictionary

The sub-task has been marked as `[x]` in the TASK_TRACKER.md. The next sub-task in Step 4 is: **Update `core.py` load_repo_config() - 4 calls → 1 batch**

---
Generated on: 2026-01-15T15:21:32.759439