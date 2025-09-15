# Step 4: Test & Implement get_unstaged_changes()

## Goal
Add function to detect modified and untracked files using TDD approach.

## Function Signature
```python
def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]
```

## Test Scenarios to Write
- Test with no changes (clean repo)
- Test with only modified files
- Test with only untracked files  
- Test with both modified and untracked files
- Test error cases (not git repo, git command failures)
- Test edge cases (ignored files, symlinks, etc.)

## Expected Behavior
```python
# Return structure:
{
    "modified": list[str],    # Files tracked but modified
    "untracked": list[str]    # New files not tracked by git
}
```
- Returns empty dict if not a git repository (logs error)
- File paths should be relative to project root
- Separate modified vs untracked for clear user decisions

## Implementation Guidelines
- Use existing `is_git_repository()` for validation
- Use GitPython to detect file status
- Return structured data as specified in Decisions.md
- Handle errors gracefully with appropriate logging

## Done When
- All tests pass
- Function correctly distinguishes modified vs untracked files
- Error handling behaves as expected
- Return structure matches specification

## TDD Approach
1. Write failing tests for all scenarios including edge cases
2. Implement minimal code to make tests pass
3. Refactor for clarity and performance
