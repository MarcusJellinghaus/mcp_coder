# Step 5: Test & Implement get_full_status()

## Goal
Add comprehensive status function that combines staged, modified, and untracked info in one call.

## Function Signature
```python
def get_full_status(project_dir: Path) -> dict[str, list[str]]
```

## Test Scenarios to Write
- Test comprehensive status with various file combinations
- Test consistency with individual functions (`get_staged_changes`, `get_unstaged_changes`)
- Test performance (should be efficient, not multiple git calls)
- Test error cases (not git repo)
- Test with large repositories (basic performance validation)

## Expected Behavior
```python
# Return structure:
{
    "staged": list[str],      # Files staged for commit
    "modified": list[str],    # Files tracked but modified  
    "untracked": list[str]    # New files not tracked by git
}
```
- Returns empty dict if not a git repository (logs error)
- Should be consistent with calling individual status functions
- More efficient than separate calls

## Implementation Guidelines
- Reuse logic from `get_staged_changes()` and `get_unstaged_changes()` OR
- Implement efficiently with single git status call
- Ensure consistency with individual functions
- Handle errors gracefully

## Done When
- All tests pass
- Function provides comprehensive status efficiently
- Results consistent with individual status functions
- Performance acceptable for typical repositories

## TDD Approach
1. Write tests covering all status combinations
2. Write tests verifying consistency with existing functions
3. Implement efficiently (optimize git calls)
4. Refactor for clarity and maintainability
