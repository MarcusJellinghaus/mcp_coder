# Plan Review Log — Issue #813 (Run 1)

## Round 1 — 2026-04-19

**Findings**:
- 5 missing source consumers in step 2: `failure_handling.py`, `base_manager.py`, `ci_results_manager.py`, `pr_manager.py`, `issues/manager.py`
- 4 missing test consumers in step 3: `test_check_branch_status_pr_waiting.py`, `test_create_pr_integration.py`, `test_github_integration_smoke.py`, `test_github_utils.py`
- 4 symbols (`is_git_repository`, `create_branch`, `delete_branch`, `push_branch`) classified as dead but have live consumers in `github_operations/` and test files
- `@patch` decorators in test files reference old module paths (string-based mock targets)
- Stale `jenkins_independence` contract in `.importlinter` references deleted package
- `PushResult` listed in dead symbols but never in `utils/__init__.py` (no-op removal)
- `needs_rebase` not in step 0's verification checklist
- `validate_branch_name` falsely reported as missing from shim (actually present — finding skipped)

**Decisions**:
- Add 4 "dead" symbols to shim → accepted (user chose "Add to shim" — can be removed in issue ⑤)
- Add 5 missing source consumers to step 2 → accepted (straightforward)
- Add 4 missing test consumers to step 3 → accepted (straightforward)
- Update `@patch` decorators to `mcp_coder.mcp_workspace_git.X` → accepted (straightforward)
- Update `jenkins_independence` contract → accepted (straightforward)
- Remove `PushResult` and `is_git_repository` from dead symbols list → accepted
- Add `needs_rebase` to step 0 verification → accepted
- Finding 6 (`validate_branch_name` missing) → skipped (incorrect — already in shim)
- Findings 12, 14, 15, 17, 20 → skipped (nits/informational)

**User decisions**:
- Q: How to handle `is_git_repository`, `create_branch`, `delete_branch`, `push_branch` (classified as dead but have live consumers)?
- A: Add to shim now. Can be removed in issue ⑤ when github_operations is refactored.

**Changes**:
- step_0.md: Added `needs_rebase` to verification checklist
- step_1.md: Added 4 symbols to shim, updated `__all__` count to 29, updated smoke test
- step_2.md: Added 5 source consumers, updated dead symbols list, fixed `is_git_repository` handling
- step_3.md: Added 4 test consumers, added `@patch` decorator update notes
- step_5.md: Added `jenkins_independence` contract update, added `tach check` note
- summary.md: Updated symbol count, consumer lists, dead symbols section

**Status**: committed (94feed8)

## Round 2 — 2026-04-19

**Findings**:
- 4 more missing source consumers in step 2: `cli/utils.py`, `cli/commands/set_status.py`, `cli/commands/gh_tool.py`, `cli/commands/coordinator/issue_stats.py`
- 6 more missing test consumers with `@patch` string paths: `test_utils.py`, `test_base_manager.py`, `test_ci_results_manager_foundation.py`, `test_issue_branch_manager.py`, `issues/conftest.py`, `test_issue_manager_label_update.py`
- `jenkins_independence` contract update wording needed to be more explicit
- Summary file counts inconsistent after round 1 additions
- Test method name `test_workflow_git_operations_integration` cosmetic rename (skipped per SE principles)

**Decisions**:
- Add 4 source consumers to step 2 → accepted (straightforward)
- Add 6 test consumers to step 3 → accepted (straightforward, `@patch` paths)
- Make `jenkins_independence` update explicit → accepted
- Update summary file counts → accepted
- Test method rename → skipped (cosmetic, out of scope)
- `git_local` contract removal note → skipped (nit)

**User decisions**: None needed this round.

**Changes**:
- step_2.md: Added 4 source consumers
- step_3.md: Added 6 test consumers with `@patch` path update details
- step_5.md: Made `jenkins_independence` update wording explicit
- summary.md: Updated file counts (now 38 files modified)

**Status**: committed (6551c98)

## Round 3 — 2026-04-19

**Findings**:
- 3 test files had wrong `@patch` target (`mcp_coder.mcp_workspace_git.is_git_repository` should be `mcp_coder.utils.github_operations.base_manager.is_git_repository`): test_ci_results_manager_foundation.py, test_issue_branch_manager.py, issues/conftest.py
- `test_check_branch_status_pr_waiting.py` had wrong `@patch` targets (should be `mcp_workspace.git_operations.branch_queries.*` since patching internal dependencies)
- Inconsistency: `is_git_repository`, `create_branch`, `push_branch` marked as "no longer dead" but not in surviving re-exports list
- Stale docstring comment in `test_git_tool.py` referencing deleted test directory
- Step sizing is reasonable (mechanical transforms, no split needed)
- Symbol count (29) verified correct
- Architecture config changes verified complete

**Decisions**:
- Fix @patch paths for 3 github_operations test files → accepted (critical correctness fix)
- Fix @patch paths for test_check_branch_status_pr_waiting.py → accepted (critical correctness fix)
- Clarify re-export scope in step 2 → accepted (consistency improvement)
- Add test_git_tool.py stale comment fix → accepted (nit)

**User decisions**: None needed this round.

**Changes**:
- step_2.md: Added clarifying note about symbols in shim but not in utils/__init__.py re-exports
- step_3.md: Fixed @patch paths for 4 test files, added test_git_tool.py, rewrote Important Note with correct rationale

**Status**: pending commit
