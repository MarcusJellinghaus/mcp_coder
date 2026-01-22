# Step 1: Verify Test Imports and Create `readers.py`

## LLM Prompt
```
You are implementing Step 1 of Issue #317: Refactor git_operations layered architecture.
See pr_info/steps/summary.md for full context.

This step verifies existing tests use package-level imports (safety net),
then creates the new `readers.py` module.
```

## Overview
First ensure existing tests import from package level (`from mcp_coder.utils.git_operations import ...`) so they act as a safety net during refactoring. Then create `readers.py` with all read-only git operations.

---

## Part A: Verify Test Imports Use Package Level

### WHERE
`tests/utils/git_operations/test_branches.py` and `tests/utils/git_operations/test_repository.py`

### WHAT
Verify tests import from package level, not directly from submodules.

### HOW
```bash
# Check for direct submodule imports in tests
grep -r "from mcp_coder.utils.git_operations\.\(branches\|repository\)" tests/utils/git_operations/
```

If any tests import directly from submodules (e.g., `from ...branches import`), update them to use package-level imports (`from mcp_coder.utils.git_operations import ...`).

### VERIFICATION
```bash
# Run all git_operations tests to establish baseline
pytest tests/utils/git_operations/ -v
```

All tests should pass before proceeding.

---

## Part B: Create Implementation File

### WHERE
`src/mcp_coder/utils/git_operations/readers.py`

### WHAT
New module with all read-only git operations.

### HOW
1. Copy functions from `repository.py` (all functions)
2. Copy reader functions from `branches.py`:
   - `validate_branch_name`
   - `get_current_branch_name`
   - `get_default_branch_name`
   - `_check_local_default_branches`
   - `get_parent_branch_name`
   - `branch_exists`
   - `remote_branch_exists`
   - `extract_issue_number_from_branch`
3. Update imports to use `.core` only

### DATA
Functions use these imports from `.core`:
- `_safe_repo_context`
- `logger`

External imports:
- `Path` from `pathlib`
- `Optional` from `typing`
- `re` (for extract_issue_number_from_branch)
- `Repo` from `git`
- `GitCommandError`, `InvalidGitRepositoryError` from `git.exc`

### ALGORITHM (module structure)
```
1. Add module docstring
2. Import dependencies from core and standard library
3. Add repository status functions (is_git_repository, get_staged_changes, etc.)
4. Add branch validation function (validate_branch_name)
5. Add branch name reader functions (get_current_branch_name, etc.)
6. Add branch existence functions (branch_exists, remote_branch_exists)
7. Add utility function (extract_issue_number_from_branch)
```

### File Content Structure
```python
"""Read-only git operations for repository queries.

This module provides all read-only/query operations for git repositories.
These functions are used by multiple command modules (branches, remotes, etc.)
and form the middle layer of the git_operations architecture.

Architecture:
    Command modules (branches, remotes, commits, etc.) → readers → core
"""

import logging
import re
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger


# ============================================================================
# Repository Status Functions
# ============================================================================

def is_git_repository(project_dir: Path) -> bool:
    """Check if the project directory is a git repository."""
    ...

def get_staged_changes(project_dir: Path) -> list[str]:
    """Get list of files currently staged for commit."""
    ...

def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]:
    """Get list of files with unstaged changes."""
    ...

def get_full_status(project_dir: Path) -> dict[str, list[str]]:
    """Get comprehensive status of all changes."""
    ...

def is_working_directory_clean(
    project_dir: Path, ignore_files: list[str] | None = None
) -> bool:
    """Check if working directory has no uncommitted changes."""
    ...


# ============================================================================
# Branch Validation
# ============================================================================

def validate_branch_name(branch_name: str) -> bool:
    """Validate branch name against git naming rules."""
    ...


# ============================================================================
# Branch Name Readers
# ============================================================================

def get_current_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the current active branch."""
    ...

def get_default_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the default branch."""
    ...

def _check_local_default_branches(repo: Repo) -> Optional[str]:
    """Check for common default branch names in local repository."""
    ...

def get_parent_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the parent branch."""
    ...


# ============================================================================
# Branch Existence Checks
# ============================================================================

def branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists locally."""
    ...

def remote_branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists on the remote origin."""
    ...


# ============================================================================
# Branch Utilities
# ============================================================================

def extract_issue_number_from_branch(branch_name: str) -> Optional[int]:
    """Extract issue number from branch name pattern '{issue_number}-title'."""
    ...
```

---

## Verification

```bash
# Run new tests (should pass once implementation is complete)
pytest tests/utils/git_operations/test_readers.py -v

# Check for syntax/import errors
python -c "from mcp_coder.utils.git_operations.readers import *"

# Run pylint on new module
pylint src/mcp_coder/utils/git_operations/readers.py

# Run mypy on new module
mypy src/mcp_coder/utils/git_operations/readers.py
```

---

## Notes

- Create `readers.py` with exact copies of functions - no logic changes
- The new `readers.py` temporarily duplicates code from other modules
- Existing tests serve as safety net - run them after creating `readers.py` to verify no regressions
