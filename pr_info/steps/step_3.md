# Step 3: Add `last_full_refresh` field and use it for full refresh threshold

## Context
See `pr_info/steps/summary.md` for full context. This is step 3 of 3.

After steps 1-2, API failures no longer cause permanent gaps. But frequent usage still prevents the 24-hour full refresh from firing because `last_checked` advances every ~55 seconds. This step separates the two concerns.

## Goal
Track `last_full_refresh` independently from `last_checked`. The 24-hour full refresh threshold uses `last_full_refresh`, which only advances after a successful full refresh. This ensures periodic full refreshes fire regardless of how frequently incremental refreshes run.

## WHERE
- **Modify:** `src/mcp_coder/utils/github_operations/issues/cache.py`
- **Modify:** `tests/utils/github_operations/test_issue_cache.py`

## WHAT

### Production code

#### 1. Add `last_full_refresh` to `CacheData` TypedDict
```python
class CacheData(TypedDict):
    last_checked: Optional[str]
    last_full_refresh: Optional[str]
    issues: Dict[str, IssueData]
```

#### 2. Update `_load_cache_file()` to include `last_full_refresh`
```python
return {
    "last_checked": data.get("last_checked"),
    "last_full_refresh": data.get("last_full_refresh"),
    "issues": data["issues"],
}
```
Also update the empty/error return values to include `"last_full_refresh": None`.

#### 3. Update `_fetch_and_merge_issues()` signature and full refresh logic
Add `last_full_refresh: Optional[datetime]` parameter. Change the `is_full_refresh` condition:

**Before:**
```python
is_full_refresh = (
    force_refresh
    or not last_checked
    or (now - last_checked) > timedelta(minutes=cache_refresh_minutes)
)
```

**After:**
```python
is_full_refresh = (
    force_refresh
    or not last_checked
    or not last_full_refresh
    or (now - last_full_refresh) > timedelta(minutes=cache_refresh_minutes)
)
```

#### 4. Update `get_all_cached_issues()` to parse and pass `last_full_refresh`
> **Note:** Update the `_fetch_and_merge_issues(...)` call inside the try/except block (added in step 2) to unpack the new tuple return value.
- Parse `last_full_refresh` from `cache_data` (same pattern as `last_checked`)
- Pass it to `_fetch_and_merge_issues()`
- After a successful fetch, determine if it was a full refresh and set `cache_data["last_full_refresh"] = format_for_cache(now)` only for full refreshes

**ALGORITHM for determining if full refresh occurred:**
```
# _fetch_and_merge_issues returns (fresh_issues, was_full_refresh)
fresh_issues, was_full_refresh = _fetch_and_merge_issues(...)
if was_full_refresh:
    cache_data["last_full_refresh"] = format_for_cache(now)
cache_data["last_checked"] = format_for_cache(now)
```

Change `_fetch_and_merge_issues` return type from `List[IssueData]` to `tuple[List[IssueData], bool]` where the bool indicates whether a full refresh was performed.

### Test code
Add tests in `tests/utils/github_operations/test_issue_cache.py`:

**`test_last_full_refresh_in_cache_data`**
- Create cache with `last_full_refresh` field
- Save and reload — verify field persists

**`test_full_refresh_updates_last_full_refresh`**
- Set up cache with no `last_full_refresh` (or old one)
- Trigger a full refresh (e.g. `force_refresh=True` or `last_checked=None`)
- Verify `last_full_refresh` is set to current time in saved cache

**`test_incremental_refresh_does_not_update_last_full_refresh`**
- Set up cache with recent `last_checked` and recent `last_full_refresh`
- Trigger incremental refresh (cache age > 50s but < 24h)
- Verify `last_full_refresh` is unchanged in saved cache

**`test_full_refresh_triggers_when_last_full_refresh_is_old`**
- Set up cache with recent `last_checked` (1 minute ago) but old `last_full_refresh` (25 hours ago)
- Call `get_all_cached_issues()`
- Verify `_list_issues_no_error_handling()` was called with `state="open"` (full refresh fetches only open issues) not `state="all"` with `since=` (incremental fetches all states since last check)

**`test_load_cache_without_last_full_refresh_field`**
- Load a cache file that doesn't have the `last_full_refresh` field (backward compatibility)
- Verify it defaults to `None` and triggers a full refresh

## HOW
- `_fetch_and_merge_issues` gains a `last_full_refresh` parameter and returns `tuple[List[IssueData], bool]`
- `get_all_cached_issues` parses, passes, and conditionally updates `last_full_refresh`
- `_load_cache_file` reads the new field with `.get()` defaulting to `None` (backward compatible)
- Existing cache files without `last_full_refresh` will get `None`, triggering a full refresh on first run — this is the desired behavior

## DATA
- **`CacheData`:** Gains `last_full_refresh: Optional[str]` field
- **`_fetch_and_merge_issues` return:** Changes from `List[IssueData]` to `tuple[List[IssueData], bool]`
- **Cache file format:** Gains optional `last_full_refresh` key (backward compatible)

## LLM Prompt
```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_3.md.

In src/mcp_coder/utils/github_operations/issues/cache.py:
1. Add last_full_refresh to CacheData TypedDict
2. Update _load_cache_file() to read last_full_refresh (default None)
3. Update _fetch_and_merge_issues() to accept last_full_refresh param, use it for
   the full refresh threshold, and return tuple[List[IssueData], bool]
4. Update get_all_cached_issues() to parse/pass/update last_full_refresh

Add tests in tests/utils/github_operations/test_issue_cache.py:
1. test_last_full_refresh_in_cache_data
2. test_full_refresh_updates_last_full_refresh
3. test_incremental_refresh_does_not_update_last_full_refresh
4. test_full_refresh_triggers_when_last_full_refresh_is_old
5. test_load_cache_without_last_full_refresh_field

Run all quality checks after changes. Commit as one unit.
```
