# Step 4 — Coordinator runs PR-health in `_collect_work`; vscodeclaude stops

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_4.md`). Implement step 4 only,
> test-first: `_collect_work` in `src/mcp_coder/cli/commands/coordinator/commands.py` fetches all
> cached issues once per repo with `get_all_cached_issues`, filters eligible issues from that list,
> and — only when the cache worked — calls `check_pr_health`. Remove the call from vscodeclaude
> `launch`, delete `get_cached_eligible_issues`, and rewrite the coordinator tests that patched it.
> The multi-status-label ERROR is step 5, not this step. Run all checks from the summary; produce
> exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/coordinator/commands.py` (`_collect_work`, imports)
- `src/mcp_coder/cli/commands/coordinator/core.py` (delete `get_cached_eligible_issues`)
- `src/mcp_coder/cli/commands/coordinator/__init__.py` (drop its import and `__all__` entry)
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` (`_launch_for_repos`)
- Tests in `tests/cli/commands/coordinator/`: `conftest.py`, new `test_commands_pr_health.py`,
  `test_commands.py`, `test_integration.py`, `test_commands_capacity_gate.py`,
  `test_commands_dispatch_order.py`, `test_commands_trust_gate.py`, `test_core_eligibility.py`,
  `test_vscodeclaude_rate_limit.py`, `test_vscodeclaude_cli.py`; delete `test_vscodeclaude_pr_health.py`
- `vulture_whitelist.py` (`_no_pr_health` comment)

## WHAT

`commands.py` imports:
- add `get_all_cached_issues` to the `....mcp_workspace_github` import (tests patch
  `commands.get_all_cached_issues`);
- add `from ....workflows.pr_health import check_pr_health`;
- `.core`: replace `get_cached_eligible_issues` with `_filter_eligible_issues`.

`_collect_work` signature unchanged.

`_Repo`: replace the field `full_name: str` with `repo_identifier: RepoIdentifier` (its only reader is
the dispatch write-back). `_collect_work` stores the identifier it passes to `get_all_cached_issues`.
The dispatch write-back in `execute_coordinator_run` (`commands.py:475`) passes `repo.repo_identifier`
instead of `RepoIdentifier.from_full_name(repo.full_name)`, so a GitHub Enterprise repo reads and
writes the same issue-cache file (`from_full_name` always assumes github.com).

## ALGORITHM

Per repo, after the unchanged capacity gate and manager creation:
```
repo_identifier = RepoIdentifier.from_repo_url(repo_url)      # dead `except ValueError` fallback dropped
try:
    all_issues = get_all_cached_issues(repo_identifier, issue_manager=issue_manager,
                     force_refresh=force_refresh, cache_refresh_minutes=get_cache_refresh_minutes())
    eligible_issues = _filter_eligible_issues(all_issues)
except Exception as e:  # existing handler; also covers labels-config ValueError/KeyError/TypeError
    raise_if_rate_limited(e); logger.warning(...cache failed... using direct fetch)
    eligible_issues = get_eligible_issues(issue_manager)
else:
    check_pr_health(repo_name, validated_config, all_issues)
```
Then the existing `Found N eligible issues` log, `if not eligible_issues: continue`,
`_Repo(..., repo_identifier=repo_identifier, ...)`.
The `else` runs only when the `try` succeeded, and exceptions raised in it are not caught by the
`except` — a PR-health error never triggers the fallback; a `GitHubRateLimitError` propagates
(run ends with exit 0, no dispatch).

`_collect_work` docstring: "A rate limit during a fetch or from PR-health propagates"; mention that
PR-health runs per repo with capacity and a working issue cache, on the full cached list.

`core.py`: delete `get_cached_eligible_issues`; drop the then unused `get_all_cached_issues` import;
update the module docstring line "Issue filtering functions (including cached version via issue_cache)".

`commands_vscodeclaude.py`: remove the `check_pr_health` import and call (with its comment) from
`_launch_for_repos`; docstring first line → "Launch eligible issues per repo, then summarise."

## DATA

`_collect_work` return value unchanged: `list[tuple[IssueData, _Repo]]`.

## HOW — tests first

1. `conftest.py`: add autouse fixture `_no_pr_health` patching
   `mcp_coder.cli.commands.coordinator.commands.check_pr_health` with a `MagicMock` (yield it).
   New PR-health tests request `_no_pr_health` to inspect or configure it.
2. Remove the file-level `_no_pr_health` fixture from `test_vscodeclaude_cli.py` (same step —
   a file-level fixture with the same name would override the conftest one) and imports it alone used.
3. New `test_commands_pr_health.py` (cannot import from `tests.workflows` — import-linter
   `test_module_independence`; build issues with `tests.github_factories.make_issue_data`). Patch around
   `execute_coordinator_run` / `_collect_work` like `test_commands_capacity_gate.py` does
   (`get_all_cached_issues`, `get_eligible_issues`, `IssueManager`, `IssueBranchManager`, `JenkinsClient`,
   `load_repo_config`, `validate_repo_config`, `dispatch_workflow`, `update_issue_labels_in_cache`, ...).
   Cases:
   - called once per repo with capacity, with `(repo_name, validated_config, full cached list)` —
     the list includes an unassigned `status-10` issue and a closed issue;
   - not called for a repo whose executor job is busy, and `get_all_cached_issues` not called for it;
   - cache failure (`get_all_cached_issues` raises `RuntimeError`) → `get_eligible_issues` used,
     `check_pr_health` not called;
   - `check_pr_health` raises `GitHubRateLimitError` → exit 0, `dispatch_workflow` not called;
   - `check_pr_health` raises `RuntimeError` → the error propagates out of `execute_coordinator_run`
     (its final `except Exception` logs "Unexpected error" and re-raises, as for any other
     non-rate-limit error): assert `pytest.raises(RuntimeError)`, `get_eligible_issues` not called
     (no fallback) and `dispatch_workflow` not called;
   - `_filter_eligible_issues` raises `KeyError` (labels-config error; patch
     `commands._filter_eligible_issues`) → `get_eligible_issues` called (direct-fetch fallback),
     `check_pr_health` not called. Replaces the deleted
     `test_get_cached_eligible_issues_fallback_on_error`.
4. Rewrite each `patch(...commands.get_cached_eligible_issues)` to `get_all_cached_issues` in
   `test_commands.py`, `test_integration.py`, `test_commands_capacity_gate.py`,
   `test_commands_dispatch_order.py`, `test_commands_trust_gate.py`. Not a rename:
   - the `RepoIdentifier` is positional: side effects reading `kwargs["repo_full_name"]` read
     `args[0].full_name` (e.g. `def fetch(identifier, **kwargs)`); assertions on
     `call_args[1]["repo_full_name"]` become `call_args.args[0].full_name`;
   - results now pass through the real `_filter_eligible_issues`: fixture issues must be open
     (`make_issue_data` default) and carry exactly one bot_pickup label, no ignore label.
   - `_Repo` field rename: `_Repo(full_name="user/repo_a", ...)` in `test_commands_capacity_gate.py`
     → `repo_identifier=RepoIdentifier.from_full_name("user/repo_a")`; `r.full_name` in
     `test_commands_dispatch_order.py` → `r.repo_identifier.full_name`.
   - In `test_commands.py::TestExecuteCoordinatorRun::test_execute_coordinator_run_single_repo_success`
     (also patch `commands.update_issue_labels_in_cache`) assert that every dispatch cache update
     gets the same `RepoIdentifier` that was passed to `get_all_cached_issues`:
     `all(c.args[0] is get_all_cached.call_args.args[0] for c in update_cache.call_args_list)`
     (and `update_cache.call_count == 2`).
5. `test_core_eligibility.py`: delete the `get_cached_eligible_issues` test class and import (its
   filter-error fallback case is replaced by the `KeyError` case in `test_commands_pr_health.py`).
6. `test_vscodeclaude_rate_limit.py`: remove `check_pr_health` from `launch_mocks` and every
   `check_pr_health` assertion. `test_pr_health_limit_stops_before_next_repo` → delete (covered by
   `test_wrapped_limit_in_launch_exits_zero`). `test_later_repo_limit_still_reports_started_sessions` →
   `process_eligible_issues.side_effect = [[started], _rest_rate_limit()]`, `call_count == 2`.
   `test_other_error_is_reraised` → `process_eligible_issues.side_effect = RuntimeError("boom")`.
7. Delete `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` (remaining
   `TestPrHealthOutsideCapacityGate` is obsolete).
8. `vulture_whitelist.py`: the `_no_pr_health` comment path becomes
   `tests/cli/commands/coordinator/conftest.py` ("stubbing check_pr_health so coordinator tests never
   run real PR-health checks").
9. Then implement as in ALGORITHM; run all checks.

## Verify

- `mcp__mcp-workspace__search_files` for `get_cached_eligible_issues` → no match in `src/` or `tests/`.
- If a test relied on the removed `except ValueError: repo_full_name = repo_name` fallback in a way
  that cannot be rewritten without changing production behaviour, write one line to
  `pr_info/.blocked.txt` and stop.
