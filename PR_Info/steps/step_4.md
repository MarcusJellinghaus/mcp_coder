# Step 4: Implement get_parent_branch_name Function  

## Objective
Implement `get_parent_branch_name()` function using simple heuristic approach.

**Note**: This is the final implementation step - Steps 5-6 are removed/complete.

## WHERE
- **File**: `src/mcp_coder/utils/git_operations.py`
- **Location**: Add after `get_main_branch_name()` function  
- **Integration**: Uses `get_main_branch_name()` internally for consistency

## WHAT
### Function Signature
```python
def get_parent_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the parent branch (typically main branch).

    Args:
        project_dir: Path to the project directory containing git repository

    Returns:
        str: Name of parent branch if main branch exists, None otherwise
        
    Note:
        - Uses simple heuristic: most branches are created from main  
        - Returns main branch name ("main" or "master")
        - Returns None if no main branch found
        - Returns None if not a git repository
    """
```

## HOW
### Integration Points
- **Dependency**: Call `get_main_branch_name(project_dir)` internally
- **Validation**: Relies on `get_main_branch_name()` for git repo validation
- **Logging**: Follow existing `logger.debug()` pattern
- **Error Handling**: Return result from `get_main_branch_name()` directly

## ALGORITHM
### Implementation Pseudocode  
```
1. Call get_main_branch_name(project_dir)
2. Return the result (main branch name or None)
3. Log debug message about parent branch detection
4. No additional error handling needed (delegated)
```

## DATA
### Return Values
- **With main branch**: `"main"` or `"master"` (same as main branch)
- **No main branch**: `None`
- **Invalid repo**: `None`
- **Any error**: `None` (via delegation)

### Heuristic Logic
- **Assumption**: 90% of branches are created from main/master
- **Simplicity**: No complex merge-base or git log analysis
- **Reliability**: Leverages existing main branch detection

## LLM Prompt for Implementation
```
Based on summary.md, step_1.md, step_2.md, and step_3.md, implement Step 4 by adding the get_parent_branch_name function to src/mcp_coder/utils/git_operations.py.

This function should:
1. Use the get_main_branch_name() function internally  
2. Return the main branch name as the parent branch (simple heuristic)
3. Follow existing logging patterns
4. Delegate all validation and error handling to get_main_branch_name()

Keep it extremely simple - just call get_main_branch_name() and return its result. This covers the majority of real-world use cases where feature branches come from main. The function should pass the tests written in Step 1.
```
