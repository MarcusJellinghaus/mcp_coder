# Issue #257: Refactor Cache Logic to github_operations

## Overview

Move caching logic from `coordinator/core.py` to `utils/github_operations/issue_cache.py` and relocate the test file to match the new code location.

## Architectural Changes

### Before
```
src/mcp_coder/cli/commands/coordinator/
└── core.py                          # Contains cache logic (misplaced)

tests/utils/
└── test_coordinator_cache.py        # Tests for cache (misplaced)
```

### After
```
src/mcp_coder/utils/github_operations/
├── issue_cache.py                   # NEW: Cache logic (proper location)
└── __init__.py                      # Updated exports

src/mcp_coder/cli/commands/coordinator/
├── core.py                          # Thin wrapper + _filter_eligible_issues
└── __init__.py                      # Updated exports

tests/utils/github_operations/
├── test_issue_cache.py              # MOVED: All cache tests
└── conftest.py                      # Updated with cache fixtures (merged)
```

## Design Rationale

1. **Caching is infrastructure, not presentation**: The CLI coordinator layer should orchestrate workflows, not implement caching mechanisms. Cache logic belongs in the infrastructure layer (`utils`).

2. **Grouping with related code**: Issue caching is part of GitHub operations - it caches issue data from GitHub API. Placing it alongside `issue_manager.py` makes architectural sense.

3. **Single test file approach (KISS)**: Rather than splitting into 4-5 test files, keep all cache tests in one file. The main problem is *location*, not size.

4. **Split approach for `get_cached_eligible_issues`**: 
   - ~90% (caching logic) moves to `issue_cache.py` as `get_all_cached_issues()`
   - ~10% (filtering wrapper) stays in `coordinator/core.py` as `get_cached_eligible_issues()`
   - **No callback parameters needed** - clean layer separation

5. **`_filter_eligible_issues` stays in coordinator**: This function uses `PRIORITY_ORDER` from `command_templates.py` and loads label config from `mcp_coder.config` - it's coordinator-specific business logic.

## Files to Create

| File | Description |
|------|-------------|
| `src/mcp_coder/utils/github_operations/issue_cache.py` | New module with cache logic |
| `tests/utils/github_operations/test_issue_cache.py` | Relocated cache tests |

## Files to Modify

| File | Changes |
|------|---------|
| `src/mcp_coder/utils/github_operations/__init__.py` | Add issue_cache exports |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Import from issue_cache, keep thin wrapper |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Update exports |
| `tests/utils/github_operations/conftest.py` | Merge cache test fixtures |

## Files to Delete

| File | Reason |
|------|--------|
| `tests/utils/test_coordinator_cache.py` | Moved to `tests/utils/github_operations/test_issue_cache.py` |

## Functions Being Moved to `issue_cache.py`

| Function | Purpose |
|----------|---------|
| `CacheData` | TypedDict for cache structure |
| `_load_cache_file()` | Load cache from disk |
| `_save_cache_file()` | Save cache to disk (atomic write) |
| `_get_cache_file_path()` | Get cache file path for a repo |
| `_log_cache_metrics()` | Debug logging for cache operations |
| `_log_stale_cache_entries()` | Log when cached data is stale |
| `_update_issue_labels_in_cache()` | Update labels after dispatch |
| `get_all_cached_issues()` | **NEW**: Main cache function (returns all cached issues) |

## Functions Staying in `coordinator/core.py`

| Function | Reason |
|----------|--------|
| `_filter_eligible_issues()` | Uses `PRIORITY_ORDER` and coordinator-specific label config loading |
| `get_cached_eligible_issues()` | Thin wrapper: calls `get_all_cached_issues()` + `_filter_eligible_issues()` |
| `get_eligible_issues()` | Coordinator-specific fallback logic |

## Tool Compatibility

- **Import Linter**: No config changes needed
  - Layered architecture allows `cli` → `utils` imports
  - `github_operations` already exists as allowed dependency
  
- **Tach**: No config changes needed
  - `mcp_coder.cli` already has `mcp_coder.utils` in `depends_on`
  - Tests module has broad access to all mcp_coder modules

## Constraints

- **No functional changes**: Only move code and adjust imports
- **Preserve test coverage**: All existing test logic maintained
- **Maintain backwards compatibility**: Re-export from coordinator `__init__.py` for any external consumers
- **Verify tests before deletion**: Run moved tests before deleting original test file
