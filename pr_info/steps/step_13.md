# Step 13: Apply Decorator to PullRequestManager Methods

## Objective
Apply `_handle_github_errors` decorator to all 4 methods in `PullRequestManager`, removing bare `Exception` catches and debug logging.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/pr_manager.py`
- **Methods**: 4 public methods (create_pull_request, get_pull_request, list_pull_requests, close_pull_request)

## WHAT
Transform error handling and remove debug logging:
```python
# BEFORE
@log_function_call
def create_pull_request(...) -> PullRequestData:
    try:
        ...
    except GithubException as e:
        logger.error(f"GitHub API error creating pull request: {e}")
        logger.error(f"GitHub API error status: {e.status}")  # REMOVE
        logger.error(f"GitHub API error data: {e.data}")      # REMOVE
        return cast(PullRequestData, {})
    except Exception as e:  # REMOVE THIS BLOCK
        logger.error(...)
        return cast(PullRequestData, {})

# AFTER
@log_function_call
@_handle_github_errors(lambda: cast(PullRequestData, {}))
def create_pull_request(...) -> PullRequestData:
    try:
        ...
    except GithubException as e:
        logger.error(f"GitHub API error creating pull request: {e}")
        return cast(PullRequestData, {})
```

## HOW
- Import decorator from base_manager
- Add decorator to all 4 methods
- Remove bare `except Exception` blocks
- Remove debug logging lines (e.status, e.data)
- Keep single-line error logging in GithubException blocks

## ALGORITHM
```
1. For each of 4 methods in PullRequestManager:
2. Add @_handle_github_errors(lambda: cast(PullRequestData, {}))
   (or lambda: [] for list_pull_requests)
3. Remove bare Exception catch block
4. Remove debug logging (status, data) from GithubException block
5. Keep single error message line
```

## DATA
```python
# Methods and their empty return factories
create_pull_request: lambda: cast(PullRequestData, {})
get_pull_request: lambda: cast(PullRequestData, {})
close_pull_request: lambda: cast(PullRequestData, {})
list_pull_requests: lambda: []
```

## LLM Prompt
```
Based on Step 11, implement Step 13: Apply Decorator to PullRequestManager Methods.

Apply the `_handle_github_errors` decorator to all 4 methods in pr_manager.py:
1. create_pull_request
2. get_pull_request
3. list_pull_requests
4. close_pull_request

Additional cleanup required:
- Remove debug logging lines (e.status, e.data) from create_pull_request
- Remove bare `except Exception` blocks from all methods
- Keep single-line error logging in GithubException blocks

Requirements:
- Add decorator below @log_function_call
- Use appropriate empty return factory (cast(PullRequestData, {}) or [])
- Maintain all other logic unchanged

Run tests to verify behavior unchanged.
```
