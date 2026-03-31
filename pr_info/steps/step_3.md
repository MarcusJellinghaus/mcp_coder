# Step 3: Change `create_pull_request()` return type to `PullRequestData | None`

## Context
See `pr_info/steps/summary.md` for full issue context. This step changes
`create_pull_request()` to return PR info (number, url) instead of `bool`,
enabling cleanup failure comments to include a PR link.

## WHERE
- **Modify:** `src/mcp_coder/workflows/create_pr/core.py` — `create_pull_request()` function
- **Modify:** `src/mcp_coder/workflows/create_pr/core.py` — `run_create_pr_workflow()` caller site
- **Modify:** `tests/workflows/create_pr/test_workflow.py` — update mocks for new return type
- **Modify:** `tests/workflows/create_pr/test_repository.py` — update if it tests `create_pull_request()`

## WHAT

### New import in `core.py`:
```python
from mcp_coder.utils.github_operations.pr_manager import PullRequestData
```

### `create_pull_request()` signature change:
```python
# Before:
def create_pull_request(project_dir: Path, title: str, body: str) -> bool:

# After:
def create_pull_request(project_dir: Path, title: str, body: str) -> PullRequestData | None:
    """Returns PullRequestData dict with 'number', 'url' etc. on success, None on failure."""
```

### Changes inside `create_pull_request()`:
- Instead of `return True` → `return pr_result`
- Instead of `return False` → `return None`
- Remove the local logging of pr_number/pr_url (caller can do it if needed)

### Changes in `run_create_pr_workflow()` caller:
```python
# Before:
if not create_pull_request(project_dir, title, body):
    logger.error("Failed to create pull request")
    return 1

# After:
pr_result = create_pull_request(project_dir, title, body)
if pr_result is None:
    logger.error("Failed to create pull request")
    return 1

pr_number = pr_result["number"]
pr_url = pr_result.get("url", "")
log_step(f"Pull request created: #{pr_number} ({pr_url})")
```

### Test updates in `test_workflow.py`:
- `mock_create_pr.return_value = True` → `mock_create_pr.return_value = {"number": 42, "url": "https://github.com/test/repo/pull/42"}`
- `mock_create_pr.return_value = False` → `mock_create_pr.return_value = None`

## HOW
- `PullRequestManager.create_pull_request()` already returns a `PullRequestData`
  TypedDict with `number`, `url`, etc. The wrapper just stops discarding it.
- Import `PullRequestData` from `pr_manager` for type annotation

## ALGORITHM — updated `create_pull_request`:
```
1. Get current branch and base branch (return None on failure)
2. Create PullRequestManager, call create_pull_request()
3. If result is empty or has no "number" → return None
4. Return the pr_result dict
```

## DATA
- Return type: `PullRequestData | None`
- Key fields used downstream: `pr_result["number"]`, `pr_result.get("url", "")`
- `pr_result` variable stored in `run_create_pr_workflow` scope for later use in cleanup failure comments (step 4)

## Commit
One commit: "Change create_pull_request() to return PullRequestData instead of bool"
