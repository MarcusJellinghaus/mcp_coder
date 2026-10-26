# Summary — Route all git subprocess calls through `mcp_workspace_git` (#1299)

## Goal

No Python code in `src/` runs git as a subprocess. All git goes through
`mcp_coder.mcp_workspace_git`. Only that shim imports `mcp_workspace.git_operations`,
and only `mcp_coder.mcp_workspace_github` imports `mcp_workspace.github_operations`.
A new CI check (`tools/check_forbidden_calls.py`) enforces this with **no allowlist**.

Upstream API: mcp-workspace `main` ≥ 59cc455 (PR #356). No version pin.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Git access | 10 modules build `["git", ...]` argv and call `execute_command` / `execute_subprocess` | Every git operation is a shim function call; `subprocess_runner` is no longer used for git |
| Shim (`mcp_workspace_git.py`) | 30 exports | Extended per step with the functions each migration needs, plus `BaseBranchSource` and `RebaseResult` (needed for annotations); other result TypedDicts are not re-exported because call sites only read keys |
| Fail-closed semantics | Several sites read a git failure as "clean"/"success" (`status.py` dirty gate, `workflows/rebase.py` clean check, `ls-tree` empty stdout, `ls-remote` parse) | Sites that gate a decision use result types whose failure is `success=False` (`get_working_tree_status`, `probe_origin_branch`, `list_remote_branches`, `list_tree`, `get_conflict_blob_info`) |
| Base-branch detection | Local duplicate of the upstream algorithm + local `BaseBranchSource` enum | Thin wrapper over upstream `detect_base_branch_with_source`; it only builds and injects `PullRequestManager` / `IssueManager`. `BaseBranchSource` comes from upstream (`MERGE_BASE.value` becomes `"merge_base"`) |
| Rebase workflow | Private `_run_git` helper running ~15 different git commands, `.git/rebase-*` and `.git/MERGE_HEAD` filesystem probes | Upstream rebase primitives (`rebase_start/continue/skip/abort`, `reset_hard`, `is_rebase_in_progress`, `get_conflict_blob_info`, `read_conflict_stage`, `resolve_take_theirs_or_remove`, `has_staged_changes`, `list_tree`, `get_remote_url`); no filesystem probes; outcome read from `RebaseResult["status"]` |
| Review handoff | Two-route commit (`commit_staged_files` or raw `git commit -- <path>`) chosen by a fail-open `get_full_status` check; raw `git reset` | Always `commit_paths` (scoped commit); `unstage_paths` on failure |
| Enforcement | `.importlinter` TODOs ("cannot enforce"); nothing catches `"git"` argv | `tools/check_forbidden_calls.py` (text/regex scan of `src/`), CI matrix entry `forbidden-calls`, local wrappers |

### KISS decisions applied

- Shim smoke test checks that every name in `__all__` exists and is unique (instead of a count),
  so later export batches never touch it.
- `workflows/rebase.py`: one `get_conflict_blob_info` call yields both the conflicted paths
  and the binary flag (replaces `_conflicted_files` + `_binary_conflict`). Existing helper names
  (`_abort_rebase`, `_reset_hard`, `_show_stage`, `_stage_all_and_continue`) are kept with
  new bodies to limit churn. The loop reads `result["status"]` instead of re-probing
  `is_rebase_in_progress`.
- `base_branch.py`: one `_build_managers` helper; the local `detect_base_branch` stays
  `result[0] if result else None` over the local `detect_base_branch_with_source`.
- `handoff.py`: drops `_unrelated_staged_entries`, `_commit_only_path`, `_relative_to_project`
  (upstream `commit_paths` / `unstage_paths` validate paths themselves).
- Enforcement tool: a pure `find_violations(rel_path, text)` function plus a thin `main()`;
  unit tests call the pure function with fixture strings.
- `CalledProcessError` wrapping stays inline in the two vscodeclaude modules (no new helper module).

## Accepted behaviour changes (from the issue)

- Detached HEAD in `session_launch` → `"main"` (was `"HEAD"`).
- `BaseBranchSource.MERGE_BASE.value` → `"merge_base"` (visible in the rebase error message).
- Upstream `detect_base_branch` does a network `ls-remote`, drops a merge-base winner deleted on origin.
- Binary conflict detection sniffs NUL bytes instead of honouring `.gitattributes`.
- `MERGE_HEAD` check dropped; the fail-closed clean gate covers merges with conflicts or staged changes.
- `status.py`: a non-repo folder inside a repo is now "No Git".
- `workspace.py` corruption detection uses `is_git_repository` (no git spawn).
- `pr_info/` guard: a failed `list_tree` (e.g. missing `origin/<base>`) is now a preflight error.

## Steps (one commit each; the issue's 6 groups split into independent commits)

| Step | Issue group | Content |
|---|---|---|
| 1 | 1 | Smoke-test fix + `session_launch` branch name |
| 2 | 1 | `workflow_steps/rebase._base_sha` |
| 3 | 1 | `failure_handling.get_diff_stat` |
| 4 | 2 | `check_base_branch_on_origin` |
| 5 | 2 | `gh_tool` remote branch candidates |
| 6 | 2 | `review/handoff` scoped commit / unstage |
| 7 | 2 | `vscodeclaude/session_restart` |
| 8 | 3 | `vscodeclaude/workspace` (clone / re-clone / pull) |
| 9 | 3 | `vscodeclaude/status` (dirty gate) |
| 10 | 4 | `base_branch.py` consolidation |
| 11 | 5 | `workflow_steps/rebase` merge-tree probe |
| 12 | 5 | `workflows/rebase.py` guards and helpers (preflight, `pr_info/` guard, success shape, reset/abort, except/finally) |
| 13 | 5 | `workflows/rebase.py` rebase/conflict loop; `_run_git` removed |
| 14 | 6 | Enforcement tool + CI + wrappers + `.importlinter` comments (last, so CI is never red mid-PR) |

## Files created or modified

### Modified — source
- `src/mcp_coder/mcp_workspace_git.py` (steps 1–13: new exports)
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (1)
- `src/mcp_coder/workflow_steps/rebase.py` (2, 11)
- `src/mcp_coder/workflow_utils/failure_handling.py` (3)
- `src/mcp_coder/workflow_utils/base_branch.py` (4, 10)
- `src/mcp_coder/cli/commands/gh_tool.py` (5)
- `src/mcp_coder/workflows/review/handoff.py` (6)
- `src/mcp_coder/workflows/vscodeclaude/session_restart.py` (7)
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (8)
- `src/mcp_coder/workflows/vscodeclaude/status.py` (9)
- `src/mcp_coder/workflows/rebase.py` (10: import of `BaseBranchSource`; 12, 13)

### Modified — tests
- `tests/test_mcp_workspace_git_smoke.py` (1)
- `tests/workflows/vscodeclaude/test_session_launch_regenerate.py`, `tests/workflows/vscodeclaude/test_session_restart_closed_sessions.py` (1)
- `tests/workflow_steps/test_rebase.py` (2, 11)
- `tests/workflow_utils/test_failure_handling.py` (3)
- `tests/workflow_utils/test_base_branch.py` (4, 10)
- `tests/cli/commands/test_gh_tool_checkout.py` (5)
- `tests/workflows/review/test_handoff.py`, `tests/workflows/review/test_handoff_route.py`, `tests/workflows/review/conftest.py`, `tests/workflows/review/test_core.py`, `tests/workflows/review/test_core_after_steps.py` (6)
- `tests/workflows/vscodeclaude/test_session_restart_prepare_branch.py`, `test_session_restart_branch_integration.py` (7)
- `tests/workflows/vscodeclaude/test_workspace_git.py`, `test_workspace.py` (8)
- `tests/workflows/vscodeclaude/test_folder_git_status.py`, `test_status_display.py` (9)
- `tests/workflows/rebase/test_guards.py` (10, 12)
- `tests/workflows/rebase/test_workflow.py`, `tests/workflows/rebase/test_git_helpers.py` (12, 13)
- `tests/workflows/rebase/test_llm_steps.py` (13)

### Created
- `tools/check_forbidden_calls.py` (14)
- `tools/forbidden_calls_check.sh`, `tools/forbidden_calls_check.bat` (14)
- `tests/tools/test_check_forbidden_calls.py` (14)

### Modified — config
- `.github/workflows/ci.yml` (14: `forbidden-calls` matrix entry)
- `.importlinter` (14: comments only)

## Common rules for every step

- Test first, then implementation. Tests patch shim names **in the consuming module's
  namespace** (e.g. `patch("mcp_coder.workflows.vscodeclaude.status.get_working_tree_status")`),
  and assert "this shim function was called", not argv.
- A stale `patch("<module>.execute_command")` raises `AttributeError` once the module drops the
  import — fix every one in the step that removes the import.
- Add only the shim exports the step needs (append to imports and `__all__`).
- Precondition for every step: the needed function imports from the installed `mcp_workspace`.
  If an import fails, write one line to `pr_info/.blocked.txt` and stop.
- Checks before commit: `run_pylint_check`, `run_pytest_check` (fast unit set, `-n auto`),
  `run_mypy_check`, then `run_format_code`. One commit per step.
