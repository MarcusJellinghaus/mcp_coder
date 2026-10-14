# Step 2 — CI detection in the VSCodeClaude coordinator poll

See [summary.md](./summary.md) for full context. Depends on Step 1 (labels
must exist).

## Precondition

`mcp_workspace.github_operations.CIResultsManager.__init__` must accept a
`repo_url: Optional[str]` keyword argument directly (no `project_dir`
required). If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

`src/mcp_coder/workflows/vscodeclaude/session_launch.py` (modify)

## WHAT

```python
def _check_merge_conflict(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> bool:
    """Escalate to status-71 if dirty. Returns True iff it escalated."""

def _check_ci(
    issue: IssueData,
    ci_manager: CIResultsManager,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> None:
    """Escalate a status-10 PR to status-81 if its latest CI run failed."""
```

## HOW

- Import `CIResultsManager` from `...mcp_workspace_github` (already imports
  `BaseGitHubManager`, `IssueBranchManager`, `IssueData`, `IssueManager`,
  `PullRequestManager`, `RepoIdentifier`, `get_all_cached_issues` from there —
  add `CIResultsManager` to that same import block).
- In `process_eligible_issues()`, build `ci_manager = CIResultsManager(repo_url=repo_url)`
  once per repo, right next to the existing `issue_manager = IssueManager(repo_url=repo_url)`
  and `branch_manager = IssueBranchManager(repo_url=repo_url)` lines — not
  inside `_check_ci()` and not per issue.
- Change the per-issue loop from:
  ```python
  for issue in eligible_issues:
      if get_issue_status(issue) == "status-10:pr-created":
          _check_merge_conflict(issue, branch_manager, issue_manager, repo_owner, repo_name_str)
  ```
  to:
  ```python
  for issue in eligible_issues:
      if get_issue_status(issue) == "status-10:pr-created":
          escalated = _check_merge_conflict(
              issue, branch_manager, issue_manager, repo_owner, repo_name_str
          )
          if not escalated:
              _check_ci(
                  issue, ci_manager, branch_manager, issue_manager, repo_owner, repo_name_str
              )
  ```
- `_check_merge_conflict()`'s body is unchanged except: `return True` right
  after the `update_workflow_label(...)` call inside the `if prs and
  prs[0]["mergeable_state"] == "dirty":` branch, and `return False` at the
  very end of the `try` block (both existing early-return points — the
  `except` branch logs and falls through to implicitly return `False`, which
  is correct: a failed *check* should not block the CI check this poll).

## ALGORITHM (`_check_ci`)

```
branch = branch_manager.get_branch_with_pr_fallback(issue.number, owner, repo)
if branch is None: return                      # no PR/branch — nothing to check
status = ci_manager.get_latest_ci_status(branch)
run = status.get("run", {})
if run.get("status") == "completed" and run.get("conclusion") != "success":
    update_workflow_label(issue_manager, "pr_created", "failing_ci",
                           validated_issue_number=issue.number)
# any other run shape (pending, no run, missing fields) -> no-op
```
Wrap the whole body in the same non-blocking
`try: ... except Exception: logger.warning(...)` shape `_check_merge_conflict`
already uses — one bad issue must never block the rest of the batch.

## DATA

`_check_ci` returns `None` (side effect only: label transition or nothing).
`_check_merge_conflict` now returns `bool` (`True` = escalated to
`merge_conflict` this call, `False` = left alone or check failed).

## Test-first steps

Add to `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`,
in a new `TestProcessEligibleIssuesCIDetection` class next to the existing
`TestProcessEligibleIssuesMergeConflictDetection` (reuse its
`_make_pr_issue`/`_setup_common_mocks` helpers, extended with a
`MOCK_CI_LABELS_CONFIG` dict adding the `failing_ci` label the same way
`MOCK_MERGE_CONFLICT_LABELS_CONFIG` adds `merge_conflict`):

1. `test_failed_ci_run_transitions_to_failing_ci` — mock
   `_build_pr_manager`'s PR lookup as clean (no conflict escalation), mock
   `CIResultsManager` (patch the class at
   `mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager`) so
   `get_latest_ci_status` returns
   `{"run": {"status": "completed", "conclusion": "failure"}, "jobs": []}`;
   assert `transition_issue_label` called once with the issue number and
   `"status-81:failing-ci"`.
2. `test_successful_ci_run_does_not_transition` — same setup but
   `conclusion: "success"`; assert `transition_issue_label` not called.
3. `test_pending_ci_run_does_not_transition` — `status: "in_progress"`,
   `conclusion: None`; assert not called.
4. `test_merge_conflict_escalation_skips_ci_check_same_poll` — PR is dirty
   (conflict escalates); assert `CIResultsManager.get_latest_ci_status` is
   never called (patch it and assert `assert_not_called()`).
5. `test_ci_manager_exception_is_swallowed` — `get_latest_ci_status` raises;
   assert `process_eligible_issues` does not raise and
   `transition_issue_label` is not called.

Run these — confirm they fail (red, `_check_ci` doesn't exist yet / loop
doesn't skip). Then implement the changes above. Re-run — confirm green.
Also re-run the existing `TestProcessEligibleIssuesMergeConflictDetection`
tests unchanged — they must still pass (the `clean`/`dirty` tests implicitly
now also exercise the `not escalated` branch, which calls `CIResultsManager`;
patch it in `_setup_common_mocks` with a default "no run" `CIStatusData` so
those pre-existing tests don't need individual changes).

## Checks

`run_pytest_check`, `run_pylint_check`, `run_mypy_check` — all pass. Then
`run_format_code`, then commit.

## Commit

One commit: `feat(vscodeclaude): detect failing CI on status-10 PRs`.

## LLM Prompt

> Implement Step 2 of the plan in `pr_info/steps/summary.md`. Read that
> summary first, then follow `pr_info/steps/step_2.md` exactly: write the
> new tests in `tests/workflows/vscodeclaude/test_session_launch_process_issues.py`
> first (red), then change `_check_merge_conflict()` to return `bool` and add
> `_check_ci()` in `src/mcp_coder/workflows/vscodeclaude/session_launch.py`,
> wiring it into `process_eligible_issues()` exactly as specified (green). If
> the precondition at the top of step_2.md does not hold, write one line to
> `pr_info/.blocked.txt` and stop. Run pytest/pylint/mypy, format, and
> produce exactly one commit.
