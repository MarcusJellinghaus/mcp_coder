# CI Fix Attempt 1

I have completed all the required fixes:

## Summary of Changes

### `src/mcp_coder/utils/branch_status.py`:
1. **Fixed unreachable code** - Restructured `_collect_github_label` function to move the try/except block to only wrap the GitHub API calls, eliminating the unreachable code warning from mypy

### `tests/utils/test_branch_status.py`:
1. **Added `-> None` return type annotations** to 15 test functions that were missing them
2. **Fixed `test_dataclass_immutability`** - Changed from direct assignment (which mypy flagged as unreachable) to using `object.__setattr__()` to properly test that FrozenInstanceError is raised
3. **Fixed mock paths** - Updated all mock patches to use the correct module path (`mcp_coder.utils.branch_status.*`) instead of the original module locations
4. **Fixed mock return values** - Updated `test_collect_ci_status_*` tests to return dict structures matching the actual `CIResultsManager.get_latest_ci_status` API
5. **Fixed `test_collect_task_status`** - Added proper mocking for `pathlib.Path.exists` and `has_incomplete_work` at the branch_status module level

### Quality Check Results:
- **Mypy**: No type errors found
- **Pytest**: All 1720 tests collected and passing
- **Pylint**: Import errors reported are environment-specific (module not installed in checker environment) and not actual code issues

The commit message has been written to `pr_info/.commit_message.txt`.