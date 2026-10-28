# Step 11 — `check_pr_health` uses `PullRequestCache`

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_11.md`).
> Implement only Step 11. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/mcp_workspace_github.py` (re-exports)
- `src/mcp_coder/workflows/vscodeclaude/checks.py`
- tests: `tests/workflows/vscodeclaude/test_checks.py`, `test_checks_review_comments.py`,
  `test_checks_review_comments_trust.py`, `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`

## WHAT
Shim: re-export `PullRequestCache` and `OpenPullRequest` from
`mcp_workspace.github_operations.caching.pull_requests` (import the submodule
directly; `caching/__init__.py` is import-free). Add to `__all__`.

`checks.py` — `pr` becomes `OpenPullRequest`; every PR query goes through one
run-scoped cache per repo:

| Today | After |
|---|---|
| `pr_manager.find_pull_request_by_head(branch)` | `pr_cache.find_pr(branch)` |
| `pr["mergeable_state"]` | `pr_cache.mergeable_state(pr, issue)` |
| `_check_ci`: `ci_manager.get_latest_ci_status(branch)` | `pr_cache.ci_status(pr, issue)` if `pr` else live `ci_manager.get_latest_ci_status(branch)` |
| `pr_manager.get_pr_feedback(pr["number"])` | `pr_cache.feedback(pr, issue)` (alerts already excluded) |
| `issue_manager.get_issue_events(n, LABELED)` | `pr_cache.label_events(pr, issue)` — still only when `items` is non-empty |

New signatures:
```python
def _resolve_pr_target(issue, branch_manager, pr_cache: PullRequestCache, repo_owner, repo_gh_name)
    -> tuple[str | None, OpenPullRequest | None]
def _check_merge_conflict(issue, pr: OpenPullRequest, pr_cache, issue_manager, repo_name, target_label_name) -> bool
def _check_ci(issue, branch, pr: OpenPullRequest | None, pr_cache, ci_manager, issue_manager, repo_name, target_label_name) -> bool
def _check_review_comments(issue, pr: OpenPullRequest, pr_cache, issue_manager, repo_name,
                           review_label_name, created_label_name, trusted) -> bool
```
`issue_manager` stays only for `_escalate` (live label updates).

## ALGORITHM (`check_pr_health`)
```
setup (unchanged) + pr_cache = PullRequestCache.load(PullRequestManager(repo_url=repo_url))
try:
    for issue in pr_issues:
        branch, pr = _resolve_pr_target(...)   # find_pr non-rate-limit error → (branch, None) → CI-only
        if branch is None: continue
        merge-conflict (pr) or CI (pr or live) or review comments (pr)
finally:
    pr_cache.save()   # keeps fetched PR results when a rate limit came from elsewhere;
                      # no-op after the cache's own rate limit
```

## HOW
- `PullRequestManager(repo_url=...)` no longer needs a `project_dir` (Step 4).
- Keep the per-check `except` blocks (with Step 9's `raise_if_rate_limited`).
- Update the "Never raises" docstrings of `check_pr_health` and
  `_resolve_pr_target` (rate limits propagate; `find_pr` errors degrade to CI-only).
- Tests (TDD), patch `PullRequestCache` / `PullRequestManager` in the `checks` module:
  - each of the five calls goes to the cache (assert calls with `(pr, issue)`);
  - no open PR → `ci_manager.get_latest_ci_status(branch)` called live;
  - `find_pr` raises `RuntimeError` → CI-only check, other issues still processed;
  - `label_events` not called when there are no feedback items;
  - `save()` called once after the loop; a rate limit raised outside the cache
    (e.g. `_escalate`) → propagates, `save()` still called once (try/finally);
    rate limit from `find_pr` → propagates (the real cache's `save()` is then a no-op);
  - update existing fixtures from `PullRequestData` dicts to `OpenPullRequest`
    (`number`, `head_branch`, `head_sha`, `head_label`, `base_branch`, `updated_at`,
    `user`, `author_association`, `draft`).

## DATA
`OpenPullRequest` TypedDict (see summary); `PRFeedback` keys used:
`unresolved_threads`, `changes_requested`, `conversation_comments`.
