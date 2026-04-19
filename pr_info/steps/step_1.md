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

## ALGORITHM

```
# Pseudocode for create_pull_request after changes:
resolve base_branch if None — raise ValueError if can't determine
validate title — raise ValueError if empty
validate head_branch — raise ValueError if invalid
validate base_branch — raise ValueError if invalid
repo = _get_repository() — raise ValueError if None
pr = repo.create_pull(...)  # GithubException propagates naturally
return PullRequestData dict
```

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

### DO NOT change:
- Any other methods on `PullRequestManager` (they keep `@_handle_github_errors`)
- The `_handle_github_errors` decorator itself
- The `_validate_branch_name` or `_validate_pr_number` helper methods

## Commit

```
fix(pr_manager): raise exceptions instead of swallowing errors in create_pull_request

Remove @_handle_github_errors decorator and local except GithubException
from create_pull_request(). Convert silent return {} paths to raise
ValueError with descriptive messages. This allows callers to receive
actual error reasons instead of empty dicts.

Part of #859.
```
