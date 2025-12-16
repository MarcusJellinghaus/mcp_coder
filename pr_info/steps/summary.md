# Issue #204: Use Remote Refs When Local Base Branch Doesn't Exist

## Problem Statement

In CI environments (e.g., Jenkins), only the feature branch is checked out locally. The base branch (`main`) doesn't exist as a local branch, causing `get_branch_diff()` to fail:

```
mcp_coder.utils.git_operations.core - ERROR - Base branch 'main' does not exist
mcp_coder.workflows.create_pr.core - WARNING - No diff content found, using fallback PR summary
```

However, the remote ref `origin/main` **is available** and can be used for comparison.

## Solution Overview

Modify `get_branch_diff()` to fall back to `origin/{base_branch}` when the local branch doesn't exist, by adding a `remote_branch_exists()` helper function.

## Architectural / Design Changes

### New Function
- **`remote_branch_exists(project_dir, branch_name)`** in `branches.py`
  - Pure query function (no side effects, no fetch)
  - Checks if `origin/{branch_name}` exists in remote refs
  - Follows existing `branch_exists()` parameter order and patterns

### Modified Function
- **`get_branch_diff()`** in `diffs.py`
  - Added fallback logic: local branch → remote ref → error
  - Uses `origin/{base_branch}` in diff command when local doesn't exist
  - DEBUG log for fallback, ERROR only when neither exists

### Design Decisions

1. **No `checkout_branch()` refactoring**: The issue suggested DRY refactoring, but `checkout_branch()` fetches before checking (side effect), while `remote_branch_exists()` should be a pure query. Keeping them separate maintains clean function design.

2. **Hardcoded `origin` remote**: Consistent with rest of codebase (see `checkout_branch()`, `get_default_branch_name()`).

3. **No fetch in `remote_branch_exists()`**: The function is a pure existence check. Callers who need fresh data should fetch first.

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY | Add `remote_branch_exists()` function |
| `src/mcp_coder/utils/git_operations/diffs.py` | MODIFY | Update `get_branch_diff()` with remote fallback |
| `src/mcp_coder/utils/git_operations/__init__.py` | MODIFY | Export `remote_branch_exists` |
| `tests/utils/git_operations/test_branches.py` | MODIFY | Add tests for `remote_branch_exists()` |
| `tests/utils/git_operations/test_diffs.py` | MODIFY | Add test for remote fallback in `get_branch_diff()` |
| `tests/utils/git_operations/conftest.py` | MODIFY | Add fixture for repo with remote |

## Implementation Steps

1. **Step 1**: Add `remote_branch_exists()` function with tests
2. **Step 2**: Update `get_branch_diff()` with remote fallback and tests

## Acceptance Criteria

- [x] `remote_branch_exists()` function added and tested
- [ ] `checkout_branch()` refactored to use `remote_branch_exists()` - **SKIPPED** (see Design Decisions)
- [x] `get_branch_diff()` falls back to remote ref when local doesn't exist
- [x] Existing behavior unchanged when local branch exists

## Data Flow

```
get_branch_diff(project_dir, base_branch="main")
    │
    ├── branch_exists(project_dir, "main") → True
    │   └── Use "main...HEAD" (existing behavior)
    │
    └── branch_exists(project_dir, "main") → False
        │
        ├── remote_branch_exists(project_dir, "main") → True
        │   └── Use "origin/main...HEAD" (new fallback)
        │
        └── remote_branch_exists(project_dir, "main") → False
            └── ERROR log, return "" (existing error behavior)
```
