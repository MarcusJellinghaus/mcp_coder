# Implementation Task: Create `src/mcp_coder/utils/github_operations/issue_cache.py` module

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

Current task from TASK_TRACKER.md: Create `src/mcp_coder/utils/github_operations/issue_cache.py` module

Please implement this task step by step.

## LLM Response:
I have completed **Step 1** of the task tracker. Here's a summary of what was accomplished:

## Step 1 Complete: Create issue_cache.py Module

### Files Created
- **`src/mcp_coder/utils/github_operations/issue_cache.py`** - New module containing:
  - `CacheData` TypedDict for cache structure
  - `_load_cache_file()` - Load cache from disk
  - `_save_cache_file()` - Save cache atomically
  - `_get_cache_file_path()` - Get cache file path for a repo
  - `_log_cache_metrics()` - Debug logging for cache operations
  - `_log_stale_cache_entries()` - Log stale cache data
  - `_update_issue_labels_in_cache()` - Update labels in cache after dispatch
  - `_fetch_and_merge_issues()` - Helper to fetch and merge issues (new)
  - `get_all_cached_issues()` - Main cache function returning ALL cached issues (unfiltered)

### Quality Checks Passed
- ✅ Pylint - No issues (with appropriate disable comments for intentional patterns)
- ✅ Mypy - No type errors

### Task Tracker Updated
- All 14 sub-tasks for Step 1 marked as `[x]` complete
- Commit message prepared in TASK_TRACKER.md

### Key Implementation Notes
1. The new `get_all_cached_issues()` function extracts the caching logic from `get_cached_eligible_issues()` but does **NOT** call `_filter_eligible_issues()` - that filtering stays in the coordinator layer (Step 2)
2. The `_update_issue_labels_in_cache()` function now calls helpers directly instead of using late binding through the coordinator module
3. A helper function `_fetch_and_merge_issues()` was created to reduce local variables in the main function while maintaining readability

### Commit Message Ready
```
feat(cache): add issue_cache module to github_operations

Create new issue_cache.py module in utils/github_operations/ with:
- CacheData TypedDict for cache structure
- Cache file operations (_load_cache_file, _save_cache_file, _get_cache_file_path)
- Cache metrics logging (_log_cache_metrics, _log_stale_cache_entries)
- Cache update function (_update_issue_labels_in_cache)
- New get_all_cached_issues() function extracting caching logic

This is Step 1 of the cache refactoring - the new module is created but
coordinator/core.py still has the original functions (to be removed in Step 2).

Part of: Issue #257 - Refactor Cache Logic to github_operations
```

---
Generated on: 2026-01-18T23:12:24.265209