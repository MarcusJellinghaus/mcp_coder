# Step 2: Implement Cache Label Update Function

## LLM Prompt
```
Review the summary at pr_info/steps/summary.md for context on Issue #231 coordinator cache invalidation.

Implement the _update_issue_labels_in_cache() function in src/mcp_coder/cli/commands/coordinator.py to make the tests from Step 1 pass.

The function should update issue labels in the existing cache after successful workflow dispatch, following KISS principles and existing codebase patterns.

Key requirements:
- Update labels in-place (remove old, add new)
- Handle errors gracefully (log warnings, don't break workflow)
- Follow existing cache file operations patterns
- Use existing helper functions (_load_cache_file, _save_cache_file, etc.)
- Maintain cache structure integrity
```

## WHERE: File Location
- **Primary**: `src/mcp_coder/cli/commands/coordinator.py`
- **Section**: Add after existing cache helper functions (around line 400)

## WHAT: Function Implementation

### Main Function
```python
def _update_issue_labels_in_cache(
    repo_full_name: str,
    issue_number: int,
    old_label: str,
    new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch."""
```

### Helper Function (optional)
```python
def _update_issue_labels_list(
    labels: List[str], 
    old_label: str, 
    new_label: str
) -> List[str]:
    """Update labels list by removing old and adding new label."""
```

## HOW: Integration Points

### Imports
No additional imports needed - use existing:
```python
from ...utils.github_operations.github_utils import RepoIdentifier
from pathlib import Path
import logging
```

### Dependencies
Uses existing helper functions:
- `RepoIdentifier.from_full_name()`
- `_get_cache_file_path()`
- `_load_cache_file()`
- `_save_cache_file()`
- `logger.debug()`, `logger.warning()`

## ALGORITHM: Core Implementation Logic

### Main Function Logic
```
1. Parse repo_full_name into RepoIdentifier
2. Load existing cache data using _load_cache_file()
3. Find target issue in cache["issues"][str(issue_number)]
4. Update issue labels: remove old_label, add new_label
5. Save updated cache using _save_cache_file()
6. Log success/failure appropriately
```

### Label Update Logic
```
1. Get current labels list from issue
2. Remove old_label if present (avoid KeyError)
3. Add new_label if not already present (avoid duplicates)
4. Update issue["labels"] with modified list
5. Preserve all other issue metadata unchanged
```

## ALGORITHM: Detailed Implementation

### Error Handling Strategy
```python
def _update_issue_labels_in_cache(
    repo_full_name: str,
    issue_number: int,
    old_label: str,
    new_label: str
) -> None:
    """Update issue labels in cache after successful dispatch.
    
    Updates the cached issue labels to reflect GitHub label changes made
    during workflow dispatch. This prevents stale cache data from causing
    duplicate dispatches within the 1-minute duplicate protection window.
    
    Args:
        repo_full_name: Repository in "owner/repo" format (e.g., "anthropics/claude-code")
        issue_number: GitHub issue number to update
        old_label: Label to remove from cached issue
        new_label: Label to add to cached issue
        
    Note:
        Cache update failures are logged as warnings but do not interrupt
        the main workflow. The next cache refresh will fetch correct data
        from GitHub API.
    """
    try:
        # Step 1: Parse repository identifier
        repo_identifier = RepoIdentifier.from_full_name(repo_full_name)
        
        # Step 2: Load existing cache
        cache_file_path = _get_cache_file_path(repo_identifier)
        cache_data = _load_cache_file(cache_file_path)
        
        # Step 3: Find target issue in cache
        issue_key = str(issue_number)
        if issue_key not in cache_data["issues"]:
            logger.debug(f"Issue #{issue_number} not found in cache, skipping update")
            return
            
        # Step 4: Update issue labels
        issue = cache_data["issues"][issue_key]
        current_labels = list(issue.get("labels", []))
        
        # Remove old label if present
        if old_label in current_labels:
            current_labels.remove(old_label)
            
        # Add new label if not already present  
        if new_label and new_label not in current_labels:
            current_labels.append(new_label)
            
        # Update cached issue
        issue["labels"] = current_labels
        cache_data["issues"][issue_key] = issue
        
        # Step 5: Save updated cache
        save_success = _save_cache_file(cache_file_path, cache_data)
        if save_success:
            logger.debug(
                f"Updated cache for issue #{issue_number}: '{old_label}' → '{new_label}'"
            )
        else:
            logger.warning(
                f"Failed to save cache update for issue #{issue_number}"
            )
            
    except ValueError as e:
        # Repository parsing or cache structure errors
        logger.warning(
            f"Cache update failed for issue #{issue_number}: {e}"
        )
    except Exception as e:
        # Any unexpected errors - don't break main workflow
        logger.warning(
            f"Unexpected error updating cache for issue #{issue_number}: {e}"
        )
```

## DATA: Return Values and Structures

### Function Signature
```python
def _update_issue_labels_in_cache(
    repo_full_name: str,    # "owner/repo" 
    issue_number: int,      # GitHub issue number
    old_label: str,         # Label to remove
    new_label: str          # Label to add
) -> None:                  # Updates cache file in-place
```

### Cache Structure (Unchanged)
```python
{
    "last_checked": "2025-01-03T10:30:00Z",  # Unchanged
    "issues": {
        "123": {
            "number": 123,
            "state": "open",
            "labels": ["status-03:planning", "bug"],  # UPDATED
            "updated_at": "2025-01-03T09:00:00Z",
            # ... all other fields preserved
        }
    }
}
```

### Logging Output
```
# Success case
DEBUG: Updated cache for issue #123: 'status-02:awaiting-planning' → 'status-03:planning'

# Error cases  
WARNING: Cache update failed for issue #123: Invalid repository format
WARNING: Failed to save cache update for issue #123
DEBUG: Issue #123 not found in cache, skipping update
```

## Implementation Notes

### Design Considerations
1. **Graceful Degradation**: Cache failures don't break dispatch workflow
2. **Idempotent**: Safe to call multiple times with same parameters
3. **Conservative**: Only updates what changed, preserves all other data
4. **Consistent**: Uses same error handling patterns as existing cache functions

### Code Quality
- Follow existing function naming (`_private_function`)
- Use existing logging patterns (`logger.debug`, `logger.warning`)
- Maintain consistent docstring style
- Handle edge cases (empty labels, missing issues)
- No breaking changes to cache structure

### Performance Considerations
- Minimal overhead: single file read/write per update
- No additional API calls required
- Atomic file operations via existing `_save_cache_file()`
- Early return for missing issues (no unnecessary work)