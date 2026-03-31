# Step 1: Add `find_pull_request_by_head()` to PullRequestManager

## LLM Prompt
> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add `find_pull_request_by_head()` method to `PullRequestManager`. Write tests first (TDD), then implement. Run all code quality checks after.

## WHERE
- **Test**: `tests/utils/github_operations/test_pr_manager_find_by_head.py` (new file)
- **Implementation**: `src/mcp_coder/utils/github_operations/pr_manager.py`

## WHAT

### New method on `PullRequestManager`:
```python
@log_function_call
@_handle_github_errors(lambda: [])
def find_pull_request_by_head(self, head_branch: str) -> List[PullRequestData]:
```

**Parameters:**
- `head_branch`: Branch name (e.g., `"feature/xyz"`) — method constructs `"owner:branch"` internally

**Returns:** `List[PullRequestData]` — matching open PRs (empty list on error/not found)

## HOW
- Decorators: `@log_function_call`, `@_handle_github_errors(lambda: [])`
- Import: Already available — `log_function_call`, `_handle_github_errors` from base_manager
- Get owner from `self.repository_name` property (returns `"owner/repo"`, split on `/`)
- Use only the `@_handle_github_errors` decorator for error handling. Do NOT add an inner try/except block — the decorator already catches `GithubException` and returns the default.

## ALGORITHM
```
1. Validate head_branch using existing _validate_branch_name()
2. Get repo via self._get_repository()
3. Extract owner from self.repository_name.split("/")[0]
4. Call repo.get_pulls(state="open", head=f"{owner}:{head_branch}")
5. Convert each PR to PullRequestData dict (same pattern as list_pull_requests)
6. Return list
```

## DATA
- **Input**: `head_branch: str` (branch name without owner prefix)
- **Output**: `List[PullRequestData]` — each dict has: number, title, body, state, head_branch, base_branch, url, created_at, updated_at, user, mergeable, merged, draft
- **Error**: Returns `[]` (via decorator)

## TESTS (`test_pr_manager_find_by_head.py`)

Follow existing pattern from `test_pr_manager.py`:
- `@pytest.mark.git_integration` class marker
- Mock `Github` via `@patch("mcp_coder.utils.github_operations.base_manager.Github")`
- Use `create_mock_pr()` helper (import from `test_pr_manager`)

| Test | Description |
|------|-------------|
| `test_find_pr_by_head_success` | Single PR found — verify API called with `head="owner:branch"`, returns list with 1 item |
| `test_find_pr_by_head_multiple_prs` | Two PRs found — returns list with 2 items |
| `test_find_pr_by_head_not_found` | No PRs — returns empty list |
| `test_find_pr_by_head_invalid_branch` | Invalid branch name — returns empty list (validation) |
| `test_find_pr_by_head_api_error` | GithubException — returns empty list (decorator handles) |

## COMMIT
`feat(pr_manager): add find_pull_request_by_head() for PR discovery by head branch`
