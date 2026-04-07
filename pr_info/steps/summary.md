# Issue #701: Cache incremental refresh permanently misses issues on silent API failure

## Problem Summary

Three interacting bugs cause the issue cache to permanently miss updates:

1. **Silent API failure** — `list_issues()` is wrapped in `@_handle_github_errors(default_return=[])`, so any exception returns `[]`. The caller cannot distinguish "no changes" from "API failed", and advances `last_checked` anyway — permanently skipping the failed window.
2. **Full refresh never fires** — The 24-hour full refresh threshold uses `last_checked`, which advances every ~55 seconds during normal usage. The only recovery mechanism (full refresh) is unreachable.
3. **One-way ratchet** — These combine: `last_checked` only moves forward, a single failure creates a permanent gap, and the recovery path is blocked.

## Architectural / Design Changes

### Before
- `list_issues()` has `@_handle_github_errors(default_return=[])` — silently returns `[]` on any non-auth exception
- `CacheData` has two fields: `last_checked` and `issues`
- `_fetch_and_merge_issues()` uses `last_checked` for both incremental refresh timing AND the 24-hour full refresh threshold
- `get_all_cached_issues()` always advances `last_checked` after calling `_fetch_and_merge_issues()`, regardless of success/failure

### After
- `list_issues()` keeps `@_handle_github_errors(default_return=[])` for backward compatibility; a new private `_list_issues_no_error_handling()` exposes the raw body that raises on failure
- The cache path calls `_list_issues_no_error_handling()` directly to detect failures
- `CacheData` gains a third field: `last_full_refresh` — tracks when the last successful full refresh occurred
- `_fetch_and_merge_issues()` uses `last_full_refresh` (not `last_checked`) for the 24-hour full refresh threshold
- `get_all_cached_issues()` wraps the fetch in try/except — on failure, restores a pre-fetch snapshot of cached issues and returns stale data

### Key Design Decision: Two-function split
Rather than removing the decorator (which would change behavior for all callers), we split into two functions: `_list_issues_no_error_handling()` (raises on failure) and `list_issues()` (delegates, keeps decorator). The cache calls the private function directly to detect failures. All other callers are unchanged.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/issues/manager.py` | Extract `_list_issues_no_error_handling()`; `list_issues()` delegates to it |
| `src/mcp_coder/utils/github_operations/issues/cache.py` | Call `_list_issues_no_error_handling()`; add `last_full_refresh` to `CacheData`; handle API failure with snapshot restore in `get_all_cached_issues()` |
| `tests/utils/github_operations/test_issue_manager_core.py` | Test `_list_issues_no_error_handling()` raises on errors; test `list_issues()` still returns `[]` |
| `tests/utils/github_operations/test_issue_cache.py` | Tests for: API failure not advancing `last_checked`; snapshot restore on failure; `last_full_refresh` tracking; full refresh threshold using `last_full_refresh` |

## Implementation Steps

| Step | Description | Files |
|------|-------------|-------|
| 1 | Extract `_list_issues_no_error_handling()` from `list_issues()` + tests | `manager.py`, `test_issue_manager_core.py` |
| 2 | Handle API failure in `get_all_cached_issues()` with snapshot restore + tests | `cache.py`, `test_issue_cache.py` |
| 3 | Add `last_full_refresh` field and use it for full refresh threshold + tests | `cache.py`, `test_issue_cache.py` |
