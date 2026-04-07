# Step 2: Handle API failure in `get_all_cached_issues()` with snapshot restore

## Context
See `pr_info/steps/summary.md` for full context. This is step 2 of 3.

**Depends on step 1** — the cache calls `_list_issues_no_error_handling()` (introduced in step 1) to detect API failures.

## Goal
When `_fetch_and_merge_issues()` raises (because `_list_issues_no_error_handling()` failed), `get_all_cached_issues()` should:
1. Log a warning
2. **Not** advance `last_checked`
3. Restore the pre-fetch cache snapshot (since `_fetch_and_merge_issues` clears `cache_data["issues"]` on full refresh before calling the API)
4. Return existing cached issues (stale data is better than a permanent gap)

## WHERE
- **Modify:** `src/mcp_coder/utils/github_operations/issues/cache.py`
- **Modify:** `tests/utils/github_operations/test_issue_cache.py`

## WHAT

### Production code

#### 1. Change `_fetch_and_merge_issues` to call `_list_issues_no_error_handling`
Replace calls to `issue_manager.list_issues(...)` with `issue_manager._list_issues_no_error_handling(...)` so exceptions propagate instead of being swallowed.

#### 2. Snapshot + try/except in `get_all_cached_issues()`
**CRITICAL**: `_fetch_and_merge_issues` does `cache_data["issues"] = {}` on full refresh BEFORE calling the API. If the API call raises after the clear, `cache_data["issues"]` is empty. The exception handler must restore from a snapshot taken before the fetch.

**ALGORITHM (pseudocode):**
```
# Save snapshot BEFORE fetch (in case full refresh clears cache_data["issues"])
issues_snapshot = dict(cache_data["issues"])

try:
    fresh_issues = _fetch_and_merge_issues(...)
    fresh_dict = {str(issue["number"]): issue for issue in fresh_issues}
    cache_data["issues"].update(fresh_dict)
    if additional_dict:
        cache_data["issues"].update(additional_dict)
    cache_data["last_checked"] = format_for_cache(now)
    _save_cache_file(...)
except Exception:  # pylint: disable=broad-exception-caught
    logger.warning("API fetch failed for %s, returning stale cache", repo_name)
    cache_data["issues"] = issues_snapshot
    return list(cache_data["issues"].values())
```

#### 3. Update `mock_cache_issue_manager` fixture
In `tests/utils/github_operations/conftest.py`, update the `mock_cache_issue_manager` fixture to mock `_list_issues_no_error_handling` instead of (or in addition to) `list_issues`, since `_fetch_and_merge_issues` now calls the private method. Existing cache tests will break without this.

### Test code
Add tests in `tests/utils/github_operations/test_issue_cache.py`:

**`test_api_failure_does_not_advance_last_checked`**
- Set up cache with known `last_checked` and existing issues
- Mock `_list_issues_no_error_handling()` to raise `GithubException(500, ...)`
- Call `get_all_cached_issues()`
- Verify `last_checked` is unchanged in cache file

**`test_api_failure_returns_stale_cached_issues`**
- Set up cache with 3 known issues
- Mock `_list_issues_no_error_handling()` to raise `ConnectionError`
- Verify all 3 stale issues are returned

**`test_api_failure_restores_snapshot_on_full_refresh`**
- Set up cache with known issues and `last_checked=None` (triggers full refresh)
- Mock `_list_issues_no_error_handling()` to raise after `cache_data["issues"]` is cleared
- Verify returned issues match the original cached issues (snapshot restored)

**`test_successful_fetch_still_advances_last_checked`**
- Sanity check — mock a successful fetch, verify `last_checked` is updated

## HOW
- The try/except wraps steps 4 through 6 in `get_all_cached_issues()`
- The snapshot is a shallow dict copy taken after `additional_dict` is merged into `cache_data["issues"]` (after step 2 in `get_all_cached_issues`) but before step 4 (`_fetch_and_merge_issues`)
- Use the same test fixtures/patterns as existing cache tests

## DATA
- **Return value on failure:** `List[IssueData]` — the stale cached issues (from snapshot)
- **Cache file on failure:** Unchanged (no write)
- **`last_checked` on failure:** Unchanged (not advanced)

## LLM Prompt
```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_2.md.
This step depends on step 1 (the _list_issues_no_error_handling method must exist).

In src/mcp_coder/utils/github_operations/issues/cache.py:
1. Change _fetch_and_merge_issues to call _list_issues_no_error_handling instead of list_issues
2. In get_all_cached_issues(), save issues_snapshot = dict(cache_data["issues"]) before step 4
3. Wrap steps 4-6 in try/except. On exception: restore cache_data["issues"] from snapshot,
   log warning, return stale issues

Add tests in tests/utils/github_operations/test_issue_cache.py:
1. test_api_failure_does_not_advance_last_checked
2. test_api_failure_returns_stale_cached_issues
3. test_api_failure_restores_snapshot_on_full_refresh
4. test_successful_fetch_still_advances_last_checked

Run all quality checks after changes. Commit as one unit.
```
