# Step 5: Add Enhanced Features and Validation

## Objective
Add enhanced features to PullRequestManager and improve validation and error handling.

## WHERE
- File: `src/mcp_coder/utils/github_operations/pr_manager.py` (modify existing)
- File: `tests/utils/test_github_operations.py` (modify existing)

## WHAT
- Enhance merge_pull_request method with better parameters and validation
- Add input validation for all methods
- Improve error handling with specific exception types
- Add logging for better debugging
- Add additional tests for enhanced features

## HOW
### Enhanced merge_pull_request Method
```python
@log_function_call
def merge_pull_request(
    self, 
    pr_number: int, 
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None,
    merge_method: str = "merge"
) -> Dict[str, Any]:
    """Merge a pull request with enhanced options.
    
    Args:
        pr_number: Pull request number
        commit_title: Optional custom commit title
        commit_message: Optional custom commit message  
        merge_method: "merge", "squash", or "rebase"
        
    Returns:
        Dict with merge details: {'merged': bool, 'sha': str, 'message': str}
        
    Raises:
        ValueError: If merge_method is invalid
    """
    if merge_method not in ["merge", "squash", "rebase"]:
        raise ValueError(f"Invalid merge_method: {merge_method}")
    
    try:
        pr = self._repo.get_pull(pr_number)
        result = pr.merge(
            commit_title=commit_title,
            commit_message=commit_message,
            merge_method=merge_method
        )
        return {
            'merged': result.merged,
            'sha': result.sha,
            'message': result.message
        }
    except Exception as e:
        logger.error(f"Failed to merge PR {pr_number}: {e}")
        return {}
```

### Input Validation
```python
def _validate_pr_number(self, pr_number: int) -> None:
    """Validate PR number is positive integer."""
    if not isinstance(pr_number, int) or pr_number <= 0:
        raise ValueError(f"PR number must be positive integer, got: {pr_number}")

def _validate_branch_name(self, branch: str) -> None:
    """Validate branch name is non-empty string."""
    if not isinstance(branch, str) or not branch.strip():
        raise ValueError(f"Branch name must be non-empty string, got: {branch}")
```

## ALGORITHM
```
1. Enhance merge_pull_request method with additional parameters
2. Add validation for merge_method parameter
3. Add comprehensive error handling with specific exceptions
4. Add input validation helper methods
5. Update all methods to use validation helpers
6. Add proper logging for debugging
7. Add tests for validation and error cases
8. Add tests for enhanced merge functionality
```

## DATA
- **Enhanced merge method**: Additional parameters for commit_title, commit_message, merge_method
- **Validation**: Input validation for PR numbers, branch names, merge methods
- **Error handling**: Specific exception types with descriptive messages
- **Logging**: Debug information for troubleshooting

## LLM Prompt
```
You are implementing Step 5 of the GitHub Pull Request Operations feature using the updated PullRequestManager approach.

Add enhanced features and validation to the PullRequestManager class to make it more robust and production-ready.

Requirements:
1. Enhance merge_pull_request method:
   - Add commit_title and commit_message optional parameters
   - Add validation for merge_method ("merge", "squash", "rebase")
   - Raise ValueError for invalid merge methods
   - Add comprehensive error handling and logging

2. Add input validation helper methods:
   - _validate_pr_number: Check for positive integers
   - _validate_branch_name: Check for non-empty strings
   - _validate_state: Check for valid PR states

3. Update existing methods to use validation:
   - Add validation calls to all methods that take PR numbers or branch names
   - Improve error messages with specific details

4. Add comprehensive logging:
   - Import logging and create logger
   - Add debug/error logging for all operations
   - Log validation failures and API errors

5. Add tests for enhanced features:
   - Test validation failures raise appropriate exceptions
   - Test enhanced merge functionality
   - Test error handling scenarios

Keep the existing functionality working while adding these enhancements.
```

## Verification
- [ ] merge_pull_request enhanced with additional parameters
- [ ] Merge method validation implemented
- [ ] Input validation helper methods added
- [ ] All methods updated to use validation
- [ ] Comprehensive logging added
- [ ] Tests added for validation failures
- [ ] Tests added for enhanced merge functionality
- [ ] Error handling scenarios tested
- [ ] All existing tests still pass
- [ ] New validation raises appropriate exceptions
