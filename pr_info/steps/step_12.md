# Step 12: Apply Decorator to IssueManager Methods

## Objective
Apply `_handle_github_errors` decorator to all 10 methods in `IssueManager`, removing bare `Exception` catches.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: All 10 public methods (create_issue, add_comment, get_comments, edit_comment, delete_comment, close_issue, reopen_issue, get_available_labels, add_labels, remove_labels, set_labels)

## WHAT
Transform error handling from:
```python
@log_function_call
def create_issue(...) -> IssueData:
    try:
        ...
    except GithubException as e:
        if e.status in (401, 403):
            raise
        logger.error(...)
        return IssueData(number=0, ...)
    except Exception as e:
        logger.error(...)
        return IssueData(number=0, ...)
```

To:
```python
@log_function_call
@_handle_github_errors(lambda: IssueData(number=0, title="", ...))
def create_issue(...) -> IssueData:
    try:
        ...
    except GithubException as e:
        if e.status in (401, 403):
            raise
        logger.error(...)
        return IssueData(number=0, ...)
    # Remove bare Exception catch
```

## HOW
- Import decorator from base_manager
- Add decorator above each method (below `@log_function_call`)
- Remove bare `except Exception` blocks
- Keep method-specific `GithubException` handling for custom error messages
- Keep validation logic unchanged

## ALGORITHM
```
1. For each of 10 methods in IssueManager:
2. Add @_handle_github_errors(empty_factory) decorator
3. Remove bare Exception catch block
4. Keep GithubException handling as-is (for custom logging)
5. Verify return type matches empty_factory type
```

## DATA
```python
# Methods and their empty return factories
create_issue: lambda: IssueData(number=0, title="", body="", state="", labels=[], user=None, created_at=None, updated_at=None, url="", locked=False)
close_issue: lambda: IssueData(...) # same as above
reopen_issue: lambda: IssueData(...) # same as above
add_labels: lambda: IssueData(...) # same as above
remove_labels: lambda: IssueData(...) # same as above
set_labels: lambda: IssueData(...) # same as above

add_comment: lambda: CommentData(id=0, body="", user=None, created_at=None, updated_at=None, url="")
edit_comment: lambda: CommentData(...) # same as above

get_comments: lambda: []
get_available_labels: lambda: []

delete_comment: lambda: False
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary and Step 11, implement Step 12: Apply Decorator to IssueManager Methods.

Apply the `_handle_github_errors` decorator to all 10 methods in issue_manager.py:
1. create_issue
2. add_comment
3. get_comments
4. edit_comment
5. delete_comment
6. close_issue
7. reopen_issue
8. get_available_labels
9. add_labels
10. remove_labels
11. set_labels

Requirements:
- Add decorator below @log_function_call
- Remove ONLY the bare `except Exception` catch blocks
- Keep existing `except GithubException` blocks (they have custom error messages)
- Use appropriate empty return factory for each method's return type
- Do not change any other logic or validation

Run unit tests to verify:
- All 49+ IssueManager unit tests still pass
- Auth errors still raise exceptions
- Other errors return empty values
- Method behavior unchanged
```
