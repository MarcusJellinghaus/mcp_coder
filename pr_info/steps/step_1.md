# Step 1: Remove `@_handle_github_errors` from `list_issues()`

## Context
See `pr_info/steps/summary.md` for full context. This is step 1 of 3.

## Goal
Make `list_issues()` propagate exceptions instead of silently returning `[]`. This lets callers distinguish "no issues changed" from "API failed".

## WHERE
- **Modify:** `src/mcp_coder/utils/github_operations/issues/manager.py`
- **Modify:** `tests/utils/github_operations/test_issue_manager_core.py`

## WHAT

### Production code
Remove `@_handle_github_errors(default_return=[])` decorator from `IssueManager.list_issues()` method. Keep the `@log_function_call` decorator.

**Before:**
```python
@log_function_call
@_handle_github_errors(default_return=[])
def list_issues(self, state="open", include_pull_requests=False, since=None) -> List[IssueData]:
```

**After:**
```python
@log_function_call
def list_issues(self, state="open", include_pull_requests=False, since=None) -> List[IssueData]:
```

Also clean up the import if `_handle_github_errors` is no longer used in this file — but check first: other methods (`create_issue`, `get_issue`, `close_issue`, `reopen_issue`) still use it, so the import stays.

### Test code
Add tests in `TestIssueManagerCore` that verify non-auth GitHub errors (e.g. 500) and general exceptions now propagate from `list_issues()`:

**`test_list_issues_server_error_raises`**
- Mock `_repository.get_issues` to raise `GithubException(500, ...)`
- Assert `list_issues()` raises `GithubException`

**`test_list_issues_network_error_raises`**
- Mock `_repository.get_issues` to raise `ConnectionError`
- Assert `list_issues()` raises `ConnectionError`

## HOW
- The decorator is stacked: `@log_function_call` then `@_handle_github_errors`. Simply remove the second decorator line.
- The existing test `test_list_issues_github_error_handling` already tests 403 (auth error) raising — that behavior is unchanged (403 was already re-raised by the decorator, and without the decorator it still propagates naturally).

## DATA
- **Return value:** Unchanged — `List[IssueData]` on success
- **Error behavior change:** Non-auth exceptions (500, network errors, etc.) now raise instead of returning `[]`

## LLM Prompt
```
Read pr_info/steps/summary.md for full context, then implement pr_info/steps/step_1.md.

Remove the @_handle_github_errors(default_return=[]) decorator from IssueManager.list_issues() 
in src/mcp_coder/utils/github_operations/issues/manager.py. Keep @log_function_call.

Add two tests in tests/utils/github_operations/test_issue_manager_core.py:
1. test_list_issues_server_error_raises — GithubException(500) propagates
2. test_list_issues_network_error_raises — ConnectionError propagates

Run all three quality checks after changes. Commit as one unit.
```
