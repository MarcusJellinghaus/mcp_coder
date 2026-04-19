# Step 3: Wire error message through Step 5 + update workflow/failure tests

> **Context**: See `pr_info/steps/summary.md` for full issue context. Steps 1-2 must be completed first.

## LLM Prompt

You are implementing Step 3 of Issue #859. Read `pr_info/steps/summary.md` for context, then implement this step.

**Goal**: Unpack the tuple returned by `create_pull_request()` in Step 5 of `run_create_pr_workflow()` and pass the real error message to `_handle_create_pr_failure()`. Update workflow and failure handling tests to match.

## WHERE

- **Modify**: `src/mcp_coder/workflows/create_pr/core.py` — function `run_create_pr_workflow()`, Step 5 block
- **Modify**: `tests/workflows/create_pr/test_workflow.py` — tests that mock `create_pull_request`
- **Modify**: `tests/workflows/create_pr/test_failure_handling.py` — `test_pr_creation_failure`

## WHAT

### `core.py` `run_create_pr_workflow()` Step 5 (~line 606):

**Change** the Step 5 block from:

```python
pr_result = create_pull_request(project_dir, title, body)
if pr_result is None:
    logger.error("Failed to create pull request")
    ...
    _handle_create_pr_failure(
        ...
        message="Failed to create pull request",
        ...
    )
```

**To:**

```python
pr_result, pr_error = create_pull_request(project_dir, title, body)
if pr_result is None:
    error_msg = pr_error or "Failed to create pull request"
    logger.error(error_msg)
    ...
    _handle_create_pr_failure(
        ...
        message=error_msg,
        ...
    )
```

That's it — one line unpacking change, one variable for the error message, pass it through.

## ALGORITHM

```
# Step 5 pseudocode:
pr_result, pr_error = create_pull_request(project_dir, title, body)
if pr_result is None:
    error_msg = pr_error or "Failed to create pull request"  # fallback just in case
    log error_msg
    call _handle_create_pr_failure(message=error_msg, ...)
    return 1
# ... continue with success path using pr_result
```

## DATA

- `pr_result`: `PullRequestData | None` (same as before)
- `pr_error`: `str | None` — actual error message from the wrapper
- `error_msg`: `str` — the message passed to failure handler (real error or fallback)

## Test changes

### `tests/workflows/create_pr/test_failure_handling.py`:

**`test_pr_creation_failure`**: Change mock return value and verify error message propagation:

```python
# Before:
mock_create_pr.return_value = None

# After:
mock_create_pr.return_value = (None, "422 Validation Failed: head branch not found")

# Add assertion:
assert "422 Validation Failed" in call_kwargs["message"]
```

### `tests/workflows/create_pr/test_workflow.py`:

Update all tests that mock `create_pull_request`:

| Test | Current mock return | New mock return |
|---|---|---|
| `test_workflow_complete_success` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_pr_creation_fails` | `None` | `(None, "GitHub API error: 422 Validation Failed")` |
| `test_workflow_caches_issue_number_before_pr_creation` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_skips_label_update_when_not_linked` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_fallback_finds_issue_via_closing_references` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_fallback_multiple_closing_issues_uses_first` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_fallback_no_closing_issues_skips_labels` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_completed_with_warnings_when_no_issue_found` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_skips_fallback_when_issue_already_found` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |
| `test_workflow_execution_dir_passed_to_generate_summary` | `{"number": 42, "url": "..."}` | `({"number": 42, "url": "..."}, None)` |

Also verify in `test_workflow_pr_creation_fails` that the error message is passed through:

```python
assert "422 Validation Failed" in mock_handle_failure.call_args.kwargs["message"]
```

## Commit

```
fix(create-pr): surface actual error message when PR creation fails

Unpack (result, error_msg) tuple from create_pull_request() in step 5
and pass the real error message to the failure handler. Users now see
the actual GitHub API error instead of generic "Failed to create PR".

Closes #859.
```
