# Step 6: Test & Implement stage_specific_files()

## Goal
Add function to stage specific files for commit using TDD approach.

## Function Signature
```python
def stage_specific_files(files: list[Path], project_dir: Path) -> bool
```

## Test Scenarios to Write
- Test staging specific existing files
- Test staging non-existent files (should handle gracefully)
- Test staging files outside repository (should reject)
- Test staging already staged files (should be no-op)
- Test staging mix of valid/invalid files
- Test with relative vs absolute file paths
- Test error cases (not git repo, permission issues, git failures)

## Expected Behavior
- Returns `True` if all specified files staged successfully
- Returns `False` if any files couldn't be staged or other errors
- Handles both absolute and relative file paths
- Validates files exist and are within project directory
- Logs appropriate warnings/errors for failed operations

## Implementation Guidelines
- Use existing `is_git_repository()` for validation
- Convert file paths to relative paths from project_dir
- Use GitPython's staging operations
- Handle path validation and conversion
- Follow existing error handling patterns

## Done When
- All tests pass
- Function correctly stages valid files
- Proper error handling for invalid scenarios
- Path handling works for both relative and absolute paths

## TDD Approach
1. Write tests for all file path scenarios (valid, invalid, mixed)
2. Write tests for error conditions and edge cases
3. Implement file validation and staging logic
4. Refactor for robustness and clarity
