# Summary: Reduce GitHub API traffic (mcp-coder side) — issue #1300

## Goal

The every-minute commands (`coordinator --all`, `vscodeclaude status`,
`vscodeclaude launch --cleanup`) share one 5000/h `core` budget. This change:

1. wires the mcp-workspace **traffic log** (config keys + command name),
2. **stops on the first rate-limit error** instead of swallowing it and
   sending more failing requests (exit 0, except coordinator partial dispatch),
3. makes a failed **final workflow label update** a red build (retry once, then
   non-zero exit, without triggering the `run_guarded` safety net),
4. fixes the **`IssueBranchManager` both-arguments bug**,
5. routes PR-health and branch lookups through the mcp-workspace **disk caches**
   (`PullRequestCache`, `BranchLookupCache`).

All mcp-workspace APIs used here are on mcp-workspace `main` (W-1/W-2/W-3) and
were verified in the installed package:

| Name | mcp-workspace location |
|---|---|
| `set_traffic_log_context` | `mcp_workspace.traffic_log` |
| `GitHubRateLimitError` | `mcp_workspace.github_operations` (top level) |
| `to_rate_limit_error` | `mcp_workspace.github_operations.caching.errors` |
| `BranchLookupCache` | `mcp_workspace.github_operations.caching.branches` |
| `PullRequestCache`, `OpenPullRequest` | `mcp_workspace.github_operations.caching.pull_requests` |
| `BranchLookup`, `BranchLookupError`, `get_issue_cache_last_checked` | `mcp_workspace.github_operations.issues` |

Important library facts:
- Manager methods (`_handle_github_errors`) re-raise rate limits as the **raw**
  `GithubException` / `RetryError`, not as `GitHubRateLimitError`.
- `get_authenticated_username` (`GET /user`, our `get_github_username`) wraps a
  rate limit in a plain `ValueError` whose `__cause__` is the original.
- `BranchLookupCache.lookup` / `PullRequestCache.*` raise `GitHubRateLimitError`
  on a rate limit; `save()` is a no-op afterwards.

## Architectural / design changes

### 1. One rate-limit helper module (new)
`src/mcp_coder/workflow_utils/rate_limit.py`:
- `as_rate_limit(exc) -> GitHubRateLimitError | None` — recognises
  `GitHubRateLimitError`, raw rate-limit exceptions (via `to_rate_limit_error`)
  and a rate limit wrapped as `__cause__` (the `GET /user` case).
- `raise_if_rate_limited(exc) -> None` — one line at the top of every broad
  `except` on the every-minute paths; raises `GitHubRateLimitError from exc`.
- `log_rate_limit_stop(exc) -> None` — the single "rate limited, reset at …" /
  "reset time unknown" line (OUTPUT level).

Lives in `workflow_utils` because `cli`, `workflows` and `workflow_utils`
itself (label transitions) may all depend on it (tach).

### 2. Stop-on-first-error with one catch per entry point
- Inner broad `except` blocks only call `raise_if_rate_limited(e)` first; their
  other behaviour is unchanged.
- Each entry point has one place that catches the rate limit, logs it once and
  returns 0: `coordinator` run, `vscodeclaude status`, `vscodeclaude launch`.
- `vscodeclaude launch` uses one local `rate_limited` variable:
  phase-1 limit → offline assessments (`build_assessments(sessions, None)`);
  cleanup always runs; restart skipped if already limited; `apply_assessments`
  always runs; then return 0 if limited, else PR health + launch in one `try`.
- `vscodeclaude status` (incl. `--explain`): one `try` around the whole
  GitHub part; on a limit print only the rate-limit line, exit 0.
- Coordinator partial dispatch: `dispatch_workflow` returns `bool`; `False`
  (Jenkins job started, label swap hit a rate limit) → one ERROR + exit 1.
- `workspace.py` `_fetch_marked_comment` keeps swallowing (WARNING).

### 3. "Unknown" issue state in `status.py`
`get_issue_current_status` returns `tuple[str | None, bool | None]`; a failed
live fetch (exception or empty `IssueData`) gives `is_open=None` ("unknown"),
never "closed". `is_session_stale` / `is_issue_closed` treat unknown as
"not stale / not closed" with a WARNING. Rate limits re-raise.

### 4. Final label helper (new function)
`apply_final_label(project_dir, from_label_id, to_label_id, issue_number=None) -> int`
in `workflow_utils/label_transitions.py`: attempt, sleep 30 s, attempt again,
then one ERROR naming the issue and intended label and **return 1** (never
raise / `sys.exit`, so `run_guarded`'s safety net stays silent). All six
workflows return its code from `body()`. `update_workflow_label` re-raises
rate limits instead of returning `False`.

### 5. Run-scoped disk caches, owned by each function
Each function that needs them does `load(...)` per repo, works, `save()` once.
No cache objects are threaded through call chains; `save()` merges on disk so a
later phase reuses earlier entries.
- `check_pr_health`: `PullRequestCache` replaces all live PR queries.
- Branch lookups (`check_pr_health`, status branch check, launch, restart):
  `BranchLookupCache` via one helper `lookup_branch(cache, issue) -> str | None`
  in `workflows/vscodeclaude/issues.py` that turns non-rate-limit lookup errors
  into "no branch".
- Stay live: coordinator dispatch branch lookup, `--intervene`.

### 6. Manager construction
Never pass both `project_dir` and `repo_url`. `_build_pr_manager` and the
`__new__` workaround in `label_transitions` are removed.

### 7. Shim
`mcp_workspace_github.py` gains the new re-exports and loses the four
underscore cache aliases (`get_cache_file_path`, `load_cache_file`,
`save_cache_file`, `log_stale_cache_entries`).

## Files

### Created
- `src/mcp_coder/workflow_utils/rate_limit.py`
- `tests/workflow_utils/test_rate_limit.py`
- `tests/workflow_utils/test_final_label.py`
- `tests/test_mcp_workspace_github_exports.py`
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_13.md`

### Deleted
- `tests/test_mcp_workspace_github_cache.py`

### Modified (source)
- `src/mcp_coder/mcp_workspace_github.py`
- `src/mcp_coder/utils/user_config.py`
- `src/mcp_coder/cli/main.py`
- `src/mcp_coder/cli/commands/gh_tool.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `src/mcp_coder/cli/commands/coordinator/core.py`
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- `src/mcp_coder/services/branch_info.py`
- `src/mcp_coder/workflow_utils/label_transitions.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`, `create_plan/core.py`
- `src/mcp_coder/workflows/implement/core.py`
- `src/mcp_coder/workflows/create_pr/core.py`
- `src/mcp_coder/workflows/fix_ci/core.py`
- `src/mcp_coder/workflows/fix_conflict/core.py`
- `src/mcp_coder/workflows/review/handoff.py`, `review/core.py`
- `src/mcp_coder/workflows/vscodeclaude/checks.py`
- `src/mcp_coder/workflows/vscodeclaude/issues.py`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
- `src/mcp_coder/workflows/vscodeclaude/assessment.py`
- `src/mcp_coder/workflows/vscodeclaude/status.py`

### Modified (docs)
- `docs/configuration/config.md`
- `docs/coordinator-vscodeclaude.md`

### Modified (tests, existing files)
- `tests/services/test_branch_info.py`
- `tests/cli/test_main.py`
- `tests/cli/commands/test_gh_tool_checkout.py`
- `tests/utils/test_user_config_schema.py`, `tests/utils/test_user_config_create_default.py`
- `tests/workflow_utils/test_label_transitions.py`
- `tests/workflows/create_plan/test_success_label_gate.py`, `create_pr/test_workflow_labels.py`,
  `create_pr/test_resume.py`, `fix_ci/test_core.py`, `fix_conflict/test_core.py`,
  `implement/test_core_workflow.py`, `review/test_core*.py`, `review/test_handoff_route.py`,
  `review/test_gates.py` (patch target moves from `update_workflow_label` to `apply_final_label`)
- `tests/cli/commands/coordinator/test_commands.py`, `test_core_dispatch.py`, `test_core_eligibility.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`, `test_vscodeclaude_pr_health.py`
- `tests/workflows/vscodeclaude/test_checks*.py`, `test_issues_branch_check.py`,
  `test_session_launch_process_issues.py`, `test_session_restart_*.py`,
  `test_assessment_*.py`, `test_cache_aware.py`, `test_status_note.py`, `test_explain.py`

## Step order

| Step | Content | Issue scope |
|---|---|---|
| 1 | Shim: `get_issue_cache_last_checked`, drop underscore aliases | 2 (last bullet) |
| 2 | Config keys `traffic_log` / `traffic_log_dir` + docs | 1 |
| 3 | Register traffic-log command name in `main()` | 1 |
| 4 | Manager construction fixes | 5 |
| 5 | Rate-limit helper module + shim exports | 3 |
| 6 | Final label helper + six workflows | 3, 4 |
| 7 | Coordinator rate-limit handling + partial dispatch | 3 |
| 8 | vscodeclaude entry points (launch / status) | 3 |
| 9 | vscodeclaude inner re-raises | 3 |
| 10 | `status.py` "unknown" issue state | 3 |
| 11 | `PullRequestCache` in `check_pr_health` | 2 |
| 12 | `BranchLookupCache` at four call sites | 2 |
| 13 | Docs: `coordinator-vscodeclaude.md` | 6 |

After the PR: open an mcp-workspace follow-up issue to remove its underscore
cache aliases (confirm with the user before creating it — it writes to GitHub).
