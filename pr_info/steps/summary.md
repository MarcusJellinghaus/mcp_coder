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
- `list_issues()` has **no error-swallowing decorator** — exceptions propagate to callers, who can distinguish success from failure
- `CacheData` gains a third field: `last_full_refresh` — tracks when the last successful full refresh occurred
- `_fetch_and_merge_issues()` uses `last_full_refresh` (not `last_checked`) for the 24-hour full refresh threshold
- `get_all_cached_issues()` wraps the fetch in try/except — on failure, skips advancing `last_checked` and returns stale cache data

### Key Design Decision: Raise vs Sentinel
The decorator silently hiding failures IS the root cause. Rather than adding a sentinel/result object around it, removing it follows Pythonic EAFP and lets all callers benefit from seeing failures. The `get_all_cached_issues()` caller handles the exception by preserving stale cache — which is the correct fallback.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/issues/manager.py` | Remove `@_handle_github_errors` from `list_issues()` |
| `src/mcp_coder/utils/github_operations/issues/cache.py` | Add `last_full_refresh` to `CacheData`; handle API failure in `get_all_cached_issues()`; use `last_full_refresh` for full refresh threshold |
| `tests/utils/github_operations/test_issue_manager_core.py` | Add test for `list_issues()` raising on non-auth errors (500, network) |
| `tests/utils/github_operations/test_issue_cache.py` | Add tests for: API failure not advancing `last_checked`; `last_full_refresh` tracking; full refresh threshold using `last_full_refresh` |

## Implementation Steps

| Step | Description | Files |
|------|-------------|-------|
| 1 | Remove `@_handle_github_errors` from `list_issues()` + tests | `manager.py`, `test_issue_manager_core.py` |
| 2 | Handle API failure in `get_all_cached_issues()` — don't advance `last_checked` on failure + tests | `cache.py`, `test_issue_cache.py` |
| 3 | Add `last_full_refresh` field and use it for full refresh threshold + tests | `cache.py`, `test_issue_cache.py` |
