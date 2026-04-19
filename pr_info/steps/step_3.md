# Step 3: Update test consumers + delete old git_operations tests

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Switch test files that import from `mcp_coder.utils.git_operations` to use the shim. Delete the old `tests/utils/git_operations/` test suite (already moved to mcp_workspace). Update `tests/test_module_integration.py` to test the new import paths.

## WHERE

### Test files to update imports

| File | Old import | New import |
|------|-----------|------------|
| `tests/utils/test_git_encoding_stress.py` | `from mcp_coder.utils.git_operations import get_branch_diff, is_git_repository` | `from mcp_coder.mcp_workspace_git import get_branch_diff` (remove `is_git_repository` — dead symbol, check if still used in test) |
| `tests/cli/commands/test_check_branch_status_pr_waiting.py` | `mcp_coder.utils.git_operations.branch_queries` (imports AND `@patch` decorators) | `from mcp_coder.mcp_workspace_git import ...` + update `@patch` target paths |
| `tests/workflows/test_create_pr_integration.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` |
| `tests/utils/github_operations/test_github_integration_smoke.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` (uses `create_branch`, `delete_branch`, `branch_exists`, `checkout_branch`) |
| `tests/utils/github_operations/test_github_utils.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` (uses `create_branch`, `push_branch`, `get_current_branch_name`, `branch_exists`, `checkout_branch`, `fetch_remote`) |
| `tests/cli/test_utils.py` | `@patch("mcp_coder.utils.git_operations.branch_queries.get_current_branch_name")` | `@patch("mcp_coder.mcp_workspace_git.get_current_branch_name")` (multiple `@patch` uses) |
| `tests/utils/github_operations/test_base_manager.py` | `@patch("mcp_coder.utils.github_operations.base_manager.git_operations.is_git_repository")` + `.get_github_repository_url` | `@patch("mcp_coder.utils.github_operations.base_manager.is_git_repository")` + `.get_github_repository_url` (after step 2 changes base_manager.py from module-level `git_operations` import to direct symbol import, the patch path changes) |
| `tests/utils/github_operations/test_ci_results_manager_foundation.py` | `@patch("mcp_coder.utils.git_operations.is_git_repository")` | `@patch("mcp_coder.mcp_workspace_git.is_git_repository")` (patch through shim) |
| `tests/utils/github_operations/test_issue_branch_manager.py` | `@patch("mcp_coder.utils.git_operations.is_git_repository")` (multiple uses) | `@patch("mcp_coder.mcp_workspace_git.is_git_repository")` (multiple `@patch` uses) |
| `tests/utils/github_operations/issues/conftest.py` | `@patch("mcp_coder.utils.git_operations.is_git_repository")` | `@patch("mcp_coder.mcp_workspace_git.is_git_repository")` (fixture-level patch) |
| `tests/utils/github_operations/test_issue_manager_label_update.py` | `@patch("mcp_coder.utils.github_operations.base_manager.git_operations.is_git_repository")` | `@patch("mcp_coder.utils.github_operations.base_manager.is_git_repository")` (same base_manager pattern as test_base_manager.py) |

**Important note about `@patch` decorators**: `test_check_branch_status_pr_waiting.py` uses `@patch("mcp_coder.utils.git_operations.branch_queries.X")` as string-based mock targets. These must be updated. Since the source module is now `mcp_workspace.git_operations.branch_queries`, the patch target should reference wherever the symbol is looked up at runtime. Since the test imports from the shim, the patch path should be `"mcp_coder.mcp_workspace_git.X"` (patching where it's looked up, not where it's defined).

### Test file to rewrite

| File | Change |
|------|--------|
| `tests/test_module_integration.py` | Rewrite to test shim import paths instead of old `utils.git_operations` paths. Remove tests for dead symbols. Update `test_no_circular_imports` to test through shim. |

### Directory to delete

| Path | Reason |
|------|--------|
| `tests/utils/git_operations/` (entire directory) | Full test suite already moved to mcp_workspace in issue ② |

Contains 14 files:
- `__init__.py`, `conftest.py`
- `test_branches.py`, `test_branch_queries.py`, `test_commits.py`
- `test_compact_diffs.py`, `test_compact_diffs_header_only.py`, `test_compact_diffs_integration.py`
- `test_diffs.py`, `test_file_tracking.py`, `test_parent_branch_detection.py`
- `test_remotes.py`, `test_repository_status.py`, `test_staging.py`

## WHAT — Updated `tests/test_module_integration.py`

Rewrite to test:
1. Shim module importability (`from mcp_coder.mcp_workspace_git import ...`)
2. `utils` re-exports still work for surviving symbols
3. Root `mcp_coder` re-exports still work
4. Function attributes preserved
5. `CommitResult` TypedDict usable
6. `__all__` exports correct (updated lists — no dead symbols)
7. No circular imports (test through shim path, not old path)

Remove from tests:
- References to `mcp_coder.utils.git_operations` (package deleted)
- Dead symbols: `git_move`, `is_file_tracked`, `get_staged_changes`, `get_unstaged_changes`, `stage_specific_files`
- Note: `is_git_repository`, `create_branch`, `push_branch` are now in the shim (they have consumers)

## ALGORITHM

```
1. Delete tests/utils/git_operations/ directory entirely
2. Update tests/utils/test_git_encoding_stress.py imports
3. Rewrite tests/test_module_integration.py for new paths
4. Run pytest (unit tests only — exclude integration markers)
5. Run pylint, mypy on modified test files
6. Commit: "refactor: update test imports to shim, delete old git_operations tests"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Delete the entire tests/utils/git_operations/ directory. Update test imports in
tests/utils/test_git_encoding_stress.py to use the shim. Rewrite
tests/test_module_integration.py to test the new shim-based import paths
(remove dead symbols, test surviving re-exports through utils and root __init__).
Run pylint, mypy, and pytest checks.
Commit with message: "refactor: update test imports to shim, delete old git_operations tests"
```
