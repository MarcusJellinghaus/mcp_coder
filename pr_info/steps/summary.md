# Issue #859: Surface actual error message when PR creation fails

## Problem

The `create-pr` workflow fails at Step 5 ("Creating pull request...") without surfacing the actual error message. The process exits with RC=-1 but no error details are shown in the output or posted to the GitHub issue comment.

Error messages are swallowed at multiple layers:
1. `PullRequestManager.create_pull_request()` catches `GithubException`, returns `{}`
2. The `@_handle_github_errors` decorator also catches and returns `{}`
3. `core.py` wrapper returns `None`, losing the error context
4. Step 5 passes a hardcoded `"Failed to create pull request"` to the failure handler

## Solution

Propagate real error messages from `PullRequestManager` through `core.py` to the failure handler:

1. Let `PullRequestManager.create_pull_request()` raise exceptions instead of swallowing them
2. Have `core.py`'s `create_pull_request()` wrapper catch and return errors as a tuple
3. Pass the actual error string to `_handle_create_pr_failure()` in step 5

## Architectural / Design Changes

### Error propagation pattern change

**Before:** `PullRequestManager.create_pull_request()` silently returns `{}` on all failures (validation errors, API errors). The `@_handle_github_errors` decorator adds a second layer of silent error swallowing. The `core.py` wrapper converts `{}` → `None`, and step 5 uses a hardcoded error string.

**After:** `PullRequestManager.create_pull_request()` raises exceptions with descriptive messages on all failure paths. The `@_handle_github_errors` decorator is removed from this method only (kept on all other methods). The `core.py` wrapper catches exceptions and returns `tuple[PullRequestData | None, str | None]` — `(result, None)` on success, `(None, "error message")` on failure. Step 5 unpacks the tuple and passes the real error message to the failure handler.

### Scope of decorator removal

`@_handle_github_errors` is removed **only** from `create_pull_request()` because it's a critical workflow-determining operation. All other `PullRequestManager` methods (`get_pull_request`, `list_pull_requests`, `find_pull_request_by_head`, `close_pull_request`, `get_closing_issue_numbers`) keep the decorator — they are fire-and-forget operations where silent failure is acceptable.

### Auth error behavior preserved

The decorator previously re-raised 401/403 errors. After removal, these still propagate naturally — caught by the broad `except` in `core.py`. No behavior change for auth failures.

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Remove decorator + exception catch from `create_pull_request()`, convert `return {}` to `raise ValueError(...)` |
| `src/mcp_coder/workflows/create_pr/core.py` | Change `create_pull_request()` return type to tuple, unpack in step 5 |
| `tests/utils/github_operations/test_pr_manager.py` | Update validation tests to expect `ValueError` instead of empty dict |
| `tests/workflows/create_pr/test_repository.py` | Update wrapper tests for tuple return type |
| `tests/workflows/create_pr/test_workflow.py` | Update workflow tests for tuple return type |
| `tests/workflows/create_pr/test_failure_handling.py` | Update PR creation failure test for tuple + error message |

## Implementation Steps

- **Step 1**: `pr_manager.py` — Remove error swallowing from `create_pull_request()`
- **Step 2**: `core.py` wrapper — Return `(result, error_msg)` tuple
- **Step 3**: `core.py` step 5 + workflow/failure tests — Wire error message through
