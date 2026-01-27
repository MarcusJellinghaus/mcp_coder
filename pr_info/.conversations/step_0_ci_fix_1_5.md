# CI Fix Attempt 1

I've completed all the tasks. Here's a summary of the changes made:

## Summary of Changes

### Problem
The CI pipeline was failing because test mocks weren't properly intercepting git repository detection functions. When tests called `collect_branch_status()` or `_run_auto_fixes()`, the underlying `get_current_branch_name()` function wasn't being properly mocked.

### Root Causes
1. **`_collect_github_label()` called `get_current_branch_name()` directly** - This was redundant since `collect_branch_status()` already fetched the branch name, and it made mocking harder.
2. **CLI tests patched at wrong import path** - Tests were patching `mcp_coder.utils.git_operations.readers.get_current_branch_name` but the function was imported locally inside `_run_auto_fixes()`.

### Fixes Applied

**src/mcp_coder/utils/branch_status.py:**
- Modified `_collect_github_label()` to accept an optional `branch_name` parameter
- Updated `collect_branch_status()` to pass the branch name to `_collect_github_label()`

**src/mcp_coder/cli/commands/check_branch_status.py:**
- Moved `get_current_branch_name` import to module level for proper mock patching
- Removed the local import from inside `_run_auto_fixes()`

**tests/utils/test_branch_status.py:**
- Updated `test_collect_github_label()` to pass branch_name directly
- Added new `test_collect_github_label_without_branch_name()` test for fallback behavior
- Updated `test_collect_github_label_no_status_label()` to pass branch_name directly
- Updated `test_collect_github_label_error_handling()` to test the new behavior

**tests/cli/commands/test_check_branch_status.py:**
- Fixed patch paths from `mcp_coder.utils.git_operations.readers.get_current_branch_name` to `mcp_coder.cli.commands.check_branch_status.get_current_branch_name` in three test methods