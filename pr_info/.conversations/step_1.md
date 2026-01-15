# Implementation Task: Rewrite `find_data_file()` function in `src/mcp_coder/utils/data_files.py` to use `importlib.resources.files()`

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Prepare commit message when that sub-task appears
- Do NOT commit - just prepare the message

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Rewrite `find_data_file()` function in `src/mcp_coder/utils/data_files.py` to use `importlib.resources.files()`

Please implement this task step by step.

## LLM Response:
## Step 1 Complete - Summary

I have completed **Step 1: Implement Simplified find_data_file with importlib.resources**. Here's what was done:

### Files Modified:
1. **`src/mcp_coder/utils/data_files.py`**
   - Rewrote `find_data_file()` to use `importlib.resources.files()` (~95 lines vs ~250 lines)
   - Removed `development_base_dir` parameter (Decision #6)
   - Added 10+ verbose logging statements (Decision #3)
   - Implemented `ModuleNotFoundError` → `FileNotFoundError` conversion (Decision #2)
   - Used `Path(str(resource))` for Traversable to Path conversion (Decision #1)
   - Updated `find_package_data_files()` to remove `development_base_dir` parameter (Decision #12)
   - Kept `get_package_directory()` unchanged (Decision #4)

2. **`src/mcp_coder/prompt_manager.py`**
   - Removed `development_base_dir=None` arguments from two `find_data_file()` calls

3. **`pr_info/TASK_TRACKER.md`**
   - Marked all Step 1 sub-tasks as complete
   - Added prepared git commit message

### Code Quality Checks:
- **Pylint**: Passed (only pre-existing warnings in other files)
- **Mypy**: Passed - no type errors
- **Tests**: Expected to fail until Step 2 updates them (tests still use removed `development_base_dir` parameter)

### Prepared Commit Message:
```
refactor(data_files): simplify find_data_file using importlib.resources

Replace complex 5-method file search with single importlib.resources.files() call.
This addresses Issue #285 by using Python 3.9+ standard library for robust
package data file discovery that works correctly with pytest-xdist.

Breaking changes:
- Remove `development_base_dir` parameter from `find_data_file()`
- Remove `development_base_dir` parameter from `find_package_data_files()`

Changes:
- Rewrite find_data_file() to use importlib.resources.files()
- Convert ModuleNotFoundError to FileNotFoundError for backwards compatibility
- Use Path(str(resource)) for Traversable to Path conversion
- Add verbose logging (~10+ statements) for troubleshooting
- Update prompt_manager.py to remove development_base_dir=None arguments
- Remove unused imports (site, os, sys) - kept importlib for get_package_directory

Note: Tests in tests/utils/test_data_files.py will fail until Step 2 updates them.
```

---
Generated on: 2026-01-15T16:30:04.933776