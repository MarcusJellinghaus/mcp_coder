# Summary — #1465: run PR-health detection on Jenkins instead of vscodeclaude

## Goal

PR-health detection (`status-10:pr-created` → `status-71` / `81` / `91`) runs today only in
`mcp-coder vscodeclaude launch`. Move it into the Jenkins `coordinator` run (`_collect_work`),
per repo with executor capacity, before dispatch. vscodeclaude keeps the interactive sessions only.

Issue: #1465 (read it for the full rationale; this plan implements its "Implementation approach",
"Tests" and "Docs" sections with the KISS simplifications listed below).
Refactoring rules for the move-only steps: `.claude/knowledge_base/refactoring_principles.md`.

## Architectural / design changes

| Before | After |
|---|---|
| `workflows/vscodeclaude/checks.py` (`check_pr_health`) | `workflows/pr_health/checks.py`, exported from `workflows/pr_health/__init__.py` |
| `get_issue_status`, `is_marked` in `vscodeclaude/helpers.py`; `lookup_branch` in `vscodeclaude/issues.py` | all three in new `workflow_utils/issue_helpers.py`; vscodeclaude imports them from there (no re-exports) |
| `vscodeclaude/__init__.py` re-exports `check_pr_health` | re-export removed (avoids a `pr_health` ↔ `vscodeclaude` import cycle) |
| PR-health selection: assignee = token user, exactly one human_action label, `get_issue_status == status-10` | open + `status-10:pr-created` in labels + no `ignore_labels`; other `status-*` labels don't matter; no assignee filter |
| Repo URL rebuilt as `https://github.com/{full_name}` (drops GHE host) | `RepoIdentifier.from_repo_url(repo_url).https_url` (keeps host, validates inside the setup `try`) |
| Escalation writes GitHub only | after a successful escalation, `update_issue_labels_in_cache(10 → target)` as dispatch does |
| `vscodeclaude launch` → `_launch_for_repos` calls `check_pr_health` | call removed; `coordinator` → `_collect_work` calls it |
| `_collect_work` uses `get_cached_eligible_issues` (core.py) | `get_all_cached_issues` once per repo, `_filter_eligible_issues` on the same list; `get_cached_eligible_issues` deleted |
| — | ERROR log per open issue with >1 `status-*` label (repos with capacity and a working cache) |

### Call order in `_collect_work` (per repo)

1. config + capacity gate (unchanged; busy job → `continue`, no GitHub call)
2. `try`: `get_all_cached_issues(...)` → `_filter_eligible_issues(all_issues)`
3. `except`: re-raise rate limit, warn, `get_eligible_issues(issue_manager)` (direct-fetch fallback)
4. `else` (cache worked only): `_log_multiple_status_labels(repo_name, all_issues)`, then
   `check_pr_health(repo_name, validated_config, all_issues)`
5. existing `if not eligible_issues: continue` and `_Repo` build

The `else` branch replaces a sentinel variable: it runs only when the `try` succeeded, and an
exception raised inside it is not caught by the `except`, so a PR-health error can never trigger
the fallback. A `GitHubRateLimitError` from PR-health propagates → run ends with exit 0, no dispatch.

### KISS decisions (preserve all issue requirements)

- One destination module (`workflow_utils/issue_helpers.py`) for the three shared helpers.
- One existing broad `except` in `_collect_work` covers the old narrow `(ValueError, KeyError, TypeError)` fallback.
- Selection is a list comprehension in `check_pr_health`, reusing the labels config it already loads.
- One module constant `PR_CREATED_LABEL = "status-10:pr-created"` for selection and cache write-back.
- No `try` around `update_issue_labels_in_cache` (it catches and logs everything itself).
- `ignore_labels` matched exactly, as in the coordinator's `_filter_eligible_issues`.

## Steps (one commit each)

1. Move `get_issue_status`, `is_marked`, `lookup_branch` to `workflow_utils/issue_helpers.py` (move only).
2. Move `vscodeclaude/checks.py` to `workflows/pr_health/` with its tests (move only).
3. `pr_health` behaviour: new selection, `RepoIdentifier` URL, cache write-back.
4. Coordinator runs PR-health in `_collect_work`; vscodeclaude stops; delete `get_cached_eligible_issues`.
5. Multi-status-label ERROR in `_collect_work`.
6. Docs.

## Files

### Created
- `src/mcp_coder/workflow_utils/issue_helpers.py` (step 1)
- `tests/workflow_utils/test_issue_helpers.py` (step 1)
- `src/mcp_coder/workflows/pr_health/__init__.py` (step 2)
- `src/mcp_coder/workflows/pr_health/checks.py` (step 2, moved from `workflows/vscodeclaude/checks.py`)
- `tests/workflows/pr_health/__init__.py` (step 2)
- `tests/workflows/pr_health/test_checks.py`, `test_checks_alerts.py`, `test_checks_pr_cache.py`,
  `test_checks_review_comments.py`, `test_checks_review_comments_trust.py`, `_review_comments_helpers.py`
  (step 2, moved from `tests/workflows/vscodeclaude/`)
- `tests/workflows/pr_health/test_checks_rate_limit.py` (step 2, `TestCheckPrHealthRateLimit`)
- `tests/workflows/pr_health/conftest.py` (step 3, autouse stub of `update_issue_labels_in_cache`)
- `tests/workflows/pr_health/test_checks_selection.py` (step 3)
- `tests/workflows/pr_health/test_checks_warm_cache.py` (step 3, moved warm-cache test)
- `tests/cli/commands/coordinator/test_commands_pr_health.py` (step 4, extended in step 5)

### Modified
- `src/mcp_coder/workflows/vscodeclaude/helpers.py`, `issues.py`, `session_launch.py`,
  `session_restart.py`, `status.py`, `workspace.py` (step 1 imports)
- `src/mcp_coder/workflows/vscodeclaude/__init__.py` (step 2)
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` (steps 2, 4)
- `src/mcp_coder/cli/commands/coordinator/commands.py` (steps 4, 5)
- `src/mcp_coder/cli/commands/coordinator/core.py`, `coordinator/__init__.py` (step 4)
- `tests/workflows/vscodeclaude/test_helpers.py`, `test_issues_branch_check.py` (step 1)
- `tests/workflows/vscodeclaude/test_rate_limit_reraise.py` (step 2)
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` (step 2 path, step 3 warm-cache test removed)
- `tests/cli/commands/coordinator/conftest.py`, `test_commands.py`, `test_integration.py`,
  `test_commands_capacity_gate.py`, `test_commands_dispatch_order.py`, `test_commands_trust_gate.py`,
  `test_core_eligibility.py`, `test_vscodeclaude_rate_limit.py`, `test_vscodeclaude_cli.py` (step 4)
- `vulture_whitelist.py` (steps 2, 4: comment paths)
- `docs/coordinator-vscodeclaude.md`, `docs/processes-prompts/processes/71-pr-follow-up.md`,
  `docs/getting-started/label-setup.md`, `docs/repository-setup/jenkins.md`, `docs/cli-reference.md`,
  `docs/repository-setup/github.md`, `docs/architecture/architecture.md` (step 6)

### Deleted
- `src/mcp_coder/workflows/vscodeclaude/checks.py` (moved, step 2)
- the 5 `tests/workflows/vscodeclaude/test_checks*.py` files and `_review_comments_helpers.py` (moved, step 2)
- `tests/cli/commands/coordinator/test_vscodeclaude_pr_health.py` (step 4)

## Checks after every step

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"])
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_vulture_check
mcp__mcp-workspace__check_file_size
```
