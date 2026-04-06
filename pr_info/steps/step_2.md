# Step 2: Handle API failure in `get_all_cached_issues()` — don't advance `last_checked`

## Context
See `pr_info/steps/summary.md` for full context. This is step 2 of 3.

After step 1, `list_issues()` now raises on failure. This step makes the cache resilient to those failures by catching exceptions and preserving `last_checked` so the next refresh retries from the same window.

## Goal
When `_fetch_and_merge_issues()` raises (because `list_issues()` failed), `get_all_cached_issues()` should:
1. Log a warning
2. **Not** advance `last_checked`
3. **Not** update cache with empty data
4. Return existing cached issues (stale data is better than a permanent gap)

## WHERE
- **Modify:** `src/mcp_coder/utils/github_operations/issues/cache.py`
- **Modify:** `tests/utils/github_operations/test_issue_cache.py`

## WHAT

### Production code
In `get_all_cached_issues()`, wrap the `_fetch_and_merge_issues()` call (step 4) and the subsequent cache update (steps 5-6) in a try/except. On exception, log warning and return current cached issues.

**ALGORITHM (pseudocode):**
```
try:
    fresh_issues = _fetch_and_merge_issues(...)
    cache_data["issues"].update(fresh_dict)
    cache_data["last_checked"] = format_for_cache(now)
    _save_cache_file(...)
except Exception:
    logger.warning("API fetch failed for %s, returning stale cache", repo_name)
    return list(cache_data["issues"].values())
```

Specifically: wrap lines from "Step 4" through "Step 6" (the fetch, merge, timestamp update, and save) in a try/except block. The except should catch `Exception` (since `list_issues()` can raise `GithubException`, `ConnectionError`, etc.) with a `# pylint: disable=broad-exception-caught` comment. On failure, skip all cache mutations and return current `cache_data["issues"]` values.

The `additional_dict` restore (step 5b) should also be inside the try block since it's part of the successful-fetch path.

### Test code
Add tests in `tests/utils/github_operations/test_issue_cache.py`:

**`test_api_failure_does_not_advance_last_checked`**
- Set up cache file with known `last_checked` timestamp and some existing issues
- Mock `list_issues()` to raise `GithubException(500, ...)`
- Call `get_all_cached_issues()`
- Verify returned issues are the stale cached issues
- Reload cache file and verify `last_checked` is unchanged (not advanced)

**`test_api_failure_returns_stale_cached_issues`**
- Set up cache with 3 known issues and a `last_checked` from 2 minutes ago
- Mock `list_issues()` to raise `ConnectionError`
- Call `get_all_cached_issues()`
- Verify all 3 stale issues are returned

**`test_successful_fetch_still_advances_last_checked`**
- Existing behavior sanity check — mock `list_issues()` to return issues normally
- Verify `last_checked` is updated after the call

## HOW
- The try/except wraps lines in `get_all_cached_issues()` from step 4 through step 6
- Use the same test fixtures/patterns as existing cache tests (mock `_load_cache_file`, `_save_cache_file`, `list_issues`, etc.)

## DATA
- **Return value on failure:** `List[IssueData]` — the stale cached issues
- **Cache file on failure:** Unchanged (no write)
- **`last_checked` on failure:** Unchanged (not advanced)

## LLM Prompt
```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_2.md.

In get_all_cached_issues() in src/mcp_coder/utils/github_operations/issues/cache.py,
wrap the _fetch_and_merge_issues() call and subsequent cache update (steps 4-6) in 
try/except. On exception: log warning, skip cache mutations, return stale cached issues.

Add tests in tests/utils/github_operations/test_issue_cache.py:
1. test_api_failure_does_not_advance_last_checked
2. test_api_failure_returns_stale_cached_issues  
3. test_successful_fetch_still_advances_last_checked

Run all three quality checks after changes. Commit as one unit.
```
