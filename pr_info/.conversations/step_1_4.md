# Implementation Task: Remove `get_cache_refresh_minutes` from `coordinator/__init__.py` exports

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
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Remove `get_cache_refresh_minutes` from `coordinator/__init__.py` exports

Please implement this task step by step.

## LLM Response:
**Step 1 is now complete!** Here's a summary of what was accomplished:

## Step 1 Completion Summary

All sub-tasks in Step 1 have been completed:

1. ✅ **Removed `get_cache_refresh_minutes` from coordinator/__init__.py exports**
   - Removed from import statement from `.core`
   - Removed from `__all__` list

2. ✅ **Added tests for moved function in tests/utils/test_user_config.py**
   - Added `TestGetCacheRefreshMinutes` class with 5 tests:
     - `test_get_cache_refresh_minutes_default` - Returns 1440 when config not set
     - `test_get_cache_refresh_minutes_from_config` - Returns configured value
     - `test_get_cache_refresh_minutes_invalid_value` - Returns 1440 for non-integer values
     - `test_get_cache_refresh_minutes_negative_value` - Returns 1440 for negative values
     - `test_get_cache_refresh_minutes_zero_value` - Returns 1440 for zero value

3. ✅ **Updated test patches in tests/cli/commands/coordinator/test_core.py**
   - Updated import to use `mcp_coder.utils.user_config`
   - Updated all `@patch` decorators to patch at new location

4. ✅ **Fixed additional files that were importing from old location**
   - `src/mcp_coder/utils/vscodeclaude/orchestrator.py:345`
   - `src/mcp_coder/cli/commands/coordinator/commands.py:387`

5. ✅ **All checks pass**
   - Pylint: No new issues (only pre-existing unrelated issues)
   - Mypy: No type errors

6. ✅ **Commit message prepared** at `pr_info/.commit_message.txt`

---
Generated on: 2026-01-31T11:45:17.531287