# Issue #538: Split branch_manager.py into branch_naming.py

## Goal

Extract two standalone symbols (`BranchCreationResult`, `generate_branch_name_from_issue`) from
`branch_manager.py` (778 lines) into a new `branch_naming.py` (~80 lines) in the same package.
This brings `branch_manager.py` under the 750-line limit.

## Architectural / Design Changes

- **No behavioral changes.** This is a pure move-only refactoring per the #263 methodology.
- **New module:** `src/mcp_coder/utils/github_operations/issues/branch_naming.py` contains the
  `BranchCreationResult` TypedDict and the pure function `generate_branch_name_from_issue`.
- **Dependency direction:** `branch_manager.py` imports from `branch_naming.py` (not the reverse).
  The two extracted symbols have zero coupling to `IssueBranchManager` internals.
- **Public API unchanged:** `__init__.py` re-exports both symbols — consumers importing from the
  package see no change.

## Files to Create

| File | Purpose |
|------|---------|
| `src/mcp_coder/utils/github_operations/issues/branch_naming.py` | New home for `BranchCreationResult` + `generate_branch_name_from_issue` |
| `tests/utils/github_operations/test_branch_naming.py` | Tests for branch naming (moved from `test_issue_branch_manager.py`) |

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/issues/branch_manager.py` | Remove moved symbols, add import from `branch_naming` |
| `src/mcp_coder/utils/github_operations/issues/__init__.py` | Update re-exports to source from `branch_naming` |
| `tests/utils/github_operations/test_issue_branch_manager.py` | Remove `TestBranchNameGeneration` class |
| `.large-files-allowlist` | Remove `branch_manager.py` entry (conditional on < 750 lines) |

## Steps Overview

| Step | Description |
|------|-------------|
| 1 | Move `BranchCreationResult` and `generate_branch_name_from_issue` to `branch_naming.py`, update `__init__.py` |
| 2 | Move `TestBranchNameGeneration` tests to `test_branch_naming.py`, remove from allowlist |
