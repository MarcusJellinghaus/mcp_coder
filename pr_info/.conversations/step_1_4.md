# Implementation Task: Add `--force-refresh` CLI flag to coordinator run command

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

Current task from TASK_TRACKER.md: Add `--force-refresh` CLI flag to coordinator run command

Please implement this task step by step.

## LLM Response:
Perfect! I have successfully completed Step 3 of the task tracker. 

## Summary

I have successfully implemented the **`--force-refresh` CLI flag** feature for the coordinator run command with all the required functionality:

### ✅ What was implemented:

1. **CLI Flag**: Added `--force-refresh` argument to `src/mcp_coder/cli/main.py` for the coordinator run command
2. **Configuration**: Implemented `get_cache_refresh_minutes()` function in `src/mcp_coder/cli/commands/coordinator.py` with proper validation and default fallback
3. **Integration**: Modified `execute_coordinator_run()` to use cached eligible issues with graceful fallback to direct fetch
4. **Tests**: Added comprehensive integration tests covering all scenarios
5. **Code Quality**: All checks passed (pylint, mypy, pytest)
6. **Documentation**: Prepared detailed commit message

### ✅ Key features:

- **`--force-refresh` flag**: Bypasses all caching when set to `true`
- **Configuration support**: Reads `cache_refresh_minutes` from `[coordinator]` section with 1440 minute (24 hour) default
- **Graceful fallback**: Any cache errors automatically fall back to direct GitHub API calls with warning logs
- **Full backward compatibility**: Existing behavior preserved, zero breaking changes
- **Comprehensive error handling**: Invalid config values fall back to defaults

The implementation follows all the specified requirements and maintains the existing codebase patterns. Step 3 is now complete and ready for the next phase of development.

---
Generated on: 2025-12-31T17:58:41.477587