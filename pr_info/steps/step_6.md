# Step 6 — create-pr auto-path assignee-add (best-effort)

**Read `pr_info/steps/summary.md` first** (§6 create-pr assignee-add). Depends on Step 1
(`get_repo_flag`). After a successful PR creation on the auto path, assign the PR to the
authenticated user. Best-effort: never fails the workflow or flips a label. TDD: write tests first.

## WHERE
- Modify `src/mcp_coder/workflows/create_pr/core.py` — inside `run_create_pr_workflow`, after
  `pr_result` is confirmed successful (right after `pr_number = pr_result["number"]` and the PR
  logging, before / around the existing label-update block).
- Add tests in `tests/workflows/create_pr/` (the module covering `run_create_pr_workflow`).

## WHAT
Add a small private helper for testability and a single call site:
```python
def _add_pr_assignee_best_effort(project_dir: Path, pr_number: int) -> None:
    """Assign the PR to the authenticated user on the auto-review path only.

    No-op when auto_review_implementation is off for the repo. Best-effort:
    logs a warning on failure, never raises.
    """
```

## HOW
- `from mcp_coder.utils.repo_config import get_repo_flag`
- **Add `get_authenticated_username` to the existing `mcp_coder.mcp_workspace_github` import** in
  this module — `PullRequestManager` is already imported here, but `get_authenticated_username` is
  **not yet** imported and must be added.
- Call `_add_pr_assignee_best_effort(project_dir, pr_number)` on the success path only.
- `add_assignees` is best-effort by construction upstream (returns `{}` on API failure, never
  raises); the local try/except guards only non-API exceptions.
- **`get_authenticated_username()` takes NO `project_dir`.** Its upstream signature is
  `get_authenticated_username(hostname: Optional[str] = None) -> str` — call it with **no
  arguments** (it resolves the token internally). It **raises `ValueError`** on auth failure and
  never returns an empty string, so no empty-username check is needed; the `try/except Exception`
  catches that `ValueError` and keeps the assignee-add best-effort.

## ALGORITHM
```
if not get_repo_flag(project_dir, "auto_review_implementation"): return
try:
    username = get_authenticated_username()   # no args; raises ValueError on auth failure
    PullRequestManager(project_dir).add_assignees(pr_number, username)
    log OUTPUT "Assigned PR #{pr_number} to {username}"
except Exception as e:  # pylint: disable=broad-exception-caught
    log warning "assignee-add failed (non-blocking): {e}"
```

## DATA
- Helper returns `None`. No change to `run_create_pr_workflow`'s `int` return contract.

## TESTS
Patch `get_repo_flag`, `get_authenticated_username`, and `PullRequestManager` at
`mcp_coder.workflows.create_pr.core.*`:
1. Flag on → `add_assignees(pr_number, username)` called once with the PR number + username.
2. Flag off → `add_assignees` never called (manual PRs don't get assigned).
3. `add_assignees` raises → workflow still returns success (0); warning logged, no re-raise.
4. Assignee-add runs only after successful PR creation (not on a failed-PR path).

## Commit
One commit: helper + call site + tests. Run pylint, pytest (`-n auto` unit exclusion), mypy,
`lint-imports`.
