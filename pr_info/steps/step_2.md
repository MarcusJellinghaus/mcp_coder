# Step 2 — `check_pr_health` with a shared lookup (still called from `process_eligible_issues`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Work test-first: rewrite / add the tests listed under "Tests" so they fail, then change
> the source until they pass. Keep the "never raises" and "at most one action per issue
> per poll" guarantees. Do not touch the CLI call site yet — that is step 3. Run pylint,
> pytest (fast unit tests, `-n auto`), mypy, lint-imports and tach; all must pass. Format,
> then make exactly one commit.

## WHERE

Source:
- `src/mcp_coder/workflows/vscodeclaude/checks.py`
- `src/mcp_coder/workflows/vscodeclaude/__init__.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (check loop → `checks.check_pr_health` call)

Tests:
- `tests/workflows/vscodeclaude/test_checks.py` (rewrite)
- `tests/workflows/vscodeclaude/test_checks_review_comments.py` (rewrite)
- `tests/workflows/vscodeclaude/test_checks_orchestration.py` (create only if `test_checks.py` > 750 lines)
- `tests/workflows/vscodeclaude/test_session_launch.py`, `test_session_launch_process_issues.py`,
  `test_session_restart_branch_integration.py` (interim `checks.check_pr_health` patch)

## WHAT — `checks.py`

New imports: `PullRequestData` (from `...mcp_workspace_github`), `build_label_lookups`,
`get_labels_config_path`, `load_labels_config` (from `...config.label_config`),
`OUTPUT` (from `...utils.log_utils`), `get_github_username`, `get_repo_full_name` (from `.config`),
`get_issue_status` (from `.helpers`), `_filter_eligible_vscodeclaude_issues` (from `.issues`).
`.issues` imports only `.config` / `.helpers`, so there is no import cycle.

```python
def _escalate(
    issue: IssueData,
    issue_manager: IssueManager,
    to_label_id: str,
    to_label_name: str,
    repo_name: str,
) -> None:
    """Set the escalation label; log one OUTPUT line only if the update succeeded."""

def _resolve_pr_target(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    pr_manager: PullRequestManager,
    repo_owner: str,
    repo_gh_name: str,
) -> tuple[str | None, PullRequestData | None]:
    """Resolve an issue's branch and open PR once. Never raises."""

def _check_merge_conflict(
    issue: IssueData,
    pr: PullRequestData,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool: ...

def _check_ci(
    issue: IssueData,
    branch: str,
    ci_manager: CIResultsManager,
    issue_manager: IssueManager,
    repo_name: str,
    target_label_name: str,
) -> bool: ...

def _check_review_comments(
    issue: IssueData,
    pr: PullRequestData,
    pr_manager: PullRequestManager,
    issue_manager: IssueManager,
    repo_name: str,
    review_label_name: str,   # also the target label name
    created_label_name: str,
) -> bool: ...

def check_pr_health(
    repo_name: str,
    repo_config: dict[str, str],
    all_cached_issues: list[IssueData],
) -> None:
    """Run PR-health checks on the repo's status-10 issues. Never raises."""
```

`_build_pr_manager` and `_review_comments_watermark` stay unchanged.

## ALGORITHM

`_escalate`:
```
if update_workflow_label(issue_manager, "pr_created", to_label_id, validated_issue_number=n):
    logger.log(OUTPUT, "PR-health: %s #%d → %s", repo_name, n, to_label_name)
```

`_resolve_pr_target`:
```
try: branch = branch_manager.get_branch_with_pr_fallback(n, owner, gh_name)
except Exception: warn("Failed to resolve branch for issue #%d"); return None, None
if branch is None: return None, None
try: prs = pr_manager.find_pull_request_by_head(branch)
except Exception: warn("Failed to look up PR for issue #%d"); return branch, None
return branch, (prs[0] if prs else None)
```

Checks — the body of each existing check minus its lookups; on a hit:
`_escalate(...); return True`. The existing `try/except Exception → warning → return False`
stays around each check's own API call and label update:
- conflict: `pr["mergeable_state"] == "dirty"` → `merge_conflict`
- CI: `ci_manager.get_latest_ci_status(branch)` completed and not success → `failing_ci`
- review: `pr_manager.get_pr_feedback(pr["number"])` + watermark logic unchanged → `pr_review_comments`

`check_pr_health`:
```
try:
    username = get_github_username()
    pr_issues = [i for i in _filter_eligible_vscodeclaude_issues(all_cached_issues, username)
                 if get_issue_status(i) == "status-10:pr-created"]
    if not pr_issues: return
    full = get_repo_full_name(repo_config); owner, gh_name = full.split("/", 1)
    url = f"https://github.com/{full}"
    issue_mgr, branch_mgr, ci_mgr = IssueManager(repo_url=url), IssueBranchManager(repo_url=url), CIResultsManager(repo_url=url)
    pr_mgr = _build_pr_manager(url)
    names = build_label_lookups(load_labels_config(get_labels_config_path(None)))["id_to_name"]
except Exception as exc:
    logger.warning("PR-health: skipping repo %s: %s", repo_name, exc); return
for issue in pr_issues:
    branch, pr = _resolve_pr_target(issue, branch_mgr, pr_mgr, owner, gh_name)
    if branch is None: continue
    _ = ((pr is not None and _check_merge_conflict(issue, pr, issue_mgr, repo_name, names["merge_conflict"]))
         or _check_ci(issue, branch, ci_mgr, issue_mgr, repo_name, names["failing_ci"])
         or (pr is not None and _check_review_comments(issue, pr, pr_mgr, issue_mgr, repo_name,
                                                       names["pr_review_comments"], names["pr_created"])))
```

## HOW — integration

- `workflows/vscodeclaude/__init__.py`: `from .checks import check_pr_health`, add `"check_pr_health"` to `__all__`.
- `session_launch.py` / `process_eligible_issues()` (interim; step 3 moves the call to the CLI):
  - replace the `repo_owner, repo_name_str = ...` line and the
    `for issue in eligible_issues: if ... "status-10:pr-created": ...` check loop with
    `checks.check_pr_health(repo_name, repo_config, all_cached_issues)` — at the same place,
    i.e. after the cache fallback, so `all_cached_issues` is never `None`
  - delete the now-dead locals `ci_manager`, `label_lookups`, `review_label_name`,
    `created_label_name` (pylint `unused-variable`)
  - keep the module imports (`CIResultsManager`, `...config.label_config`, `from . import checks`):
    existing tests still patch `session_launch.CIResultsManager`; step 3 removes imports and patches together
  - keep the capacity early return, `issue_manager`, `branch_manager`
- Remaining `process_eligible_issues` tests in `test_session_launch.py`,
  `test_session_launch_process_issues.py` and `test_session_restart_branch_integration.py`:
  patch `mcp_coder.workflows.vscodeclaude.checks.check_pr_health` (with a `MagicMock`), via a
  per-file autouse fixture or per-test `monkeypatch.setattr`. Without it, the interim call
  reaches `checks.get_github_username` (a real GitHub API call) and the real managers, because
  those tests only patch the `session_launch.*` names. Step 3 removes this patch together with
  the interim call.

## DATA

- `_resolve_pr_target` → `(branch, pr)`: `(None, None)` = skip the issue; `(branch, None)` = CI only.
- Checks → `bool`: `True` iff a problem was detected (label update attempted), which stops the chain.
- `check_pr_health` → `None`.
- OUTPUT line: `PR-health: <config repo_name> #<n> → <label name>`, e.g.
  `PR-health: test-repo #999 → status-71:merge-conflict`.

## Tests (write first)

All tests in this step call `check_pr_health` or the `_check_*` / `_resolve_pr_target` helpers
directly — none go through `process_eligible_issues`.

Shared helpers at the top of `test_checks.py` (module-level, replacing the class methods):
- `MOCK_MERGE_CONFLICT_LABELS_CONFIG`, `MOCK_CI_LABELS_CONFIG` (unchanged; they feed only
  `mcp_coder.workflow_utils.label_transitions.load_labels_config`; `check_pr_health` reads the real config)
- `_make_pr_issue(number, labels=["status-10:pr-created"]) -> IssueData`
- `_patch_env(monkeypatch, issues, *, issue_manager, branch_manager, ci_manager, pr_manager, labels_config=MOCK_CI_LABELS_CONFIG)`
  patching in `mcp_coder.workflows.vscodeclaude.checks`: `IssueManager`, `IssueBranchManager`,
  `CIResultsManager` (each `lambda **kw: <mock>`), `_build_pr_manager` (`lambda repo_url: pr_manager`),
  `get_github_username` (`lambda: "testuser"`), `_filter_eligible_vscodeclaude_issues`
  (`lambda issues, user: issues`); plus `label_transitions.load_labels_config`.
  Default mocks: `transition_issue_label.return_value = True`, `project_dir = None`,
  CI `{"run": {}, "jobs": []}`, PR `[{"number": 1, "mergeable_state": "clean"}]`, feedback empty.
- Call `check_pr_health("test-repo", {"repo_url": "https://github.com/owner/repo"}, [issue])`.

`test_checks.py` — orchestration (`TestCheckPrHealth`), rewritten from the moved process tests:
- dirty PR → `transition_issue_label(999, "status-71:merge-conflict", ...)`
- clean PR, green CI, no feedback → no transition
- failed CI → `status-81:failing-ci`; successful / in-progress CI → no transition; CI exception swallowed
- dirty PR → `get_latest_ci_status` and `get_pr_feedback` not called
- failed CI → `get_pr_feedback` not called
- no branch → `find_pull_request_by_head` and `get_latest_ci_status` not called (no assertion on `_build_pr_manager`)
- no PR found → `get_latest_ci_status` called, `get_pr_feedback` not called, no conflict transition
- non-`status-10` issues only → managers / `_build_pr_manager` not built (patch with `MagicMock` and assert not called)
- setup failure: `get_github_username` raises → no exception, a WARNING is logged
- one lookup per issue: `get_branch_with_pr_fallback` and `find_pull_request_by_head` each called once

`test_checks.py` — `TestResolvePrTarget` (call `_resolve_pr_target` directly):
- branch lookup raises (`side_effect=ValueError`) → `(None, None)`, WARNING logged, PR lookup not called
- no branch → `(None, None)`, PR lookup not called
- PR lookup raises → `(branch, None)`, WARNING logged
- no PR → `(branch, None)`; PR found → `(branch, prs[0])`
- via `check_pr_health`: PR lookup raises → CI still checked, `get_pr_feedback` not called, no conflict transition

`test_checks.py` — `TestCheckCi` (moved from `TestCheckCiReturnValue` in `test_checks_review_comments.py`,
call `_check_ci(issue, "123-fix", ci_manager, issue_manager, "test-repo", "status-81:failing-ci")`):
- failed → `True`; success / in-progress → `False`; exception → `False`
- drop `test_returns_false_when_no_branch`

`test_checks.py` — `TestPrHealthOutput` (caplog on logger `mcp_coder.workflows.vscodeclaude.checks`,
filter records by `levelno == OUTPUT` from `mcp_coder.utils.log_utils`):
- escalation → exactly one OUTPUT record `PR-health: test-repo #999 → status-71:merge-conflict`
- no escalation → no OUTPUT record
- `transition_issue_label.return_value = False` → no OUTPUT record, and `_check_merge_conflict` still returns `True`

`test_checks_review_comments.py`:
- `TestReviewCommentsWatermark` unchanged
- `TestCheckReviewComments`: call `_check_review_comments(issue, {"number": 1}, pr_manager, issue_manager,
  "test-repo", REVIEW_LABEL, CREATED_LABEL)`; no branch-manager mocks, no `_build_pr_manager` patch
- drop `test_no_branch_returns_false_never_calls_feedback` and `test_no_pr_found_returns_false`
- delete `TestProcessEligibleIssuesPriorityChaining` (both tests). It is not rewritten: its two
  cases are already covered by the `TestCheckPrHealth` chaining tests in `test_checks.py`
  ("dirty PR → `get_latest_ci_status` and `get_pr_feedback` not called", "failed CI →
  `get_pr_feedback` not called")
- remove `TestCheckCiReturnValue` (moved to `TestCheckCi`); drop the now-unused imports
  (`process_eligible_issues`, `_check_ci`, `.test_checks`)

Remove:
- `test_pr_lookup_failure_does_not_raise_and_other_issues_still_processed`

If `test_checks.py` exceeds 750 lines, move `TestCheckPrHealth` and `TestPrHealthOutput` (plus the
helpers they need, importing shared ones from `.test_checks`) into `test_checks_orchestration.py`.
Check with `mcp__mcp-workspace__check_file_size(max_lines=750)`.

## Commit

`refactor(vscodeclaude): add check_pr_health with a shared branch/PR lookup (#1238)`
