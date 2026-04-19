# Step 3: Update test consumers + delete old git_operations tests

> **Read `pr_info/steps/summary.md` first for full context.**

## Goal

Switch remaining test files that import from `mcp_coder.utils.git_operations` to use the shim. Delete the old `tests/utils/git_operations/` test suite (already moved to mcp_workspace). Add a smoke test for the shim.

> **Note:** Test files whose `@patch` targets break due to step 2 source changes were already updated in step 2 (`tests/test_module_integration.py`, `tests/utils/github_operations/test_base_manager.py`, `test_ci_results_manager_foundation.py`, `test_issue_branch_manager.py`, `issues/conftest.py`, `test_issue_manager_label_update.py`, `tests/cli/test_utils.py`). This step handles only the remaining test-only files.

## WHERE

### Test files to update imports

| File | Old import | New import |
|------|-----------|------------|
| `tests/utils/test_git_encoding_stress.py` | `from mcp_coder.utils.git_operations import get_branch_diff, is_git_repository` | `from mcp_coder.mcp_workspace_git import get_branch_diff` (remove `is_git_repository` (unused in this file)) |
| `tests/cli/commands/test_check_branch_status_pr_waiting.py` | `mcp_coder.utils.git_operations.branch_queries` (imports AND `@patch` decorators) | `from mcp_coder.mcp_workspace_git import ...` + update `@patch` targets to `@patch("mcp_workspace.git_operations.branch_queries._safe_repo_context")` and `@patch("mcp_workspace.git_operations.branch_queries.is_git_repository")` |
| `tests/workflows/test_create_pr_integration.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` |
| `tests/utils/github_operations/test_github_integration_smoke.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` (uses `create_branch`, `delete_branch`, `branch_exists`, `checkout_branch`) |
| `tests/utils/github_operations/test_github_utils.py` | `mcp_coder.utils.git_operations` | `from mcp_coder.mcp_workspace_git import ...` (uses `create_branch`, `push_branch`, `get_current_branch_name`, `branch_exists`, `checkout_branch`, `fetch_remote`) |
| `tests/cli/commands/test_git_tool.py` | stale docstring comment on line 4 referencing `tests/utils/git_operations/test_compact_diffs.py` | Update or remove the docstring comment (directory deleted in this step) |

**Important note about `@patch` decorators**: `test_check_branch_status_pr_waiting.py` uses `@patch("mcp_coder.utils.git_operations.branch_queries.X")` as string-based mock targets. These must be updated. The test patches internal dependencies of `has_remote_tracking_branch()`, which lives in `mcp_workspace.git_operations.branch_queries`. After migration, the function's internal calls resolve from that module's namespace, so the correct patch targets are `@patch("mcp_workspace.git_operations.branch_queries._safe_repo_context")` and `@patch("mcp_workspace.git_operations.branch_queries.is_git_repository")`. Note: `@patch` strings are NOT Python imports -- they're runtime lookups, so import-linter won't flag them.

### Smoke test to add

| File | Purpose |
|------|---------|
| `tests/test_mcp_workspace_git_smoke.py` | Smoke test: shim importable, key symbols accessible |

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

## ALGORITHM

```
1. Delete tests/utils/git_operations/ directory entirely
2. Update remaining test file imports (test_git_encoding_stress.py, test_check_branch_status_pr_waiting.py,
   test_create_pr_integration.py, test_github_integration_smoke.py, test_github_utils.py, test_git_tool.py)
3. Add tests/test_mcp_workspace_git_smoke.py
4. Run pytest (unit tests only — exclude integration markers)
5. Run pylint, mypy on modified test files
6. Commit: "refactor: update remaining test imports to shim, delete old git_operations tests"
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Delete the entire tests/utils/git_operations/ directory. Update test imports in
the remaining test files listed in the step (test_git_encoding_stress.py,
test_check_branch_status_pr_waiting.py, test_create_pr_integration.py,
test_github_integration_smoke.py, test_github_utils.py, test_git_tool.py)
to use the shim. Add the smoke test tests/test_mcp_workspace_git_smoke.py.
Note: tests/test_module_integration.py and @patch-dependent test files were
already updated in step 2.
Run pylint, mypy, and pytest checks.
Commit with message: "refactor: update remaining test imports to shim, delete old git_operations tests"
```
