# Step 9: Test & Implement commit_all_changes()

## Goal
Add convenience function that stages all changes and commits in one operation using TDD approach.

## Function Signature
```python
def commit_all_changes(message: str, project_dir: Path) -> CommitResult
```

## Test Scenarios to Write
- Test successful staging + commit workflow
- Test with no changes to commit (clean repo)
- Test with mix of modified and untracked files
- Test when staging succeeds but commit fails
- Test when staging fails
- Test error cases (not git repo, invalid message)
- Test CommitResult matches commit_staged_files behavior

## Expected Behavior
- Combines `stage_all_changes()` + `commit_staged_files()` workflow
- Returns same CommitResult structure as `commit_staged_files()`
- Handles errors at both staging and commit phases
- Should not commit if staging fails
- Provides appropriate error messages for each failure type

## Implementation Guidelines
- Use `stage_all_changes()` for staging phase
- Use `commit_staged_files()` for commit phase  
- Handle errors from both functions appropriately
- Return CommitResult with clear error messaging
- Focus on orchestration, not reimplementation

## Done When
- All tests pass
- Function properly orchestrates staging + commit workflow
- Error handling works for both staging and commit failures
- CommitResult consistent with commit_staged_files

## TDD Approach
1. Write tests for successful end-to-end workflows
2. Write tests for failure at each stage (staging vs commit)
3. Implement workflow orchestration with proper error handling
4. Refactor for clarity and consistent error reporting
