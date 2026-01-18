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

### Step 1: Create issue_cache.py Module
_See: [pr_info/steps/step_1.md](steps/step_1.md)_

- [x] Move `DUPLICATE_PROTECTION_SECONDS` constant to `src/mcp_coder/constants.py`
- [x] Create `src/mcp_coder/utils/github_operations/issue_cache.py` module
- [x] Move `CacheData` TypedDict to issue_cache.py
- [x] Move `_load_cache_file()` to issue_cache.py
- [x] Move `_save_cache_file()` to issue_cache.py
- [x] Move `_get_cache_file_path()` to issue_cache.py
- [x] Move `_log_cache_metrics()` to issue_cache.py
- [x] Move `_log_stale_cache_entries()` to issue_cache.py
- [x] Move `_update_issue_labels_in_cache()` to issue_cache.py
- [x] Create new `get_all_cached_issues()` function extracting caching logic
- [x] Run pylint on issue_cache.py and fix any issues
- [x] Run mypy on issue_cache.py and fix any type errors
- [x] Run pytest for related tests and ensure they pass
- [x] Prepare git commit message for Step 1

**Commit message for Step 1:**
```
feat(cache): add issue_cache module to github_operations

Create new issue_cache.py module in utils/github_operations/ with:
- CacheData TypedDict for cache structure
- Cache file operations (_load_cache_file, _save_cache_file, _get_cache_file_path)
- Cache metrics logging (_log_cache_metrics, _log_stale_cache_entries)
- Cache update function (_update_issue_labels_in_cache)
- New get_all_cached_issues() function extracting caching logic

This is Step 1 of the cache refactoring - the new module is created but
coordinator/core.py still has the original functions (to be removed in Step 2).

Part of: Issue #257 - Refactor Cache Logic to github_operations
```

### Step 2: Update coordinator/core.py to Use issue_cache
_See: [pr_info/steps/step_2.md](steps/step_2.md)_

- [ ] Remove moved functions from `src/mcp_coder/cli/commands/coordinator/core.py`
- [ ] Add imports from `mcp_coder.utils.github_operations.issue_cache`
- [ ] Update `workflow_constants.py` to import `DUPLICATE_PROTECTION_SECONDS` from constants.py
- [ ] Rewrite `get_cached_eligible_issues()` as thin wrapper calling `get_all_cached_issues()` and `_filter_eligible_issues()`
- [ ] Keep `_filter_eligible_issues()` in place (coordinator-specific)
- [ ] Keep `get_eligible_issues()` in place (fallback logic)
- [ ] Run pylint on coordinator/core.py and fix any issues
- [ ] Run mypy on coordinator/core.py and fix any type errors
- [ ] Run pytest for coordinator tests and ensure they pass
- [ ] Prepare git commit message for Step 2

### Step 3: Update Module Exports
_See: [pr_info/steps/step_3.md](steps/step_3.md)_

- [ ] Update `src/mcp_coder/utils/github_operations/__init__.py` with issue_cache exports
- [ ] Add `CacheData`, `get_all_cached_issues`, `_update_issue_labels_in_cache` to `__all__`
- [ ] Update `src/mcp_coder/cli/commands/coordinator/__init__.py` exports
- [ ] Remove private cache function exports from coordinator `__init__.py`
- [ ] Verify imports work: `from mcp_coder.utils.github_operations import CacheData, get_all_cached_issues`
- [ ] Verify imports work: `from mcp_coder.cli.commands.coordinator import CacheData, get_cached_eligible_issues`
- [ ] Run pylint on __init__.py files and fix any issues
- [ ] Run mypy on __init__.py files and fix any type errors
- [ ] Run pytest for module export tests and ensure they pass
- [ ] Prepare git commit message for Step 3

### Step 4: Move and Update Test File
_See: [pr_info/steps/step_4.md](steps/step_4.md)_

- [ ] Create `tests/utils/github_operations/test_issue_cache.py`
- [ ] Copy test content from `tests/utils/test_coordinator_cache.py`
- [ ] Update imports to use `mcp_coder.utils.github_operations.issue_cache`
- [ ] Update all patch paths from coordinator to issue_cache
- [ ] Update logger paths in caplog.set_level calls
- [ ] Add fixtures to `tests/utils/github_operations/conftest.py` (sample_issue, sample_cache_data, mock_cache_issue_manager)
- [ ] Remove fixture definitions from test file (use conftest.py)
- [ ] Run pytest on `tests/utils/github_operations/test_issue_cache.py` to verify tests pass
- [ ] Run pytest on coordinator tests to ensure they still pass
- [ ] Delete original `tests/utils/test_coordinator_cache.py` after verification
- [ ] Run pylint on test files and fix any issues
- [ ] Run mypy on test files and fix any type errors
- [ ] Run full pytest suite and ensure all tests pass
- [ ] Prepare git commit message for Step 4

### Step 5: Run Verification Checks
_See: [pr_info/steps/step_5.md](steps/step_5.md)_

- [ ] Run import linter (`lint-imports`) and fix any violations
- [ ] Run tach (`tach check`) and fix any dependency violations
- [ ] Run pytest for all moved tests: `tests/utils/github_operations/test_issue_cache.py`
- [ ] Run pytest for coordinator tests: `tests/cli/commands/coordinator/`
- [ ] Run mypy on target directories and fix any errors
- [ ] Run pylint on target directories and fix any errors/warnings
- [ ] Verify `tests/utils/test_coordinator_cache.py` is deleted
- [ ] Verify `tests/utils/github_operations/test_issue_cache.py` exists and passes
- [ ] Verify `src/mcp_coder/utils/github_operations/issue_cache.py` exists
- [ ] Verify all cache helpers moved to issue_cache.py
- [ ] Verify `get_all_cached_issues()` created in issue_cache.py
- [ ] Verify `get_cached_eligible_issues()` is thin wrapper in coordinator
- [ ] Verify `_filter_eligible_issues()` unchanged in coordinator
- [ ] Verify all exports updated in `__init__.py` files
- [ ] Prepare git commit message for Step 5

---

## Pull Request

### PR Review and Summary
- [ ] Review all implementation steps are complete
- [ ] Verify all tests pass with `pytest`
- [ ] Verify code quality with `pylint`, `mypy`
- [ ] Verify architectural boundaries with `lint-imports` and `tach check`
- [ ] Create PR summary documenting changes made
- [ ] Prepare final PR review checklist
