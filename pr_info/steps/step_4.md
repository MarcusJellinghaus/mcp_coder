# Step 4: Code Review Fixes

## LLM Prompt
```
Review the summary at pr_info/steps/summary.md and decisions at pr_info/steps/Decisions.md for context on Issue #231 coordinator cache invalidation.

Implement fixes identified during code review for the _update_issue_labels_in_cache() function. These are minor adjustments to align log messages between implementation and tests, plus a pyproject.toml cleanup.

Focus on:
- Aligning log message formats with test expectations
- Removing redundant mypy override
- Maintaining existing functionality
```

## WHERE: File Locations
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Secondary**: `pyproject.toml`

## WHAT: Changes Required

### 1. Update "issue not found" log message (coordinator.py ~line 536)
```python
# BEFORE:
logger.debug(f"Issue #{issue_number} not found in cache, skipping update")

# AFTER:
logger.debug(f"Issue #{issue_number} not found in cache for {repo_full_name}, skipping update")
```

### 2. Update successful update log message (coordinator.py ~line 556-558)
```python
# BEFORE:
logger.debug(
    f"Updated cache for issue #{issue_number}: '{old_label}' → '{new_label}'"
)

# AFTER:
logger.debug(
    f"Updated issue #{issue_number} labels in cache: '{old_label}' → '{new_label}'"
)
```

### 3. Update save failure log message (coordinator.py ~line 559-560)
```python
# BEFORE:
logger.warning(f"Failed to save cache update for issue #{issue_number}")

# AFTER:
logger.warning(f"Cache update failed for issue #{issue_number}: save operation failed")
```

### 4. Remove redundant mypy override (pyproject.toml)
```toml
# REMOVE these lines (~lines 136-138):
[[tool.mypy.overrides]]
module = ["requests"]
ignore_missing_imports = true
```

## HOW: Integration Points

No new imports or integration points needed. These are in-place text changes.

## ALGORITHM: N/A

These are simple text replacements with no logic changes.

## DATA: N/A

No changes to function signatures, return values, or data structures.

## Success Criteria

### Test Alignment
- `test_update_issue_labels_missing_issue` passes with new log message format
- `test_update_issue_labels_logging` passes with new log message format
- `test_update_issue_labels_file_permission_error` passes with new log message format

### Quality Checks
- All existing tests continue to pass
- mypy passes without the redundant override (types-requests provides coverage)
- pylint passes with no new warnings

## Implementation Notes

### Log Message Changes Summary
| Location | Before | After |
|----------|--------|-------|
| Issue not found | `"Issue #X not found in cache, skipping update"` | `"Issue #X not found in cache for owner/repo, skipping update"` |
| Successful update | `"Updated cache for issue #X: ..."` | `"Updated issue #X labels in cache: ..."` |
| Save failure | `"Failed to save cache update for issue #X"` | `"Cache update failed for issue #X: save operation failed"` |

### pyproject.toml Cleanup
The `types-requests>=2.28.0` dependency provides type stubs for the requests library, making the mypy override redundant. Removing the override allows mypy to use the type stubs for better type checking.
