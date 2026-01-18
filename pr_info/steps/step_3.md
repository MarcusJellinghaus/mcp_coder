# Step 3: Update Module Exports

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 3: Update the module exports in both `__init__.py` files.

1. Update `src/mcp_coder/utils/github_operations/__init__.py`:
   - Add exports for public API only: CacheData, get_all_cached_issues, _update_issue_labels_in_cache
   - Private helpers stay internal to issue_cache.py

2. Update `src/mcp_coder/cli/commands/coordinator/__init__.py`:
   - Remove private cache function exports (they no longer exist in core.py)
   - Keep public API exports: CacheData, get_cached_eligible_issues, _update_issue_labels_in_cache

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
    _update_issue_labels_in_cache,
    get_all_cached_issues,
)

# Update __all__ to include:
__all__ = [
    # ... existing exports ...
    # Cache exports (public API only)
    "CacheData",
    "get_all_cached_issues",
    "_update_issue_labels_in_cache",
]
```

**Note:** Private helpers (`_get_cache_file_path`, `_load_cache_file`, etc.) stay internal to `issue_cache.py`.

### coordinator/__init__.py - Update Exports

**Remove these private cache function exports** (they no longer exist in `core.py`):
```python
# REMOVE from imports and __all__:
"_get_cache_file_path",
"_load_cache_file",
"_save_cache_file",
"_log_cache_metrics",
"_log_stale_cache_entries",
```

**Keep these exports** (still in `core.py`):
```python
from .core import (
    CacheData,
    _filter_eligible_issues,
    _update_issue_labels_in_cache,
    get_cached_eligible_issues,
    get_eligible_issues,
    # ... other coordinator functions ...
)
```

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
