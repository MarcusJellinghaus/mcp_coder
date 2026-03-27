# Issue #539: Split large test file test_branch_resolution.py

## Overview

Split `tests/utils/github_operations/issues/test_branch_resolution.py` (1102 lines, limit 750) into 3 focused test files + 1 shared conftest, then delete the original.

This is a **pure refactoring** — no logic changes, only moves and import adjustments.

## Architectural / Design Changes

- **No source code changes** — only test files are affected
- **No API changes** — test files have no external consumers
- **Shared fixture extraction** — the identical `mock_manager` fixture duplicated in 2 test classes is extracted into a `conftest.py`, removing duplication
- **Test organization** — each test class gets its own file, following the project's pattern of focused, small test files

## Files Created

| File | Contents | ~Lines |
|------|----------|--------|
| `tests/utils/github_operations/issues/conftest.py` | Shared `mock_manager` fixture | ~30 |
| `tests/utils/github_operations/issues/test_extract_prs_by_states.py` | `TestExtractPrsByStates` (6 tests) | ~110 |
| `tests/utils/github_operations/issues/test_get_branch_with_pr_fallback.py` | `TestGetBranchWithPRFallback` (20 tests) | ~710 |
| `tests/utils/github_operations/issues/test_search_branches_by_pattern.py` | `TestSearchBranchesByPattern` + `_make_git_ref` helper (6 tests) | ~270 |

## Files Deleted

| File | Reason |
|------|--------|
| `tests/utils/github_operations/issues/test_branch_resolution.py` | Replaced by the 3 new test files above |

## Files Unchanged

| File | Note |
|------|------|
| `tests/utils/github_operations/issues/__init__.py` | Already exists, no changes needed |

## Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | Create `conftest.py` + `test_extract_prs_by_states.py` + `test_search_branches_by_pattern.py` | "refactor: extract conftest and smaller test classes from test_branch_resolution" |
| 2 | Create `test_get_branch_with_pr_fallback.py`, delete original file | "refactor: complete split of test_branch_resolution.py (#539)" |

## Key Decisions

- **2 steps instead of 4**: Since this is a pure move (no TDD needed — tests already exist), we group the smaller files in step 1 and the large file + deletion in step 2. Each step is independently verifiable.
- **No `move_symbol` tools**: Test files have no external consumers, so direct file creation + deletion is simpler.
- **Verbatim moves**: Code is copied exactly as-is, only imports and fixture references change.
