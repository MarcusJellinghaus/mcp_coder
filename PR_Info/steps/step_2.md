# Step 2: Implement Git Push Function

## LLM Prompt
```
Review the summary document at pr_info/steps/summary.md and Step 1 implementation for context.

Implement Step 2: Add the `git_push()` function to git_operations.py. Follow the existing patterns in the module, especially `commit_staged_files()` for error handling and return structure. Keep the implementation simple - just push to origin with current branch.

Make sure the function passes the test implemented in Step 1.
```

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Add after existing commit functions
- **Module**: Extend existing git operations module

## WHAT
- **Main Function**: `git_push(project_dir: Path) -> dict[str, any]`
- **Function Signature**: Same pattern as `CommitResult` but for push operations
- **Error Handling**: Git command errors, network issues, no remote repository

## HOW
- **Use GitPython**: Follow existing patterns with `Repo` class
- **Logging**: Use existing logger from module
- **Error Types**: Handle `GitCommandError`, `InvalidGitRepositoryError`
- **Integration**: Follow same validation patterns as other functions

## ALGORITHM
```
1. Validate project_dir is git repository
2. Create Repo object and get current branch
3. Execute git push origin <current_branch>
4. Handle success -> return {"success": True, "error": None}
5. Handle errors -> return {"success": False, "error": error_message}
```

## DATA
- **Input**: `project_dir: Path` - Path to git repository
- **Return**: `dict[str, any]` with keys:
  - `success: bool` - Whether push succeeded
  - `error: str | None` - Error message if failed, None if successful
- **Dependencies**: `git` library (already imported), `logging` (existing)

## Implementation Details

### Function Structure
```python
def git_push(project_dir: Path) -> dict[str, any]:
    """
    Push current branch to origin remote.
    
    Args:
        project_dir: Path to the project directory containing git repository
    
    Returns:
        Dictionary containing:
        - success: True if push succeeded, False otherwise
        - error: Error message if failed, None if successful
    """
```

### Error Handling Cases
- Not a git repository
- No remote named 'origin'
- Network connectivity issues
- Authentication failures
- Nothing to push (up to date)

### Integration Points
- Use existing `is_git_repository()` for validation
- Follow logging patterns from other functions
- Use same exception handling as `commit_staged_files()`
- Import statements: No new imports needed
