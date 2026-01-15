# Implementation Task: Update `core.py` get_jenkins_credentials() - 3 calls → 1 batch

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

Current task from TASK_TRACKER.md: Update `core.py` get_jenkins_credentials() - 3 calls → 1 batch

Please implement this task step by step.

## LLM Response:
## Summary

I've completed the sub-task: **Update `core.py` get_jenkins_credentials() - 3 calls → 1 batch**

### Changes Made

**File:** `src/mcp_coder/cli/commands/coordinator/core.py:198-214`

**Before:**
```python
# get_config_value automatically checks environment variables first
server_url = coordinator.get_config_value("jenkins", "server_url")
username = coordinator.get_config_value("jenkins", "username")
api_token = coordinator.get_config_value("jenkins", "api_token")
```

**After:**
```python
# Batch fetch all Jenkins credentials in single disk read
config = coordinator.get_config_values(
    [
        ("jenkins", "server_url", None),
        ("jenkins", "username", None),
        ("jenkins", "api_token", None),
    ]
)
server_url = config[("jenkins", "server_url")]
username = config[("jenkins", "username")]
api_token = config[("jenkins", "api_token")]
```

This converts 3 individual disk reads into a single batch operation, improving performance.

### Next Sub-Task in Step 4
The next unchecked sub-task is: **Update `tests/conftest.py` - 2 calls → 1 batch**

---
Generated on: 2026-01-15T15:25:55.812691