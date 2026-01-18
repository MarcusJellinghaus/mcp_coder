# Step 3: Update Module Exports

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 3: Update the module exports in both `__init__.py` files.

1. Update `src/mcp_coder/utils/github_operations/__init__.py`:
   - Add exports for CacheData, get_all_cached_issues, and the cache helper functions

2. Update `src/mcp_coder/cli/commands/coordinator/__init__.py`:
   - Keep all existing exports (for backwards compatibility)
   - The cache functions are now imported from core.py which imports from issue_cache
   - Verify exports still work

Verify that existing code continues to work by checking that all __all__ exports resolve correctly.
```

## WHERE

**Modify**: 
- `src/mcp_coder/utils/github_operations/__init__.py`
- `src/mcp_coder/cli/commands/coordinator/__init__.py` (verify, likely minimal changes)

## WHAT

### github_operations/__init__.py - Add Exports

```python
from .issue_cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_cache_metrics,
    _log_stale_cache_entries,
    _save_cache_file,
    _update_issue_labels_in_cache,
    get_all_cached_issues,
)

# Update __all__ to include:
__all__ = [
    # ... existing exports ...
    # Cache exports
    "CacheData",
    "get_all_cached_issues",
    "_get_cache_file_path",
    "_load_cache_file",
    "_save_cache_file",
    "_log_cache_metrics",
    "_log_stale_cache_entries",
    "_update_issue_labels_in_cache",
]
```

### coordinator/__init__.py - Verify Exports

The coordinator `__init__.py` imports from `core.py`:
```python
from .core import (
    CacheData,
    _filter_eligible_issues,
    _get_cache_file_path,
    # ... etc
)
```

Since `core.py` now imports these from `issue_cache` and re-exports them, the coordinator `__init__.py` should work unchanged.

**Verify**: Run `python -c "from mcp_coder.cli.commands.coordinator import CacheData, get_cached_eligible_issues"` to confirm.

## HOW

The export chain is:
```
issue_cache.py (implementation)
    ↓
github_operations/__init__.py (exports for direct use)
    ↓
coordinator/core.py (imports + thin wrapper)
    ↓
coordinator/__init__.py (re-exports from core.py)
```

This maintains backwards compatibility - code importing from `coordinator` still works.

## ALGORITHM

```
# Export update pattern:
1. Add imports to github_operations/__init__.py
2. Add to __all__ list
3. Verify coordinator/__init__.py still works (no changes expected)
4. Run quick import check to verify both paths work
```

## DATA

No data changes.

## TESTS

Run quick verification:
```bash
python -c "from mcp_coder.utils.github_operations import CacheData, get_all_cached_issues; print('github_operations OK')"
python -c "from mcp_coder.cli.commands.coordinator import CacheData, get_cached_eligible_issues; print('coordinator OK')"
```
