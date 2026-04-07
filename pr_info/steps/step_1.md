# Step 1: Extract `_list_issues_no_error_handling()` from `list_issues()`

## Context
See `pr_info/steps/summary.md` for full context. This is step 1 of 3.

## Goal
Split `list_issues()` into two functions so the cache can call the raw version that raises on failure, while all other callers keep the existing error-swallowing behavior.

## WHERE
- **Modify:** `src/mcp_coder/utils/github_operations/issues/manager.py`
- **Modify:** `tests/utils/github_operations/test_issue_manager_core.py`

## WHAT

### Production code
Extract the body of `list_issues()` into a new private method `_list_issues_no_error_handling()`. Then make `list_issues()` delegate to it.

**Before:**
```python
@log_function_call
@_handle_github_errors(default_return=[])
def list_issues(self, state="open", include_pull_requests=False, since=None) -> List[IssueData]:
    # ... full body ...
```

**After:**
```python
def _list_issues_no_error_handling(
    self,
    state: str = "open",
    include_pull_requests: bool = False,
    since: Optional[datetime] = None,
) -> List[IssueData]:
    """List issues without error handling. Raises on API failure.

    Private method for callers that need to detect failures (e.g., cache).
    """
    repo = self._get_repository()
    if repo is None:
        logger.error("Failed to get repository")
        return []

    # ... rest of current list_issues body ...

@log_function_call
@_handle_github_errors(default_return=[])
def list_issues(self, state="open", include_pull_requests=False, since=None) -> List[IssueData]:
    """List all issues in the repository with pagination support.
    ...existing docstring...
    """
    return self._list_issues_no_error_handling(
        state=state, include_pull_requests=include_pull_requests, since=since
    )
```

### Test code
Add tests in `TestIssueManagerCore`:

**`test_list_issues_no_error_handling_server_error_raises`**
- Mock `_repository.get_issues` to raise `GithubException(500, ...)`
- Assert `_list_issues_no_error_handling()` raises `GithubException`

**`test_list_issues_no_error_handling_network_error_raises`**
- Mock `_repository.get_issues` to raise `ConnectionError`
- Assert `_list_issues_no_error_handling()` raises `ConnectionError`

**`test_list_issues_still_returns_empty_on_error`**
- Mock `_repository.get_issues` to raise `GithubException(500, ...)`
- Assert `list_issues()` returns `[]` (existing behavior preserved)

## HOW
- Move the entire body of `list_issues()` into `_list_issues_no_error_handling()`
- `list_issues()` becomes a thin wrapper that delegates to the private method
- The `@_handle_github_errors` decorator stays on `list_issues()` and catches any exception from the private method
- The existing test `test_list_issues_github_error_handling` (403 auth error) still passes unchanged

## DATA
- **`_list_issues_no_error_handling` return:** `List[IssueData]` on success, raises on failure
- **`list_issues` return:** Unchanged — `List[IssueData]` on success, `[]` on error (existing behavior)

## LLM Prompt
```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_1.md.

In src/mcp_coder/utils/github_operations/issues/manager.py:
1. Extract the body of list_issues() into _list_issues_no_error_handling() (no decorators)
2. Make list_issues() delegate to _list_issues_no_error_handling() (keep both decorators)

Add three tests in tests/utils/github_operations/test_issue_manager_core.py:
1. test_list_issues_no_error_handling_server_error_raises — GithubException(500) propagates
2. test_list_issues_no_error_handling_network_error_raises — ConnectionError propagates
3. test_list_issues_still_returns_empty_on_error — list_issues() returns [] on 500

Run all quality checks after changes. Commit as one unit.
```
