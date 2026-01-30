# CI Fix Attempt 2

I have completed the CI pipeline fix. Here's a summary of the changes made:

## Summary

The CI pipeline was failing because two files exceeded the 750-line limit:
1. `src/mcp_coder/utils/vscodeclaude/orchestrator.py` - 783 lines
2. `tests/utils/vscodeclaude/test_orchestrator.py` - 837 lines

### Solution

I refactored the code by extracting helper functions into a new module:

**New files created:**
1. `src/mcp_coder/utils/vscodeclaude/helpers.py` (~145 lines) - Contains utility functions:
   - `get_repo_short_name`, `get_repo_full_name`, `get_repo_short_name_from_full`
   - `get_issue_status`, `build_session`
   - `get_stage_display_name`, `truncate_title`

2. `tests/utils/vscodeclaude/test_helpers.py` (~155 lines) - Tests for the helper functions

**Modified files:**
1. `src/mcp_coder/utils/vscodeclaude/orchestrator.py` (~590 lines) - Now imports from helpers.py, includes `__all__` for explicit exports, and maintains backward compatibility with underscore-prefixed aliases

2. `tests/utils/vscodeclaude/test_orchestrator.py` (~552 lines) - Reduced to focus on orchestration logic only, with a new `TestBackwardCompatibility` class to verify the re-exported functions work correctly

### Quality Checks
- **mypy**: Passed with no type errors
- **pylint**: Only pre-existing environment issue (psutil import, unrelated to changes)