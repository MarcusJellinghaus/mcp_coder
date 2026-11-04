# Step 1: Coordinator `_check_alerts`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, and GitHub issue #1342 §1 and "Test
> gotchas". Implement this step with TDD: write the tests first, then the code. Run
> `run_format_code`, pylint, mypy, ruff and pytest (`-n auto`, unit-test markers); all must
> pass. Produce exactly one commit. Do not edit `pr_info/TASK_TRACKER.md`.

## Precondition

`PullRequestCache` in the installed mcp-workspace must have an `alerts` method (check with
`get_library_source`). If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/checks.py`
- New: `tests/workflows/vscodeclaude/test_checks_alerts.py`
- `tests/workflows/vscodeclaude/test_checks.py` (`_default_mocks`)
- `tests/workflows/vscodeclaude/test_checks_pr_cache.py`
- `tests/workflows/vscodeclaude/test_checks_review_comments_trust.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`

## WHAT

```python
def _check_alerts(
    issue: IssueData,
    pr: OpenPullRequest,
    pr_cache: PullRequestCache,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
    trusted: frozenset[str],
) -> bool:
    """Escalate a status-10 PR to status-91 on open code-scanning alerts."""
```

## HOW

- Add it to the `check_pr_health` chain between `_check_ci` and `_check_review_comments`,
  guarded by `pr is not None`, passing `label_names["pr_review_comments"]` and `trusted`.
- Escalate with the existing `_escalate(issue, issue_manager, "pr_review_comments",
  target_label_name, repo_name)`.
- Reword the OUTPUT line in `_check_review_comments` to `... untrusted PR author @%s —
  review comments and alerts not checked`.
- Module docstring becomes "merge conflicts, CI, code-scanning alerts, and review
  comments". The `check_pr_health` docstring lists: merge conflict, failing CI, alerts,
  review comments.
- Do not change `mcp_workspace_github.py`. Do not import `AlertsResult`.

## ALGORITHM

```
try:
    if PR author not trusted: return False      # silent; review-comments logs the line
    result = pr_cache.alerts(pr, issue)
    if not (result["final"] and result["alerts"]): return False
    _escalate(...); return True
except Exception: raise_if_rate_limited(exc); log warning; return False
```

## DATA

`pr_cache.alerts()` returns a mapping: `{"alerts": list, "skipped": int | None, "final":
bool}`. Skipped and not-final results always have `alerts == []`. `_check_alerts` returns
True only if a label update was attempted.

## Tests (write first)

Change `_default_mocks()` first: `pr_cache.alerts.return_value = {"alerts": [], "skipped":
None, "final": True}`.

In `test_checks_alerts.py`, reuse the helpers from `test_checks.py` (`_setup`, `_make_pr`,
`_make_pr_issue`), as `test_checks_pr_cache.py` does:

- Alerts, no other feedback, CI green → escalates to `status-91`.
- Alerts, untrusted PR author → no escalation; through `check_pr_health`, exactly one OUTPUT
  line, the reworded one.
- `{"alerts": [...], "final": False}` → no escalation.
- `final=True` while `ci_status` reports `in_progress` (a run concluded `skipped`) → escalates.
- `{"alerts": [], "skipped": 403, "final": True}` and the same with 404 → no escalation, no
  OUTPUT line.
- `alerts()` raises `RuntimeError` → warning logged, `_check_review_comments` still runs.
- `alerts()` raises `AttributeError` (old mcp-workspace) → same as above.
- `alerts()` raises `GitHubRateLimitError` → propagates.
- Merge conflict or failing CI hit → `alerts()` not called.
- No open PR → `alerts()` not called.

Update existing tests:

- `test_checks_review_comments_trust.py`: the assertion on the old wording.
- `test_checks_pr_cache.py::test_all_five_queries_go_to_cache`: add the alerts query and
  rename to `test_all_six_queries_go_to_cache`.
- `TestPrHealthWarmCacheCallCount`: stub
  `mcp_workspace.github_operations._pr_feedback_sources.fetch_code_scanning_alerts` and assert
  the second run makes no alerts request.
