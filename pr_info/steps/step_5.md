# Step 5 — VSCodeClaude merge-conflict detection (session_launch.py)

Reference: `pr_info/steps/summary.md`. Depends on Step 1 (label
`merge_conflict`/`pr_created` internal ids must exist). This step is the
trigger: it's what actually puts an issue at `status-71`, closing the loop
that Steps 2-4 built. It does not depend on Steps 2-4 to be mergeable on its
own (it only sets a label), but the end-to-end feature only works once all
five steps have landed.

## Precondition check

Read `src/mcp_coder/workflows/vscodeclaude/session_launch.py`'s
`process_eligible_issues()`. Confirm it still computes `eligible_issues =
_filter_eligible_vscodeclaude_issues(all_cached_issues, github_username)`
and then `actionable_issues = [issue for issue in eligible_issues if
is_status_eligible_for_session(get_issue_status(issue))]` as two separate,
adjacent statements, with `issue_manager`/`branch_manager` already built via
`repo_url=repo_url` above both. If this structure has changed, write one
line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (modify)
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` (modify)

## WHAT

```python
def _build_pr_manager(repo_url: str) -> PullRequestManager:
    """Build a PullRequestManager from a repo URL only, no local checkout.

    Bypasses PullRequestManager.__init__ (which requires project_dir) the
    same way label_transitions.py already does for IssueBranchManager.
    """

def _check_merge_conflict(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> None:
    """Escalate a status-10 PR to status-71 if GitHub reports it as "dirty".

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.
    """
```

Both are private module-level functions in `session_launch.py`, called from
inside `process_eligible_issues()`.

## HOW

- New imports in `session_launch.py`:
  `from ...mcp_workspace_github import BaseGitHubManager, PullRequestManager`
  (added to the existing `from ...mcp_workspace_github import (...)` block)
  and `from ...workflow_utils.label_transitions import update_workflow_label`.
- In `process_eligible_issues()`, immediately after the `eligible_issues =
  _filter_eligible_vscodeclaude_issues(...)` line and before the
  `actionable_issues = [...]` comprehension, add:

  ```python
  repo_owner, repo_name_str = repo_full_name.split("/", 1)
  for issue in eligible_issues:
      if get_issue_status(issue) == "status-10:pr-created":
          _check_merge_conflict(
              issue, branch_manager, issue_manager, repo_owner, repo_name_str
          )
  ```

  `issue_manager`/`branch_manager` are the ones already constructed earlier
  in the function via `repo_url=repo_url`.

## ALGORITHM

`_check_merge_conflict`:

```
try:
    branch = branch_manager.get_branch_with_pr_fallback(issue["number"], repo_owner, repo_name)
    if branch is None: return
    pr_manager = _build_pr_manager(f"https://github.com/{repo_owner}/{repo_name}")
    prs = pr_manager.find_pull_request_by_head(branch)
    if prs and prs[0]["mergeable_state"] == "dirty":
        update_workflow_label(issue_manager, "pr_created", "merge_conflict",
                               validated_issue_number=issue["number"])
except Exception as exc:
    log warning with issue number and exc
```

`_build_pr_manager`:

```
manager = PullRequestManager.__new__(PullRequestManager)
BaseGitHubManager.__init__(manager, repo_url=repo_url)
return manager
```

## DATA

`_check_merge_conflict` returns `None` — its only effect is the GitHub
label transition (or nothing). The in-memory `issue` dict for this poll is
not mutated, so this poll's `actionable_issues` filter still sees the old
`status-10:pr-created` label and won't launch a session for it; the next
cache refresh will see `status-71:merge-conflict` and route accordingly.

## TDD order

1. In `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`,
   add a new test class covering `process_eligible_issues` with a
   `status-10:pr-created` issue in the cached batch:
   - mock `session_launch.PullRequestManager` and
     `session_launch.BaseGitHubManager` (or patch `_build_pr_manager`
     directly, whichever is simpler to assert against) so
     `find_pull_request_by_head` returns a `PullRequestData`-shaped dict
     with `"mergeable_state": "dirty"`; assert `mock_issue_manager`'s
     underlying `transition_issue_label`/label-update path was invoked for
     `status-71:merge-conflict` (via monkeypatching
     `session_launch.update_workflow_label` directly is simplest — assert
     it was called with `from_label_id="pr_created",
     to_label_id="merge_conflict", validated_issue_number=<issue number>`).
   - a second case with `"mergeable_state": "clean"` → assert
     `update_workflow_label` was *not* called.
   - a third case with `branch_manager.get_branch_with_pr_fallback`
     returning `None` → assert no `PullRequestManager`/`update_workflow_label`
     call happens at all.
   - a fourth case where `find_pull_request_by_head` raises → assert
     `process_eligible_issues` does not raise and existing issues are still
     processed normally.
   Confirm these fail against current code.
2. Implement `_build_pr_manager`, `_check_merge_conflict`, and the splice
   in `process_eligible_issues()` to make them pass.
3. Re-run the full `test_session_launch_process_issues.py` file and
   `test_session_launch.py` to confirm no existing test (e.g. the
   status-01/status-04 branch-requirement tests already in the file) broke.

## Checks before commit

pylint, pytest (fast unit marker set), mypy,
`mcp__mcp-tools-py__run_format_code`. All must pass.

## Commit message

```
feat(vscodeclaude): detect merge conflicts on status-10 PRs
```

## LLM prompt for this step

> Read `pr_info/steps/summary.md` for the overall design, then implement
> `pr_info/steps/step_5.md` exactly as written. Follow TDD: add the new
> test cases to
> `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
> first and confirm they fail, then add `_build_pr_manager`,
> `_check_merge_conflict`, and the splice into `process_eligible_issues()`
> in `src/mcp_coder/workflows/vscodeclaude/session_launch.py` to make them
> pass, without breaking any existing test in that file. If this step's
> "Precondition check" section fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise make one commit containing all
> the changes, after formatters/pylint/pytest/mypy all pass.
