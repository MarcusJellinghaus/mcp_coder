# Step 11: Create Error Handling Decorator

## Objective
Create a reusable `_handle_github_errors` decorator in `BaseGitHubManager` to eliminate error handling duplication across all GitHub manager methods.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/base_manager.py`
- **Location**: Add after existing class methods, before end of class

## WHAT
```python
def _handle_github_errors(empty_return_factory: Callable[[], T]) -> Callable:
    """Decorator to handle GithubException errors consistently."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            ...
        return wrapper
    return decorator
```

## HOW
- Import `functools.wraps` and `Callable` from typing
- Import `GithubException` from `github`
- Decorator wraps methods, catches `GithubException` only
- Auth errors (401, 403) are re-raised
- Other errors return empty value from factory
- All other exceptions bubble up unchanged

## ALGORITHM
```
1. Receive empty_return_factory callable as parameter
2. Define decorator that wraps target method
3. In wrapper, try to call original method
4. On GithubException: check status code
   - If 401 or 403: re-raise (auth errors)
   - Else: log error, return empty_return_factory()
5. Let all other exceptions propagate (programming errors)
```

## DATA
```python
# Decorator usage patterns
@_handle_github_errors(lambda: cast(IssueData, {}))
def create_issue(...) -> IssueData: ...

@_handle_github_errors(lambda: [])
def get_comments(...) -> List[CommentData]: ...

@_handle_github_errors(lambda: False)
def delete_comment(...) -> bool: ...
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary and code review findings, implement Step 11: Create Error Handling Decorator.

Create a `_handle_github_errors` decorator in `base_manager.py` that:
- Takes a callable that returns empty values (dict/list/False)
- Wraps methods to catch `GithubException` only
- Re-raises auth errors (status 401, 403)
- Returns empty value for other GitHub errors
- Lets programming errors propagate

Requirements:
- Add to BaseGitHubManager class as a static or class method
- Use functools.wraps to preserve method metadata
- Use generic typing to support any return type
- Include comprehensive docstring with usage examples
- Follow existing code style

Do not apply the decorator yet - just create it.
Add unit tests in tests/utils/github_operations/test_base_manager.py to verify:
- Auth errors are re-raised
- Other GitHub errors return empty value
- Non-GitHub exceptions propagate
- Method metadata is preserved
```
