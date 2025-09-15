# Step 3: Test & Implement get_staged_changes()

## Goal
Add function to detect files currently staged for commit using TDD approach.

## Function Signature
```python
def get_staged_changes(project_dir: Path) -> list[str]
```

## Test Scenarios to Write
- Test with no staged files (empty repo, clean repo)
- Test with some staged files 
- Test with mixed staged/unstaged files
- Test error cases (not git repo, git command failures)
- Test with various file types and paths

## Expected Behavior
- Returns list of file paths currently staged for commit
- Returns empty list if no staged files
- Returns empty list if not a git repository (logs error)
- File paths should be relative to project root

## Implementation Guidelines
- Use existing `is_git_repository()` for validation
- Use GitPython's git commands for detecting staged files
- Handle errors gracefully with appropriate logging
- Follow existing code patterns in the module

## Done When
- All tests pass
- Function works correctly with real git repositories
- Error handling behaves as expected
- Code follows existing patterns

## TDD Approach
1. Write failing tests for all scenarios
2. Implement minimal code to make tests pass
3. Refactor for clarity and consistency
