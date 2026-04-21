# Plan Review Log — Issue #833

Review of the implementation plan for "Consume github_operations via shim + rebuild update_workflow_label (part 5 of 5)".

## Round 1 — 2026-04-21

**Findings**:
- (critical) ~30 test files outside `tests/utils/github_operations/` import from `mcp_coder.utils.github_operations` — no step covered updating these imports. After Step 6 deletion, all would break.
- (critical) `src/mcp_coder/__init__.py` re-exports `CommentData`, `IssueData`, `IssueManager`, `LabelData` from local `github_operations` — missing from Step 4. Would break `import mcp_coder` after deletion.
- (critical) 5 additional source files missing from Step 4: `gh_tool.py`, `coordinator/commands.py`, `vscodeclaude/helpers.py`, `workflow_utils/base_branch.py`, `checks/ci_log_parser.py`.
- (critical) Step 2 didn't note lazy/inline imports of `label_config` in function bodies (3 files with inline `get_labels_config_path` imports).
- (critical) Step 7 `.importlinter` proposed a shim isolation contract that would hit the known import-linter v2.11 limitation with external subpackage paths. Also proposed unnecessary exceptions for `github` and `requests` (shim re-exports, doesn't import these directly).
- (improvement) Step 3 test count was 11, actual count is 12 (missing `test_update_workflow_label_race_condition_scenario`).
- (improvement) Step 7 tach.toml proposed moving `mcp_workspace_git` to `shim_workspace` — out of scope (git shim still imports from local utils).
- (improvement) Step 7 tach.toml missing `mcp_coder.mcp_workspace_github` in `tests` module `depends_on`.
- (improvement) Summary file counts underreported modified files.
- (note) `mcp_workspace.github_operations` not yet installed — plan already notes prerequisite.

**Decisions**:
- All findings accepted as straightforward improvements — no user escalation needed.
- Test import migration added to Step 4 (alongside source imports, not deferred).
- Import-linter contract marked as conditional with v2.11 limitation note.
- Out-of-scope git shim tach.toml change removed.

**User decisions**: None required.

**Changes**:
- `step_4.md`: Added 6 missing source files, added test file migration section (~30 files), updated file count to 25
- `step_2.md`: Added lazy/inline import note for 3 files
- `step_3.md`: Fixed test count from 11 to 12, added missing test name
- `step_7.md`: Added v2.11 limitation notes, changed to verify-then-add for library isolation, removed out-of-scope git shim change, added tests depends_on
- `summary.md`: Added missing source files to table, added test file update note

**Status**: committed

## Round 2 — 2026-04-21

**Findings**:
- (critical) Step 2 missing 5 test files that import from `label_config`: `test_define_labels.py`, `test_define_labels_config.py`, `test_define_labels_label_changes.py`, `test_set_status.py`, `test_set_status_from_status.py`.
- (improvement) Step 3 test list heading still said "all 11" instead of "all 12" (incomplete round 1 fix).
- (improvement) Step 4 listed `test_gh_tool*.py` but that file doesn't import from `github_operations` — false entry.
- (improvement) Step 4 missing `test_closed_issues_integration.py` and `test_launch_vscode_env_vars.py` from vscodeclaude test list.
- (note) `tests/cli/commands/coordinator/test_core.py` has logger name strings referencing `mcp_coder.utils.github_operations.issues.cache` — may need updating.
- (note) Summary didn't note Step 2's test file updates separately from Step 4's.

**Decisions**:
- All findings accepted as straightforward improvements.
- `issue_stats.py` was already in Step 2's table (confirmed present).

**User decisions**: None required.

**Changes**:
- `step_2.md`: Added 5 test files section for label_config imports
- `step_3.md`: Fixed heading from "all 11" to "all 12"
- `step_4.md`: Removed `test_gh_tool*.py`, added 2 missing vscodeclaude test files, added logger name note
- `summary.md`: Added note about Step 2 test file updates

**Status**: committed

## Round 3 — 2026-04-21 (verification)

**Findings**: None — all round 1 and round 2 fixes verified correct.

**Verification**:
- Grep of `github_operations` across `src/` (50 matches) and `tests/` (81 matches) confirms all files are covered by the plan.
- Source files: All 25 in Step 4 accounted for. Label_config imports correctly split between Steps 2 and 4.
- Test files: ~5 in Step 2 (label_config), ~29 in Step 4 (shim), remainder in `tests/utils/github_operations/` deleted in Step 6.
- Config files: `.importlinter` and `tach.toml` covered by Step 7.
- Step numbering, cross-references, and summary all consistent.

**Changes**: None.

**Status**: no changes needed

## Final Status

**Rounds run**: 3 (2 with changes, 1 verification)
**Commits produced**: 2 (`da8f266`, `bf57e25`)
**Plan status**: Ready for implementation

**Key improvements made**:
1. Added ~30 missing test file import updates to Step 4 (would have broken all tests after Step 6 deletion)
2. Added 5 missing test files for `label_config` imports to Step 2
3. Added 6 missing source files to Step 4 (including root `__init__.py` — would have broken `import mcp_coder`)
4. Fixed Step 7 import-linter proposals to account for v2.11 limitations
5. Removed out-of-scope git shim tach.toml change
6. Fixed test count (11→12), added lazy import notes, updated summary
