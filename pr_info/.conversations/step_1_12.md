# Implementation Task: Update `core.py` get_cache_refresh_minutes() - 1 call

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

Current task from TASK_TRACKER.md: Update `core.py` get_cache_refresh_minutes() - 1 call

Please implement this task step by step.

## LLM Response:
## Summary

I've completed the sub-task: **Update `core.py` get_cache_refresh_minutes() - 1 call**

### Change Made

In `src/mcp_coder/cli/commands/coordinator/core.py:160-167`, updated the `get_cache_refresh_minutes()` function:

**Before:**
```python
value = coordinator.get_config_value("coordinator", "cache_refresh_minutes")
```

**After:**
```python
# Batch fetch config value in single disk read
config = coordinator.get_config_values(
    [("coordinator", "cache_refresh_minutes", None)]
)
value = config[("coordinator", "cache_refresh_minutes")]
```

The task tracker has been updated to mark this sub-task as complete (`- [x]`).

---
Generated on: 2026-01-15T15:24:28.026993