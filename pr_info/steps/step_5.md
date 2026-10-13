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

Also read `update_workflow_label` in
`src/mcp_coder/workflow_utils/label_transitions.py`. Confirm it still has
the `if issue_manager.project_dir is None: ... return False` guard
immediately before loading the label config (see "Fix:
`update_workflow_label` in repo_url mode" below). If that guard is gone or
reshaped, the fix below may already be moot or may need adapting — write
one line to `pr_info/.blocked.txt` and stop rather than guessing.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (modify)
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` (modify)
- `src/mcp_coder/workflow_utils/label_transitions.py` (modify — see "Fix:
  `update_workflow_label` in repo_url mode" below)
- `tests/workflow_utils/test_label_transitions.py` (modify)

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

### Fix: `update_workflow_label` in repo_url mode

`issue_manager` here is `IssueManager(repo_url=repo_url)`, so
`issue_manager.project_dir is None`. `update_workflow_label`
(`workflow_utils/label_transitions.py`) currently has an unconditional
guard — reached even when `validated_issue_number` is supplied and branch
detection is skipped entirely — that returns `False` before loading the
label config:

```python
if issue_manager.project_dir is None:
    logger.error(
        "Cannot load label config without project_dir. "
        "Label update is not supported for repo_url mode."
    )
    return False

config_path = get_labels_config_path(issue_manager.project_dir)
```

This makes `_check_merge_conflict`'s `update_workflow_label(...)` call a
guaranteed no-op: `status-71:merge-conflict` would never actually get set.
`get_labels_config_path(None)` already falls back to the bundled
`labels.json` by design (its own docstring: "Without project directory
(coordinator / remote mode): Uses bundled config") — the guard is simply
stricter than the function it's protecting. Delete the guard and call
`get_labels_config_path(issue_manager.project_dir)` unconditionally; passing
`None` through is exactly the already-supported "coordinator / remote mode"
path. This only changes behavior for calls that previously hit this `return
False` — i.e. `project_dir is None` — so no existing `project_dir`-mode
caller is affected.

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

1. In `tests/workflow_utils/test_label_transitions.py`, add a test that
   constructs `IssueManager(repo_url="https://github.com/owner/repo",
   github_token="dummy-token")` (`project_dir=None`) and calls
   `update_workflow_label(manager, "implementing", "code_review",
   validated_issue_number=123)`, mocking `load_labels_config` and
   `IssueManager.transition_issue_label` the same way the existing
   project_dir-mode tests do. Assert the result is `True` and
   `transition_issue_label` was called with issue number `123` — this is
   the case the current `project_dir is None` guard blocks. Confirm it
   fails against current code (guard returns `False` first). Then remove
   the guard in `label_transitions.py` per the "Fix" note above and confirm
   it passes, without breaking any of the file's existing project_dir-mode
   tests.
2. In `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`,
   add a new test class covering `process_eligible_issues` with a
   `status-10:pr-created` issue in the cached batch. Do not monkeypatch
   `update_workflow_label` itself — mock only at the GitHub-API boundary
   (`session_launch.PullRequestManager`/`BaseGitHubManager`, or patch
   `_build_pr_manager` directly, plus `IssueManager.transition_issue_label`
   and `load_labels_config`) so the real `update_workflow_label` body runs
   and the test would have caught the repo_url-mode bug fixed in step 1:
   - `find_pull_request_by_head` returns a `PullRequestData`-shaped dict
     with `"mergeable_state": "dirty"` → assert `transition_issue_label`
     was called with the issue's number and
     `"status-71:merge-conflict"`.
   - a second case with `"mergeable_state": "clean"` → assert
     `transition_issue_label` was *not* called.
   - a third case with `branch_manager.get_branch_with_pr_fallback`
     returning `None` → assert no `PullRequestManager`/
     `transition_issue_label` call happens at all.
   - a fourth case where `find_pull_request_by_head` raises → assert
     `process_eligible_issues` does not raise and existing issues are still
     processed normally.
   Confirm these fail against current code.
3. Implement `_build_pr_manager`, `_check_merge_conflict`, and the splice
   in `process_eligible_issues()` to make them pass.
4. Re-run the full `test_session_launch_process_issues.py` file and
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
> `pr_info/steps/step_5.md` exactly as written. Follow TDD: first add the
> repo_url-mode test to `tests/workflow_utils/test_label_transitions.py`
> and confirm it fails, then remove the `project_dir is None` guard in
> `update_workflow_label` (`src/mcp_coder/workflow_utils/label_transitions.py`)
> per the "Fix: `update_workflow_label` in repo_url mode" section and
> confirm it passes. Then add the new test cases to
> `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
> first and confirm they fail, then add `_build_pr_manager`,
> `_check_merge_conflict`, and the splice into `process_eligible_issues()`
> in `src/mcp_coder/workflows/vscodeclaude/session_launch.py` to make them
> pass, without breaking any existing test in either file. If this step's
> "Precondition check" section fails, write one line to
> `pr_info/.blocked.txt` and stop. Otherwise make one commit containing all
> the changes, after formatters/pylint/pytest/mypy all pass.
