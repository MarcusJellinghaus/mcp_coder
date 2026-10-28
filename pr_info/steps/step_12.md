# Step 12 — Branch lookups use `BranchLookupCache` (four call sites)

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_12.md`).
> Implement only Step 12. Tests first, then code.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/mcp_workspace_github.py` (re-exports)
- `src/mcp_coder/workflows/vscodeclaude/issues.py` (new helper + `build_eligible_issues_with_branch_check`)
- `src/mcp_coder/workflows/vscodeclaude/checks.py` (`_resolve_pr_target`, `check_pr_health`)
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (`process_eligible_issues`)
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` (`restart_closed_sessions`, `_prepare_restart_branch`)
- tests: `test_issues_branch_check.py`, `test_checks.py`, `test_session_launch_process_issues.py`,
  `test_session_restart_prepare_branch.py`, `test_session_restart_branch_integration.py`,
  `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py`

## WHAT
Shim re-exports (`__all__` too): `BranchLookupCache` (from
`mcp_workspace.github_operations.caching.branches`), `BranchLookup`,
`BranchLookupError` (from `mcp_workspace.github_operations.issues`).

One helper in `issues.py`:
```python
def lookup_branch(cache: BranchLookupCache, issue: IssueData) -> str | None:
    """Return the issue's single branch, or None for not_found/ambiguous/lookup errors.

    Raises:
        GitHubRateLimitError: On a rate limit (propagates).
    """
    try:
        return cache.lookup(issue).branch
    except (BranchLookupError, ValueError, GithubException) as exc:
        logger.warning("Branch lookup failed for issue #%d: %s", issue["number"], exc)
        return None
```
(`lookup` already converts rate limits into `GitHubRateLimitError`, which none
of these classes catch.)

Call sites — one cache per repo per function, `save()` once at the end:
- `build_eligible_issues_with_branch_check`: `branch_cache = BranchLookupCache.load(IssueBranchManager(repo_url=repo_url))`
  replaces `branch_manager`; inside the loop `branch = lookup_branch(branch_cache, issue)`;
  `branch_cache.save()` after the loop (inside the repo `try`).
- `check_pr_health` / `_resolve_pr_target`: parameter `branch_cache: BranchLookupCache`
  replaces `branch_manager`, `repo_owner`, `repo_gh_name`; `branch = lookup_branch(branch_cache, issue)`;
  `branch_cache.save()` next to `pr_cache.save()`.
- `process_eligible_issues`: cache replaces `branch_manager`; `branch_name = lookup_branch(branch_cache, issue)`;
  `branch_cache.save()` after the loop.
- `session_restart`:
  - `restart_closed_sessions`: `branch_caches: dict[str, BranchLookupCache] = {}` before the loop;
    per session (load lazily, so no manager is built per session):
    ```python
    branch_cache = branch_caches.get(repo_full_name)
    if branch_cache is None:
        branch_cache = BranchLookupCache.load(IssueBranchManager(repo_url=repo_url))
        branch_caches[repo_full_name] = branch_cache
    ```
    replacing the per-session `IssueBranchManager(...)` (~386);
    after the loop `for cache in branch_caches.values(): cache.save()`.
  - `_prepare_restart_branch(folder_path, current_status, branch_cache, issue)`:
    `linked_branch = lookup_branch(branch_cache, issue)`; `None` → `BranchPrepResult(False, "No branch", None)`.
    `repo_owner` / `repo_name` / `issue_number` parameters go away (`issue["number"]` where needed).
- Stay live (unchanged): coordinator `dispatch_workflow` lookup,
  `_handle_intervention_mode` (`--intervene`).

## HOW
- `lookup_branch` is imported by `checks.py`, `session_launch.py`, `session_restart.py`
  from `.issues` (no new module).
- Tests (TDD):
  - `lookup_branch`: found → branch; `not_found` / `ambiguous` → `None`;
    `BranchLookupError` / `ValueError` / `GithubException(500)` → `None` + WARNING;
    `GitHubRateLimitError` → propagates.
  - per call site: a `BranchLookupError` for issue 1 → treated as "no branch",
    issue 2 still processed (acceptance); a `GitHubRateLimitError` → propagates;
    `save()` called once per repo.
  - restart: one `BranchLookupCache.load` per repo for two sessions of the same repo.
  - **Call-count test** (acceptance, in `test_vscodeclaude_pr_health.py`):
    real `PullRequestCache` + `BranchLookupCache` on a `tmp_path` cache dir
    (patch the cache-dir location used by `cache_file_path`), a mocked
    `Repository`; warm caches from a run whose snapshot is older than 60 s;
    all PRs open, CI final, issues unchanged → second `check_pr_health` makes
    ≈ 2 `core` calls (open-PR list + base tip) and no branch-resolution or
    label-event calls. A status-10 issue without an open PR still calls
    `get_latest_ci_status` live.

## DATA
`lookup_branch -> str | None`; `BranchLookup(status, branch)` NamedTuple.
