# Issue #317: Refactor git_operations - Layered Architecture with readers.py

## Summary

This refactoring eliminates a circular import between `branches.py` and `remotes.py` by introducing a **layered architecture** with clear dependency direction. The solution creates a new `readers.py` module for all read-only git operations.

## Architectural Changes

### Before: Circular Dependency
```
branches.py ──imports─→ remotes.py (fetch_remote)
     ↑                       │
     └───────imports─────────┘ (branch_exists)
```

### After: Layered Architecture (3 Layers)
```
Layer 1 (Commands - mutations):
  branches | remotes | commits | staging | file_tracking | diffs
      │         │
      └────┬────┘
           ▼
Layer 2 (Readers - queries):
       readers.py
           │
           ▼
Layer 3 (Infrastructure):
        core.py
```

**Key principle:** Dependencies only flow **downward**. Command modules cannot import from each other.

## Design Decisions

1. **readers.py** contains all read-only/query operations that multiple modules need
2. **rebase_onto_branch** moves to `remotes.py` since it's inherently remote-aware (operates on `origin/<branch>`)
3. **repository.py** is deleted - all functions moved to `readers.py`
4. **Public API unchanged** - `__init__.py` exports same names from new locations
5. **Import linter contract** enforces layering to prevent future regressions

## Functions Being Moved

### To `readers.py` (new file):
**From `repository.py`:**
- `is_git_repository`
- `get_staged_changes`
- `get_unstaged_changes`
- `get_full_status`
- `is_working_directory_clean`

**From `branches.py`:**
- `validate_branch_name`
- `get_current_branch_name`
- `get_default_branch_name`
- `_check_local_default_branches` (private helper)
- `get_parent_branch_name`
- `branch_exists`
- `remote_branch_exists`
- `extract_issue_number_from_branch`

### To `remotes.py`:
**From `branches.py`:**
- `rebase_onto_branch`

## Files to Create/Modify/Delete

| File | Action |
|------|--------|
| `src/mcp_coder/utils/git_operations/readers.py` | **CREATE** |
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY |
| `src/mcp_coder/utils/git_operations/remotes.py` | MODIFY |
| `src/mcp_coder/utils/git_operations/staging.py` | MODIFY (import path) |
| `src/mcp_coder/utils/git_operations/file_tracking.py` | MODIFY (import path) |
| `src/mcp_coder/utils/git_operations/diffs.py` | MODIFY (import path) |
| `src/mcp_coder/utils/git_operations/commits.py` | MODIFY (import path) |
| `src/mcp_coder/utils/git_operations/repository.py` | **DELETE** |
| `src/mcp_coder/utils/git_operations/__init__.py` | MODIFY |
| `.importlinter` | MODIFY |
| `src/mcp_coder/workflows/create_plan.py` | MODIFY (import path) |
| `src/mcp_coder/utils/github_operations/ci_results_manager.py` | MODIFY (import path) |
| `src/mcp_coder/utils/github_operations/issue_manager.py` | MODIFY (import path) |
| `src/mcp_coder/workflows/create_pr/core.py` | MODIFY (import path) |
| `src/mcp_coder/cli/commands/set_status.py` | MODIFY (import path) |
| `tests/utils/git_operations/test_readers.py` | **CREATE** |
| `tests/utils/git_operations/test_branches.py` | MODIFY |
| `tests/utils/git_operations/test_remotes.py` | MODIFY |
| `tests/utils/git_operations/test_repository.py` | **DELETE** |

## Constraints

- **No function logic changes** - Only move functions and update imports
- **Public API unchanged** - `__init__.py` exports same names
- **Tests mirror source** - Test files reflect module structure
- **Test imports** - Tests import from package level (`from mcp_coder.utils.git_operations import ...`)

## Implementation Steps Overview

| Step | Description |
|------|-------------|
| 1 | Verify test imports use package level, then create `readers.py` |
| 2 | Update all source modules (branches, remotes, staging, file_tracking, diffs, commits) |
| 3 | Update external imports and add import linter contract |
| 4 | Reorganize test files |

## Verification Commands

After each step:
```bash
# Check for import errors
pylint src/mcp_coder/utils/git_operations/

# Run tests
pytest tests/utils/git_operations/ -v

# Check type hints
mypy src/mcp_coder/utils/git_operations/

# Verify layering contract (after Step 3)
lint-imports
```
