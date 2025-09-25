# Step 2: Implement get_current_branch_name Function

## Objective  
Implement `get_current_branch_name()` function to pass the tests written in Step 1.

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Add after existing functions (before `git_push` function)
- **Integration**: Follow existing function patterns in the module

## WHAT
### Function Signature
```python
def get_current_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the current active branch.

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        str: Name of current branch if successful, None otherwise
        
    Note:
        - Returns None for detached HEAD state
        - Returns None if not a git repository  
        - Returns None if any error occurs
    """
```

## HOW  
### Integration Points
- **Import**: No new imports needed (uses existing `Repo`, `InvalidGitRepositoryError`)
- **Validation**: Use existing `is_git_repository(project_dir)` check
- **Logging**: Use existing `logger.debug()` pattern  
- **Error Handling**: Follow existing pattern - return `None` on any error

## ALGORITHM
### Implementation Pseudocode
```
1. Check if project_dir is git repository, return None if not
2. Create Repo object from project_dir  
3. Get repo.active_branch.name
4. Return branch name string
5. Catch any exceptions and return None
```

## DATA
### Return Values
- **Success**: `str` - branch name (e.g., `"main"`, `"feature/new-ui"`, `"bugfix-123"`)
- **Detached HEAD**: `None`
- **Invalid repo**: `None` 
- **Any error**: `None`

### Error Handling
- `InvalidGitRepositoryError` → `None`
- `TypeError` (detached HEAD) → `None`  
- `Exception` → `None`

## LLM Prompt for Implementation
```
Based on summary.md and step_1.md, implement Step 2 by adding the get_current_branch_name function to src/mcp_coder/utils/git_operations.py.

This function should:
1. Use the existing is_git_repository() validation
2. Follow the same error handling pattern as other functions (return None on any error)  
3. Use the same logging pattern (logger.debug)
4. Handle detached HEAD state gracefully
5. Use repo.active_branch.name to get the current branch

The function should pass the tests written in Step 1. Keep it simple and consistent with existing code patterns.
```
