# Implementation Task: Remove moved functions from `src/mcp_coder/cli/commands/coordinator/core.py`

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

Current task from TASK_TRACKER.md: Remove moved functions from `src/mcp_coder/cli/commands/coordinator/core.py`

Please implement this task step by step.

## LLM Response:
Step 2 is now complete. Here's a summary of what was accomplished:

## Step 2 Complete: Update coordinator/core.py to Use issue_cache

### Changes Made:

1. **Removed moved functions from `src/mcp_coder/cli/commands/coordinator/core.py`:**
   - `CacheData` TypedDict
   - `_load_cache_file()`
   - `_save_cache_file()`
   - `_get_cache_file_path()`
   - `_log_cache_metrics()`
   - `_log_stale_cache_entries()`
   - `_update_issue_labels_in_cache()`
   - Cleaned up unused imports (`json`, `datetime`, `timedelta`, `Any`, `Dict`, `TypedDict`, `RepoIdentifier`, timezone_utils)

2. **Added imports from `mcp_coder.utils.github_operations.issue_cache`:**
   - `CacheData`
   - `_update_issue_labels_in_cache`
   - `get_all_cached_issues`

3. **Updated `workflow_constants.py`:**
   - Changed from defining `DUPLICATE_PROTECTION_SECONDS = 50.0` locally to importing it from `mcp_coder.constants`
   - Added `__all__` to re-export the constant for backward compatibility

4. **Rewrote `get_cached_eligible_issues()` as thin wrapper:**
   - Now calls `get_all_cached_issues()` from issue_cache module
   - Filters results using `_filter_eligible_issues()` (kept in place)
   - Falls back to `get_eligible_issues()` on cache errors

5. **Updated `coordinator/__init__.py`:**
   - Re-exports cache functions from `issue_cache` for backward compatibility
   - Tests can still patch at `mcp_coder.cli.commands.coordinator.<function>`

6. **Kept in place (coordinator-specific):**
   - `_filter_eligible_issues()` 
   - `get_eligible_issues()`

### Code Quality Checks:
- ✅ pylint - No errors or fatal issues
- ✅ mypy - No type errors

### Commit message prepared:
```
refactor(coordinator): use issue_cache module for caching operations

Update coordinator/core.py to use the new issue_cache module:
- Remove CacheData, _load_cache_file, _save_cache_file, _get_cache_file_path,
  _log_cache_metrics, _log_stale_cache_entries, _update_issue_labels_in_cache
- Add imports from utils.github_operations.issue_cache
- Rewrite get_cached_eligible_issues() as thin wrapper calling
  get_all_cached_issues() and _filter_eligible_issues()
- Keep _filter_eligible_issues() and get_eligible_issues() in place
  (coordinator-specific logic)

Update workflow_constants.py:
- Import DUPLICATE_PROTECTION_SECONDS from constants.py instead of
  defining locally

Update coordinator/__init__.py:
- Re-export cache functions from issue_cache for backward compatibility

Part of: Issue #257 - Refactor Cache Logic to github_operations
```

---
Generated on: 2026-01-18T23:21:17.324938