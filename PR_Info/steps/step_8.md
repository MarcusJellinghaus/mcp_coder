# Step 8: Test & Implement commit_staged_files()

## Goal
Add core commit function for creating commits from staged content using TDD approach.

## Function Signature
```python
def commit_staged_files(message: str, project_dir: Path) -> CommitResult
```

## Test Scenarios to Write
- Test successful commit with staged files
- Test commit attempt with no staged files
- Test commit with empty/None/invalid commit message
- Test commit with various message types (simple, multiline, special chars)
- Test error cases (not git repo, git commit failures)
- Test CommitResult structure and content

## Expected Behavior
```python
# Return CommitResult:
{
    "success": bool,                    # True if commit successful
    "commit_hash": str | None,          # Git commit SHA (first 7 chars)
    "error": str | None                # Error message if failed
}
```
- Only commits currently staged files
- Requires non-empty commit message
- Returns commit hash on success
- Provides error details on failure

## Implementation Guidelines
- Use existing `is_git_repository()` for validation
- Use `get_staged_changes()` to verify there's content to commit
- Use GitPython for commit operations
- Return CommitResult structure as specified in Decisions.md
- Handle all error scenarios gracefully

## Done When
- All tests pass
- Function creates commits correctly
- CommitResult structure matches specification
- Error handling covers all scenarios

## TDD Approach
1. Write tests for successful commit scenarios
2. Write tests for all error conditions and edge cases
3. Implement commit logic with proper validation
4. Refactor for clarity and robust error handling
