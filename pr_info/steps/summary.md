# Summary — #1238 PR-health: run status-10 checks independently of the session limit

## Problem

PR-health detection for `status-10:pr-created` issues (merge conflict → failing CI →
review comments, from #1188 / #1212) runs inside `process_eligible_issues()`
(`workflows/vscodeclaude/session_launch.py`), after its capacity early return
(`if current_count >= max_sessions: return []`). When all session slots are used,
no PR-health checks run. Each `status-10` issue also costs 3× `get_branch_with_pr_fallback`
and 2× `find_pull_request_by_head` per poll, because every check does its own lookup.

## Architectural / design changes

| Before | After |
|---|---|
| Checks are called from `process_eligible_issues()`, gated on capacity | New `check_pr_health()` in `checks.py`, called from the Step 4 per-repo loop in `execute_coordinator_vscodeclaude`, just before `process_eligible_issues()`, **not** gated on capacity |
| Each check resolves branch and PR itself (`branch_manager`, `repo_owner`, GitHub repo name) | One `_resolve_pr_target()` per issue; checks receive the resolved `branch` / `pr` |
| A `PullRequestManager` per check call | One `PullRequestManager` per repo (`_build_pr_manager`, still the patch point) |
| `process_eligible_issues()` builds `CIResultsManager` + label lookups | `process_eligible_issues()` only launches sessions; `check_pr_health()` builds its own managers and label lookups, and only when ≥1 `status-10` issue is selected |
| Escalations are logged at INFO by `update_workflow_label` only | One OUTPUT line per escalated issue: `PR-health: <repo> #N → <label name>`, logged only when the label update succeeds |

### Responsibilities after the change

- `checks.check_pr_health(repo_name, repo_config, all_cached_issues) -> None`
  - selects issues via `_filter_eligible_vscodeclaude_issues` + status `status-10:pr-created`
  - builds managers, the per-repo PR manager and the label lookups (real `labels.json`)
  - never raises: a setup failure (username, label config, managers, repo URL parse) → warning, repo skipped
- `checks._resolve_pr_target(...) -> (branch | None, pr | None)` — the only branch/PR lookup
  - branch lookup raises → warning, `(None, None)`; no branch → `(None, None)` → issue skipped
  - PR lookup raises → warning, `pr = None`; no PR → `pr = None` silently
  - `pr is None` → conflict and review checks skipped; CI still runs (it needs only the branch)
- `checks._escalate(...)` — shared helper: `update_workflow_label` + OUTPUT line on success
- `_check_merge_conflict` / `_check_ci` / `_check_review_comments` — take `pr` / `branch`
  and `repo_name` (config name, OUTPUT line only); same fixed order, at most one action
  per issue per poll; each still never raises

### KISS decisions

- `_check_review_comments` needs no separate target-label parameter: its target is
  `review_label_name`, which it already receives.
- `check_pr_health` reads the real labels config; tests keep patching only
  `label_transitions.load_labels_config`, so the existing `MOCK_*_LABELS_CONFIG` need no new entries
  (real names match: `status-71:merge-conflict`, `status-81:failing-ci`, `status-91:pr-review-comments`).
- `test_vscodeclaude_cli.py` gets one `autouse` fixture that patches `check_pr_health`.

### Unchanged

- `--intervene` returns before Step 4 → no PR-health checks.
- An issue escalated this run gets its session on the next run (the cached issue data still says `status-10`).
- Detection stays in the VSCodeClaude coordinator (#1188 decision).

## Files

### Modified
- `src/mcp_coder/workflows/vscodeclaude/checks.py` — `check_pr_health`, `_resolve_pr_target`, `_escalate`, new check signatures
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` — export `check_pr_health`
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — remove check loop, `ci_manager`, label lookups, unused imports
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` — call `check_pr_health` in Step 4
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` — PR-health tests moved out; `CIResultsManager` patches removed
- `tests/workflows/vscodeclaude/test_session_launch.py` — `CIResultsManager` patch removed
- `tests/workflows/vscodeclaude/test_session_restart_branch_integration.py` — `CIResultsManager` patch removed
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` — autouse fixture patching `check_pr_health`
- `.large-files-allowlist` — remove `test_session_launch_process_issues.py`
- `docs/coordinator-vscodeclaude.md` — remove the session-limit caveat (PR-health section)
- `docs/processes-prompts/development-process.md` — remove the session-limit caveat (section 10)

### Created
- `tests/workflows/vscodeclaude/test_checks.py` — orchestration, `_resolve_pr_target`, conflict, CI, OUTPUT logging
- `tests/workflows/vscodeclaude/test_checks_review_comments.py` — watermark, review comments
- `tests/workflows/vscodeclaude/test_checks_orchestration.py` — only if `test_checks.py` exceeds 750 lines
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` — capacity regression test

### Deleted
- `tests/workflows/vscodeclaude/test_session_launch_review_comments.py`

## Steps

1. Relocate the existing PR-health tests into `test_checks.py` / `test_checks_review_comments.py` (pure move, no source change).
2. Implement `check_pr_health` with the shared lookup, move the call site out of the capacity gate, and rewrite / add the tests (TDD).
3. Remove the session-limit caveat from the docs.

## Out of scope

- Updating epic #1188's "Detection splice point" decision and "runs only below the session limit" constraint — done after merge, not in this PR.
