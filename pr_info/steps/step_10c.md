# Step 10c: Update Parent `__init__.py` (Remove Issue Exports)

## LLM Prompt
```
Implement Step 10c of Issue #306 (see pr_info/steps/summary.md for context).
Update the parent github_operations/__init__.py to REMOVE all issue-related exports.
This implements Decision #1: Strict clean break - no re-exports from parent.
Run verification checks after completion.
```

## WHERE

- **Modify**: `src/mcp_coder/utils/github_operations/__init__.py`

## WHAT

### Before (current state)
```python
from .issue_branch_manager import (
    BranchCreationResult,
    IssueBranchManager,
    generate_branch_name_from_issue,
)
from .issue_cache import (
    CacheData,
    _get_cache_file_path,
    _load_cache_file,
    _log_stale_cache_entries,
    _save_cache_file,
    get_all_cached_issues,
    update_issue_labels_in_cache,
)
from .issue_manager import (
    CommentData,
    EventData,
    IssueData,
    IssueEventType,
    IssueManager,
    LabelData,
)
```

### After (clean break)
```python
# Issue-related imports REMOVED per Decision #1
# Consumers must import from: mcp_coder.utils.github_operations.issues
```

### `__all__` Update

Remove these from `__all__`:
- `IssueEventType`
- `IssueData`
- `CommentData`
- `LabelData`
- `EventData`
- `IssueManager`
- `IssueBranchManager`
- `BranchCreationResult`
- `generate_branch_name_from_issue`
- `CacheData`
- `get_all_cached_issues`
- `update_issue_labels_in_cache`
- `_get_cache_file_path`
- `_load_cache_file`
- `_log_stale_cache_entries`
- `_save_cache_file`

## HOW

1. Open `github_operations/__init__.py`
2. Delete all import lines from `issue_manager`, `issue_branch_manager`, `issue_cache`
3. Remove corresponding entries from `__all__`
4. Add comment explaining the canonical import path

## VERIFICATION

After updating the parent `__init__.py`, run:
```bash
# MCP tools
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
mcp__code-checker__run_pytest_check  # Should pass - all consumers already updated
```

**Why checks should pass:** All consumers (source + tests) were updated in Steps 10a and 10b to use the new `...issues` path directly. No one imports issue types from the parent anymore.

## DEPENDENCIES
- Steps 10a and 10b must be complete

## NOTES
- This is a **breaking change** for any external code importing from parent `__init__.py`
- Per Decision #1, this is intentional - strict clean break
- Old files still exist as safety net until Step 10d
