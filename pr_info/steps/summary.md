# Fix Architecture Violations and CI Failures

## Overview

This implementation fixes architecture violations identified by import-linter and tach, plus related CI failures.

## Problem Statement

CI is failing with 4 job failures:
1. **import-linter**: `utils.branch_status` imports from `workflow_utils.task_tracker` (layer violation)
2. **tach**: Same layer violation (infrastructure cannot import from application)
3. **import-linter**: `git_operations.branches` imports from `git_operations.remotes` (same-layer violation)
4. **vulture**: Unused `__getattr__` function in `workflow_utils/__init__.py`
5. **integration-tests**: `test_git_push_force_with_lease_fails_on_unexpected_remote` expected failure but got success

## Solution Approach

### Step 1: Move `branch_status.py` to Application Layer
Move from `utils/` to `workflow_utils/` where it belongs conceptually (workflow-specific status reporting).

### Step 2: Fix Git Operations Internal Layering
Move `needs_rebase` from `branches.py` to `workflows.py` since it orchestrates remote + branch operations.

### Step 3: Fix Vulture Warning
Add vulture whitelist entry for the lazy import `__getattr__` pattern.

### Step 4: Fix Failing Integration Test
Investigate and fix the `test_git_push_force_with_lease_fails_on_unexpected_remote` test.

## Files Affected

### Moved Files
- `src/mcp_coder/utils/branch_status.py` → `src/mcp_coder/workflow_utils/branch_status.py`
- `tests/utils/test_branch_status.py` → `tests/workflow_utils/test_branch_status.py`

### Modified Files
- `src/mcp_coder/utils/__init__.py` (remove branch_status exports)
- `src/mcp_coder/workflow_utils/__init__.py` (add branch_status exports)
- `src/mcp_coder/cli/commands/check_branch_status.py` (update import)
- `src/mcp_coder/workflows/implement/core.py` (update import)
- `tests/cli/commands/test_check_branch_status.py` (update import)
- `tests/workflows/implement/test_ci_check.py` (update import)
- `src/mcp_coder/utils/git_operations/branches.py` (remove needs_rebase)
- `src/mcp_coder/utils/git_operations/workflows.py` (add needs_rebase)
- `src/mcp_coder/utils/git_operations/__init__.py` (update exports)
- `vulture_whitelist.py` (add __getattr__ entry)
- `tests/utils/git_operations/test_remotes.py` (fix test)

## Success Criteria

- All import-linter contracts pass
- All tach checks pass
- Vulture finds no unused code
- All tests pass including integration tests
- No functional changes to behavior
