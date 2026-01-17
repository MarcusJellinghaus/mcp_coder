# Step 2: Update coordinator/core.py to Use issue_cache

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 2: Update `src/mcp_coder/cli/commands/coordinator/core.py` to import from the new issue_cache module.

Changes needed:
1. Remove the moved functions (CacheData, _load_cache_file, _save_cache_file, etc.)
2. Import these functions from `mcp_coder.utils.github_operations.issue_cache`
3. Keep `_filter_eligible_issues` in place (it's coordinator-specific)
4. Update `get_cached_eligible_issues` to be a thin wrapper that calls the issue_cache version with appropriate callbacks
5. Update `_update_issue_labels_in_cache` to be a thin wrapper if needed

The late-binding pattern (`_get_coordinator()`) should be simplified since we're now using direct imports from the lower layer.
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

### Add Imports
```python
from ....utils.github_operations.issue_cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    get_cached_eligible_issues as _get_cached_eligible_issues_impl,
    _update_issue_labels_in_cache as _update_issue_labels_in_cache_impl,
)
```

### Keep in Place
- `_filter_eligible_issues()` - coordinator-specific logic
- `get_eligible_issues()` - coordinator-specific logic

### Update wrapper functions

```python
def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection."""
    return _get_cached_eligible_issues_impl(
        repo_full_name=repo_full_name,
        issue_manager=issue_manager,
        filter_fn=_filter_eligible_issues,
        fallback_fn=get_eligible_issues,
        force_refresh=force_refresh,
        cache_refresh_minutes=cache_refresh_minutes,
    )

def _update_issue_labels_in_cache(
    repo_full_name: str, issue_number: int, old_label: str, new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch."""
    _update_issue_labels_in_cache_impl(repo_full_name, issue_number, old_label, new_label)
```

## HOW

The coordinator module becomes a thin wrapper that:
1. Imports the implementation from `issue_cache`
2. Provides the coordinator-specific callbacks (`_filter_eligible_issues`, `get_eligible_issues`)
3. Maintains the same public API for backwards compatibility

## ALGORITHM

```
# Wrapper pattern:
1. Import implementation from issue_cache
2. Define local _filter_eligible_issues (coordinator logic)
3. Define local get_eligible_issues (coordinator logic)
4. Wrap get_cached_eligible_issues to pass callbacks
5. Wrap _update_issue_labels_in_cache (direct delegate)
```

## DATA

No data structure changes - the API remains identical.

## TESTS

Existing tests should continue to work because:
- The public API hasn't changed
- Tests patch at `mcp_coder.cli.commands.coordinator.<function>` 
- Re-exports in `coordinator/__init__.py` will be updated in Step 3
