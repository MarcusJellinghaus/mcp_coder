# Step 1: Remove error swallowing from `PullRequestManager.create_pull_request()`

> **Context**: See `pr_info/steps/summary.md` for full issue context.

## LLM Prompt

You are implementing Step 1 of Issue #859. Read `pr_info/steps/summary.md` for context, then implement this step.

**Goal**: Make `PullRequestManager.create_pull_request()` raise exceptions with descriptive error messages instead of silently returning `{}`.

## WHERE

- **Modify**: `src/mcp_coder/utils/github_operations/pr_manager.py` — method `create_pull_request()`
- **Modify**: `tests/utils/github_operations/test_pr_manager.py` — tests for validation failures

## WHAT

### `pr_manager.py` changes to `create_pull_request()`:

1. **Remove** the `@_handle_github_errors(lambda: cast(PullRequestData, {}))` decorator (line above method def)
2. **Remove** the `except GithubException` block at the bottom of the method (the `try/except` around the API call)
3. **Convert** each `return cast(PullRequestData, {})` to a `raise ValueError("descriptive message")`:

| Current code | New code |
|---|---|
| `return cast(PullRequestData, {})` after `project_dir is None` | `raise ValueError("project_dir required for default branch resolution")` |
| `return cast(PullRequestData, {})` after `resolved_base is None` | `raise ValueError("Could not determine default branch for repository")` |
| `return cast(PullRequestData, {})` after invalid title | `raise ValueError(f"Invalid PR title: '{title}'. Must be a non-empty string.")` |
| `return cast(PullRequestData, {})` after `_validate_branch_name(head_branch)` fails | `raise ValueError(f"Invalid head branch name: '{head_branch}'")` |
| `return cast(PullRequestData, {})` after `_validate_branch_name(base_branch)` fails | `raise ValueError(f"Invalid base branch name: '{base_branch}'")` |
| `return cast(PullRequestData, {})` after `repo is None` | `raise ValueError("Could not access GitHub repository")` |

4. **Remove** the now-unnecessary `try:` line that wrapped the `repo = self._get_repository()` block (un-indent the remaining code)

### Function signature (unchanged):

```python
def create_pull_request(
    self,
    title: str,
    head_branch: str,
    base_branch: Optional[str] = None,
    body: str = "",
) -> PullRequestData:
```

Note: Return type stays `PullRequestData` (no longer returns empty dict — raises on failure).

**Docstring**: Update the method's docstring to reflect that it raises exceptions instead of returning empty dict. Remove "or empty dict on failure" language and add a `Raises:` section documenting `ValueError` (validation failures) and `GithubException` (API errors).

## ALGORITHM

```
# Pseudocode for create_pull_request after changes:
resolve base_branch if None — raise ValueError if can't determine
validate title — raise ValueError if empty
validate head_branch — raise ValueError if invalid
validate base_branch — raise ValueError if invalid
repo = _get_repository() — raise ValueError if None
pr = repo.create_pull(...)  # GithubException propagates as-is to caller (not wrapped in ValueError)
return PullRequestData dict
```

**Important**: After removing both the `@_handle_github_errors` decorator and the local `except GithubException`, the `repo.create_pull()` call is intentionally unprotected. `GithubException` propagates to `core.py`'s `except Exception as e` block, which formats it as `f"Error creating pull request: {e}"`. Do not re-add exception handling around this call.

**Verify**: Confirm that `@log_function_call` (the remaining decorator) does not catch or swallow exceptions — it should only log entry/exit.

## DATA

- **Input**: unchanged
- **Output on success**: `PullRequestData` dict (unchanged)
- **Output on failure**: raises `ValueError` (validation) or `GithubException` (API error) — instead of returning `{}`

## Test changes

### `tests/utils/github_operations/test_pr_manager.py`:

Update three tests that currently assert `not result` (empty dict) to assert `pytest.raises(ValueError)`:

1. `test_create_pull_request_empty_title` — expect `ValueError` with match on "Invalid PR title"
2. `test_create_pull_request_invalid_head_branch` — expect `ValueError` with match on "Invalid head branch"
3. `test_create_pull_request_invalid_base_branch` — expect `ValueError` with match on "Invalid base branch"
4. Update `test_github_api_error_returns_empty` — rename to `test_create_pull_request_github_api_error_propagates`, change assertion from `assert not result` to `pytest.raises(GithubException)`
5. Update `test_create_pr_returns_empty_when_default_branch_unknown` — change assertion from `assert not result` to `pytest.raises(ValueError)` with match on `'Could not determine default branch'`

### DO NOT change:
- Any other methods on `PullRequestManager` (they keep `@_handle_github_errors`)
- The `_handle_github_errors` decorator itself
- The `_validate_branch_name` or `_validate_pr_number` helper methods
- The `@log_function_call` decorator behavior — but verify it does not catch/swallow exceptions

## Commit

```
fix(pr_manager): raise exceptions instead of swallowing errors in create_pull_request

Remove @_handle_github_errors decorator and local except GithubException
from create_pull_request(). Convert silent return {} paths to raise
ValueError with descriptive messages. This allows callers to receive
actual error reasons instead of empty dicts.

Part of #859.
```
