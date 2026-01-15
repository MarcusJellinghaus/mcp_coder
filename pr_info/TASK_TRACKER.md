# MCP Coder Task Tracker

## Overview

This tracks **Feature Implementation** consisting of multiple **Implementation Steps**.

- **Feature**: A complete user-facing capability
- **Implementation Step**: A self-contained unit of work (tests + implementation)

## Status Legend

- [x] = Implementation step complete
- [ ] = Implementation step not complete
- Each task links to a detail file in pr_info/steps/ folder

---

## Tasks

### Step 1: Implement Simplified find_data_file with importlib.resources
[Details: pr_info/steps/step_1.md]

- [x] Rewrite `find_data_file()` function in `src/mcp_coder/utils/data_files.py` to use `importlib.resources.files()`
- [x] Remove `development_base_dir` parameter from `find_data_file()` (Decision #6)
- [x] Add verbose logging (~10+ statements) for troubleshooting (Decision #3)
- [x] Implement error handling: ModuleNotFoundError → FileNotFoundError conversion (Decision #2)
- [x] Use `Path(str(resource))` for Traversable to Path conversion (Decision #1)
- [x] Update `find_package_data_files()` to remove `development_base_dir` parameter (Decision #12)
- [x] Update `src/mcp_coder/prompt_manager.py` to remove `development_base_dir=None` arguments from calls
- [x] Remove unused imports: `importlib.util`, `site`, `os`, `sys` (kept `importlib` for `get_package_directory`)
- [x] Run pylint check on modified files
- [x] Run pytest for `tests/utils/test_data_files.py` (EXPECTED TO FAIL - tests use old API, to be fixed in Step 2)
- [x] Run pytest for `tests/test_prompt_manager.py` (EXPECTED TO PASS - no direct dependency on removed parameter)
- [x] Run mypy check on `src/mcp_coder/utils` (PASSED)
- [x] Prepare git commit message for Step 1

**Commit Message for Step 1:**
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

### Step 2: Simplify Tests for find_data_file
[Details: pr_info/steps/step_2.md]

- [ ] Remove `test_find_development_file_new_structure` test (Decision #7)
- [ ] Rename and convert `test_find_installed_file_via_importlib` to `test_find_file_in_installed_package` using real `mcp_coder` package (Decision #11)
- [ ] Remove `test_find_installed_file_via_module_file` test (redundant) (Decision #11)
- [ ] Update `test_pyproject_toml_consistency` to remove `development_base_dir` argument (Decision #8)
- [ ] Convert `test_data_file_found_logs_at_debug_level` to use real `mcp_coder` package (Decision #9)
- [ ] Update `test_find_multiple_files` in `TestFindPackageDataFiles` to use real `mcp_coder` files (Decision #10)
- [ ] Keep `test_file_not_found_raises_exception` unchanged
- [ ] Keep all `TestGetPackageDirectory` tests unchanged (Decision #5)
- [ ] Run pylint check on test files
- [ ] Run pytest for `tests/utils/test_data_files.py` with verbose output
- [ ] Run pytest with `-n auto` to verify pytest-xdist parallel execution works
- [ ] Run mypy check on test files
- [ ] Prepare git commit message for Step 2

### Step 3: Final Verification and Cleanup
[Details: pr_info/steps/step_3.md]

- [ ] Run all data_files tests with pytest-xdist (`-n auto`)
- [ ] Run prompt_manager tests to verify compatibility
- [ ] Verify pytest-xdist parallel execution works (original issue fix validation)
- [ ] Clean up any remaining unused imports in `data_files.py`
- [ ] Run mypy type checking on entire `src/mcp_coder/utils` directory
- [ ] Run full unit test suite with markers exclusion
- [ ] Update docstring in `find_data_file` to reflect new implementation
- [ ] Verify code reduced from ~350 to ~50 lines
- [ ] Run pylint check on all modified files
- [ ] Run pytest full suite
- [ ] Run mypy full check
- [ ] Prepare git commit message for Step 3

---

## Pull Request

- [ ] Review all implementation steps are complete
- [ ] Verify all tests pass with pytest-xdist (`-n auto`)
- [ ] Verify no type errors from mypy
- [ ] Verify no pylint errors
- [ ] Create PR summary with:
  - Description of changes (importlib.resources refactoring)
  - List of files modified
  - Test results summary
  - Breaking changes noted (removal of `development_base_dir` parameter)
- [ ] Prepare final PR commit message
