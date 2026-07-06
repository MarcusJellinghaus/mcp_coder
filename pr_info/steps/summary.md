# Summary — Split `cli/commands/coordinator/commands.py` (Issue #1022)

## Goal

`src/mcp_coder/cli/commands/coordinator/commands.py` (825 lines, on
`.large-files-allowlist`) mixes two unrelated command families that share **no
call graph**:

- **Jenkins path** — `format_job_output`, `execute_coordinator_test`,
  `execute_coordinator_run`
- **VSCodeClaude path** — `_get_repo_full_name_from_url`,
  `_build_cached_issues_by_repo`, `execute_coordinator_vscodeclaude`,
  `execute_coordinator_vscodeclaude_status`, `_handle_intervention_mode`

Extract the VSCodeClaude family into a new sibling module
`commands_vscodeclaude.py`. Both resulting files land well under 600 lines.

This is a **pure move-don't-change refactor** per
[`docs/processes-prompts/refactoring-guide.md`](../../docs/processes-prompts/refactoring-guide.md):
no logic edits, no back-compat re-exports, delete the old locations, update every
importer, verify with `git-tool compact-diff` (should show only import churn and
new/deleted file headers).

## Architectural / design changes

- **New module boundary inside the `coordinator` package.** The `coordinator`
  package gains a second command module. `commands.py` becomes Jenkins-only;
  `commands_vscodeclaude.py` owns the VSCodeClaude command family. The package
  `__init__.py` remains the single public facade — its `__all__` is unchanged, so
  **no external caller sees any difference** (`cli/main.py` imports from the
  package, not the module).
- **No new layer / no import-linter change.** The split is a sibling module in an
  existing package with no new cross-module dependency (the two families never
  call each other), so `.importlinter` / `tach` contracts are untouched. This is
  simpler than the sub-layer case the refactoring guide warns about.
- **Test structure mirrors source.** VSCodeClaude command tests consolidate into
  `test_vscodeclaude_cli.py`; `test_commands.py` becomes Jenkins-only, matching
  the new source layout.

## Key mechanical facts driving the plan

- **`move_symbol` auto-updates `from … import …` statements** (including
  in-function imports in tests) but is **blind to string literals** inside
  `@patch("…")` / `monkeypatch.setattr("…", …)`. Those must be repointed manually.
- **Patch targets follow the dependency into the new module.** After the move, the
  VSCodeClaude functions' dependencies (`process_eligible_issues`,
  `prepare_and_launch_session`, `load_sessions`, `load_vscodeclaude_config`,
  `create_default_config`, `get_config_file_path`, `load_repo_vscodeclaude_config`,
  `cleanup_stale_sessions`, `build_assessments`, `apply_assessments`,
  `restart_closed_sessions`, `_build_cached_issues_by_repo`, `IssueManager`,
  `IssueBranchManager`, `load_config`, `load_repo_config`) live in
  `commands_vscodeclaude`, so old patch strings `…coordinator.commands.<dep>` raise
  `AttributeError` and must become `…coordinator.commands_vscodeclaude.<dep>`.

## KISS decisions

1. **Reorganize tests first, move source second.** By relocating the two
   VSCodeClaude test classes into `test_vscodeclaude_cli.py` **before** touching
   the source (Step 1), every remaining `…coordinator.commands.<dep>` string ends
   up in a file that references **only moved symbols**. The Step 2 repointing then
   collapses to a **whole-file blanket find-replace** in exactly three files —
   `mcp_coder.cli.commands.coordinator.commands.` →
   `mcp_coder.cli.commands.coordinator.commands_vscodeclaude.` — with **no
   per-`@patch` judgement** and no risk of touching a Jenkins patch that must stay.
   `test_commands.py` needs **zero** repointing.
2. The trailing `.` in the replace target matches only string-literal patch
   targets; plain `from … commands import (` statements (space, not dot, after
   `commands`) are left for `move_symbol` — clean division of labour, no
   double-substitution (`commands_vscodeclaude` has `_`, not `.`, after `commands`).
3. Each step is an independently green, single commit; you could stop after Step 1
   with a fully working tree (Step 1 changes no production code).

## Correction to the issue text

The issue claims `tests/workflows/vscodeclaude/test_active_set_invariant.py` and
`test_explain.py` are auto-updated importers needing **no manual action**. That is
**inaccurate**: each has a plain import that `move_symbol` fixes, but each also
contains many `monkeypatch.setattr("…coordinator.commands.<dep>", …)` **string**
targets that will break. They are repointed by the Step 2 blanket replace.

## Folders / modules / files created or modified

**Created**
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py` — the 5 moved
  VSCodeClaude functions + their imports + `__all__` (via `move_symbol`).
- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`
  (planning artifacts).

**Modified**
- `src/mcp_coder/cli/commands/coordinator/commands.py` — VSCodeClaude functions
  removed; unused imports pruned by `move_symbol`; `__all__` trimmed to 3 Jenkins
  names. *(Step 2)*
- `src/mcp_coder/cli/commands/coordinator/__init__.py` — re-export split into two
  import blocks (`.commands` + `.commands_vscodeclaude`); `__all__` unchanged.
  *(Step 2)*
- `.large-files-allowlist` — remove the `…/coordinator/commands.py` entry. *(Step 2)*
- `tests/cli/commands/coordinator/test_commands.py` — remove `TestSkipGithubInstallWiring`,
  `TestAtCapacityDiagnosticLog`, and helper `_assessment_stub`; prune now-unused
  imports. Becomes Jenkins-only. *(Step 1)*
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` — receive the two
  classes + helper + required imports *(Step 1)*; blanket patch-string repoint
  *(Step 2)*.
- `tests/workflows/vscodeclaude/test_active_set_invariant.py` — plain import
  auto-updated + blanket patch-string repoint. *(Step 2)*
- `tests/workflows/vscodeclaude/test_explain.py` — plain import auto-updated +
  blanket patch-string repoint. *(Step 2)*

**Untouched (verify only)**
- `tests/cli/commands/coordinator/test_integration.py` — patches Jenkins-path deps
  that stay in `commands.py`; no change needed.
- `src/mcp_coder/cli/main.py` — imports from the package facade; unaffected.

## Verification (run after each step)

`run_format_code` → `run_pylint_check` → `run_pytest_check(extra_args=["-n","auto",
"-m","not git_integration and not claude_cli_integration and not
claude_api_integration and not formatter_integration and not github_integration and
not langchain_integration"])` → `run_mypy_check` → `run_lint_imports_check` →
`run_vulture_check` → `check_file_size(max_lines=750)` → `tach check` (Bash) →
`git-tool compact-diff` (Bash; Step 2 should show only import changes + file
headers).
