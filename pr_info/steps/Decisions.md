# Decisions

## Decision 1: Test Strategy - Refactor Order

**Discussion:** Step 1 tests would fail until Step 2 completes because tests import from package level but `__init__.py` isn't updated until Step 2.

**Decision:** Reorder the approach:
1. Adjust test imports to package level first (if needed)
2. Run all tests to verify baseline
3. Refactor source code (create `readers.py`, update modules, update `__init__.py`)
4. Run all tests to verify refactoring
5. Reorganize test files last

**Rationale:** Tests act as safety net throughout, no intermediate failing state.

## Decision 2: Additional Internal Files Need Updating

**Discussion:** Grep revealed 4 internal `git_operations` modules that import from `repository` or `branches` for reader functions, but were not listed in the plan.

**Decision:** Add these files to Step 2:
- `staging.py` - imports `get_unstaged_changes, is_git_repository` from repository
- `file_tracking.py` - imports `is_git_repository` from repository
- `diffs.py` - imports reader functions from branches and repository
- `commits.py` - imports `get_full_status, get_staged_changes, is_git_repository` from repository

All these imports need to change from `.repository`/`.branches` to `.readers`.
