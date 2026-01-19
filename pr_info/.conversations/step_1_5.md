# Implementation Task: Create `tests/utils/github_operations/test_issue_cache.py`

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

Current task from TASK_TRACKER.md: Create `tests/utils/github_operations/test_issue_cache.py`

Please implement this task step by step.

## LLM Response:
I have completed the first sub-task of Step 4: **Create `tests/utils/github_operations/test_issue_cache.py`**.

## Summary of Work Completed

I successfully completed the following sub-tasks for Step 4:

### Sub-tasks completed:
1. **Created `tests/utils/github_operations/test_issue_cache.py`** - New test file with all tests from the original `test_coordinator_cache.py`

2. **Copied test content** - All test classes and methods were migrated:
   - `TestCacheMetricsLogging`
   - `TestCacheFilePath`
   - `TestCacheFileOperations`
   - `TestStalenessLogging`
   - `TestEligibleIssuesFiltering`
   - `TestGetCachedEligibleIssues`
   - `TestCacheIssueUpdate`
   - `TestCacheUpdateIntegration`

3. **Updated imports** - Changed imports to use `mcp_coder.utils.github_operations.issue_cache`:
   ```python
   from mcp_coder.utils.github_operations.issue_cache import (
       CacheData, _get_cache_file_path, _load_cache_file, _log_cache_metrics,
       _log_stale_cache_entries, _save_cache_file, _update_issue_labels_in_cache,
   )
   ```
   - Kept `_filter_eligible_issues` and `get_cached_eligible_issues` imports from coordinator (they stay there)

4. **Updated all patch paths** - Changed from `mcp_coder.cli.commands.coordinator.*` to `mcp_coder.utils.github_operations.issue_cache.*` for cache-related functions

5. **Updated logger paths** - Changed from `mcp_coder.cli.commands.coordinator.core` to `mcp_coder.utils.github_operations.issue_cache`

6. **Added fixtures to conftest.py** - Added `sample_issue`, `sample_cache_data`, and `mock_cache_issue_manager` fixtures to `tests/utils/github_operations/conftest.py`

7. **Removed fixture definitions from test file** - The test file now uses fixtures from conftest.py

### Files created/modified:
- **Created**: `tests/utils/github_operations/test_issue_cache.py` (new test file)
- **Modified**: `tests/utils/github_operations/conftest.py` (added cache fixtures)
- **Modified**: `pr_info/TASK_TRACKER.md` (marked sub-tasks complete)

### Remaining sub-tasks for Step 4:
- Run pytest on `tests/utils/github_operations/test_issue_cache.py` to verify tests pass
- Run pytest on coordinator tests to ensure they still pass  
- Delete original `tests/utils/test_coordinator_cache.py` after verification
- Run pylint on test files and fix any issues
- Run mypy on test files and fix any type errors
- Run full pytest suite and ensure all tests pass
- Prepare git commit message for Step 4

**Note**: Running the tests requires command approval. The remaining sub-tasks should be completed in the next run once the test commands are approved.

---
Generated on: 2026-01-18T23:32:02.111072