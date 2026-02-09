# Implementation Plan: Safe Delete Folder Utility (#417)

## Overview

Add a `safe_delete_folder()` utility function that safely deletes folders by handling locked files through a staging directory strategy. This addresses Windows-specific issues where files/directories can be locked by processes.

## Architectural Changes

### New Module
- **`src/mcp_coder/utils/folder_deletion.py`** - New Layer 1 utility module

### Modified Files
- **`src/mcp_coder/utils/__init__.py`** - Export `safe_delete_folder` from Layer 1
- **`src/mcp_coder/workflows/vscodeclaude/cleanup.py`** - Use `safe_delete_folder()` in `delete_session_folder()`

### New Test File
- **`tests/utils/test_folder_deletion.py`** - Mock-based test suite

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Return type | `bool` | KISS - simple success/failure, details via logging |
| Error path extraction | `error.filename` only | Simpler than regex parsing |
| Staging cleanup | Configurable parameter | Performance flexibility |
| MAX_RETRIES | Internal constant (50) | Not exposed to callers |
| Logger | Module-level | Follows codebase convention |

## Three-Step Deletion Strategy

```
1. Fast path: Try shutil.rmtree() directly
2. Handle locks: Move locked items to staging, retry
3. Housekeeping: Clean up staging directory (optional)
```

## Key Components

### Main Function
```python
def safe_delete_folder(
    path: Path | str,
    *,
    staging_dir: Path | str | None = None,
    cleanup_staging: bool = True,
) -> bool
```

### Helper Functions
- `_get_default_staging_dir()` - Returns `%TEMP%/mcp_coder_delete_staging`
- `_move_to_staging()` - Moves files/directories with UUID suffix
- `_cleanup_staging()` - Cleans old items from staging
- `_rmtree_remove_readonly()` - Handles readonly files (Python 3.12+ compatible)
- `_is_directory_empty()` - Checks if directory is empty
- `_try_delete_empty_directory()` - Handles empty locked directories

## Files to Create/Modify

### Create
1. `src/mcp_coder/utils/folder_deletion.py` (~120 lines)
2. `tests/utils/test_folder_deletion.py` (~200 lines)

### Modify
1. `src/mcp_coder/utils/__init__.py` - Add export
2. `src/mcp_coder/workflows/vscodeclaude/cleanup.py` - Use new function

## Implementation Steps

| Step | Description | TDD |
|------|-------------|-----|
| 1 | Create `folder_deletion.py` with tests | Yes |
| 2 | Update `cleanup.py` and exports | Yes |

## Success Criteria

- [ ] `safe_delete_folder()` returns `True` for non-existent folders
- [ ] Handles locked files via staging directory
- [ ] Handles empty locked directories (Windows-specific)
- [ ] `cleanup.py` uses new function
- [ ] Exported from `utils/__init__.py`
- [ ] All tests pass
