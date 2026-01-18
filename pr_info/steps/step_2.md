# Step 2: Update coordinator/core.py to Use issue_cache

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 2: Update `src/mcp_coder/cli/commands/coordinator/core.py` to import from 
the new issue_cache module and create thin wrappers.

Changes needed:
1. Remove the moved functions (CacheData, _load_cache_file, _save_cache_file, etc.)
2. Import these functions from `mcp_coder.utils.github_operations.issue_cache`
3. Keep `_filter_eligible_issues` in place (it's coordinator-specific)
4. Keep `get_eligible_issues` in place (it's the fallback)
5. Rewrite `get_cached_eligible_issues` as a thin wrapper that:
   - Calls `get_all_cached_issues()` from issue_cache
   - Applies `_filter_eligible_issues()` to the result
   - Falls back to `get_eligible_issues()` on error

The late-binding pattern (`_get_coordinator()`) is no longer needed for cache functions.
```

## WHERE

**Modify**: `src/mcp_coder/cli/commands/coordinator/core.py`

## WHAT

### Remove These (moved to issue_cache.py)
- `CacheData` TypedDict
- `_load_cache_file()`
- `_save_cache_file()`
- `_get_cache_file_path()`
- `_log_cache_metrics()`
- `_log_stale_cache_entries()`
- `_update_issue_labels_in_cache()`
- Most of `get_cached_eligible_issues()` body (replaced with thin wrapper)

### Add Imports
```python
from ....utils.github_operations.issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,
    get_all_cached_issues,
)
```

**Note:** Only import public API and functions needed by coordinator. Private helpers 
(`_get_cache_file_path`, `_load_cache_file`, etc.) stay internal to `issue_cache.py`.

### Update workflow_constants.py Import

Update `workflow_constants.py` to import `DUPLICATE_PROTECTION_SECONDS` from the shared location:
```python
# In workflow_constants.py, change:
# DUPLICATE_PROTECTION_SECONDS = 50
# To:
from ....constants import DUPLICATE_PROTECTION_SECONDS
```

### Keep in Place (unchanged)
- `_filter_eligible_issues()` - coordinator-specific logic
- `get_eligible_issues()` - coordinator-specific logic

### New Thin Wrapper

```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection.
    
    Thin wrapper that:
    1. Calls get_all_cached_issues() for cache operations
    2. Filters results using _filter_eligible_issues()
    3. Falls back to get_eligible_issues() on cache errors
    
    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)
    
    Returns:
        List of eligible issues (filtered by bot_pickup labels, sorted by priority)
    """
    try:
        all_issues = get_all_cached_issues(
            repo_full_name=repo_full_name,
            issue_manager=issue_manager,
            force_refresh=force_refresh,
            cache_refresh_minutes=cache_refresh_minutes,
        )
        return _filter_eligible_issues(all_issues)
    except Exception as e:
        logger.warning(
            f"Cache error for {repo_full_name}: {e}, falling back to direct fetch"
        )
        return get_eligible_issues(issue_manager)
```

## HOW

The coordinator module becomes a thin wrapper that:
1. Imports cache implementation from `issue_cache`
2. Keeps coordinator-specific business logic (`_filter_eligible_issues`, `get_eligible_issues`)
3. Provides error handling and fallback behavior
4. Maintains the same public API for backwards compatibility

### Remove Late Binding for Cache Functions

The `_get_coordinator()` pattern is no longer needed for cache functions since they're
now imported directly. However, keep it for `_filter_eligible_issues` calls within
the coordinator (if any internal calls exist).

## ALGORITHM

```
# Thin wrapper pattern:
1. Try to get all cached issues from issue_cache module
2. Filter using coordinator's _filter_eligible_issues
3. On any error, fall back to get_eligible_issues (direct API fetch)
```

## DATA

No data structure changes - the API remains identical.

## TESTS

Existing tests should continue to work because:
- The public API hasn't changed
- Tests will patch at the new location: `mcp_coder.utils.github_operations.issue_cache.<function>`
