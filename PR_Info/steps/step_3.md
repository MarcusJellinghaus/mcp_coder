# Step 3: Implement get_main_branch_name Function

## Objective
Implement `get_main_branch_name()` function to detect the main branch following modern Git conventions.

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Add after `get_current_branch_name()` function
- **Integration**: Follow same patterns as other functions in module

## WHAT
### Function Signature  
```python
def get_main_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the main branch (main or master).

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        str: Name of main branch ("main" or "master") if found, None otherwise
        
    Note:
        - Checks for "main" first (modern default)
        - Falls back to "master" (legacy default)  
        - Returns None if neither exists
        - Returns None if not a git repository
    """
```

## HOW
### Integration Points
- **Validation**: Use existing `is_git_repository(project_dir)` 
- **Git Operations**: Use `repo.heads` to check branch existence
- **Logging**: Follow existing `logger.debug()` pattern
- **Error Handling**: Return `None` on any error, no exceptions

## ALGORITHM  
### Implementation Pseudocode
```
1. Check if project_dir is git repository, return None if not
2. Create Repo object from project_dir
3. Check if 'main' branch exists in repo.heads, return "main" if yes
4. Check if 'master' branch exists in repo.heads, return "master" if yes  
5. Return None if neither exists
```

## DATA
### Return Values
- **Modern repo**: `"main"`
- **Legacy repo**: `"master"`  
- **No main branch**: `None`
- **Invalid repo**: `None`
- **Any error**: `None`

### Branch Detection Logic
- Priority: `"main"` > `"master"` > `None`
- Uses: `repo.heads["branch_name"]` existence check
- Handles: `KeyError` when branch doesn't exist

## LLM Prompt for Implementation
```
Based on summary.md, step_1.md, and step_2.md, implement Step 3 by adding the get_main_branch_name function to src/mcp_coder/utils/git_operations.py.

This function should:
1. Use existing validation and error handling patterns
2. Check for "main" branch first (modern Git default)  
3. Fall back to "master" branch (legacy Git default)
4. Return None if neither exists or any error occurs
5. Use repo.heads to check branch existence

Follow the same code style and patterns as get_current_branch_name. The function should pass the tests written in Step 1.
```
