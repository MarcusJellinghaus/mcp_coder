# Step 7: Test & Implement stage_all_changes()

## Goal
Add convenience function to stage all unstaged changes using TDD approach.

## Function Signature
```python
def stage_all_changes(project_dir: Path) -> bool
```

## Test Scenarios to Write
- Test staging all changes (modified + untracked files)
- Test with no changes to stage (clean repo)
- Test with only modified files
- Test with only untracked files
- Test with already staged content (should be no-op)
- Test error cases (not git repo, staging failures)
- Test integration with existing status functions

## Expected Behavior
- Returns `True` if all unstaged changes staged successfully
- Returns `False` if staging fails or other errors
- Should stage both modified and untracked files
- Uses existing functions to determine what needs staging
- No-op if no unstaged changes exist

## Implementation Guidelines
- Use `get_unstaged_changes()` to determine what to stage
- Use `stage_specific_files()` to perform actual staging
- Reuse existing validation and error handling
- Focus on orchestration rather than reimplementation

## Done When
- All tests pass
- Function successfully stages all types of changes
- Proper integration with existing status and staging functions
- Error handling consistent with other staging functions

## TDD Approach
1. Write tests covering various combinations of unstaged changes
2. Write tests for error scenarios and edge cases
3. Implement using existing functions (composition approach)
4. Refactor for clarity and ensure proper error propagation
