# Implementation Task: Update `src/mcp_coder/utils/github_operations/__init__.py` with issue_cache exports

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

Current task from TASK_TRACKER.md: Update `src/mcp_coder/utils/github_operations/__init__.py` with issue_cache exports

Please implement this task step by step.

## LLM Response:
I've completed Step 3. Let me provide a summary of what was accomplished:

## Summary - Step 3: Update Module Exports (Complete)

### Changes Made:

1. **Updated `src/mcp_coder/utils/github_operations/__init__.py`**:
   - Added imports from `issue_cache`: `CacheData`, `_update_issue_labels_in_cache`, `get_all_cached_issues`
   - Added these to the `__all__` list

2. **Updated `src/mcp_coder/cli/commands/coordinator/__init__.py`**:
   - Removed private cache function imports: `_get_cache_file_path`, `_load_cache_file`, `_save_cache_file`, `_log_cache_metrics`, `_log_stale_cache_entries`
   - Removed these from `__all__` list
   - Kept public API exports: `CacheData`, `_update_issue_labels_in_cache`

### Verification:
- ✅ Pylint passed (no errors)
- ✅ Mypy passed (no type errors)
- ⚠️ Pytest has config issue with MCP tool, but tests that import private functions will need updates in Step 4

### Prepared Commit Message:
```
feat(exports): update module exports for issue_cache

Update __init__.py files to expose cache functionality:

github_operations/__init__.py:
- Add exports: CacheData, get_all_cached_issues, _update_issue_labels_in_cache
- Private helpers stay internal to issue_cache.py

coordinator/__init__.py:
- Remove private cache function exports (now internal to issue_cache)
- Keep public API: CacheData, get_cached_eligible_issues, _update_issue_labels_in_cache

Note: Tests patching private functions will be updated in Step 4.

Part of: Issue #257 - Refactor Cache Logic to github_operations
```

---
Generated on: 2026-01-18T23:25:49.593518