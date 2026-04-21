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
