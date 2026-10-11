# Step 4: create-pr checks the base branch before opening the PR

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. Step 1's `check_base_branch_on_origin` is already in place. Write the tests first, then the code. Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/workflows/create_pr/core.py`
- `tests/workflows/create_pr/test_repository.py`

## WHAT

`create_pull_request(project_dir, title, body) -> Tuple[Optional[PullRequestData], Optional[str]]` — signature unchanged.

## HOW

- Import `check_base_branch_on_origin` alongside `detect_base_branch` from `mcp_coder.workflow_utils.base_branch`.
- In `create_pull_request`, after the `base_branch is None` block and before `PullRequestManager`:
  ```python
  missing_err = check_base_branch_on_origin(project_dir, base_branch)
  if missing_err:
      logger.error(missing_err)
      return None, missing_err
  ```

## ALGORITHM

```
current = get_current_branch_name(); if None: fail
base = detect_base_branch(...);       if None: fail
if err := check_base_branch_on_origin(base): return (None, err)
create PR
```

## DATA

`(None, error_message)` on a missing base; otherwise unchanged.

## Tests (write first)

`TestCreatePullRequest` in `test_repository.py`:
- Every existing test that reaches `PullRequestManager` (base detected): add `@patch("mcp_coder.workflows.create_pr.core.check_base_branch_on_origin", return_value=None)`.
- New: check returns `"Base branch 'epic/x' not found on origin; ..."` → `result is None`, `error` contains `epic/x`, `PullRequestManager` not called.
