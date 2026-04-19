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

**Status**: pending commit
