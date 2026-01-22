# Step 2: Update Source Modules and Package Exports

## LLM Prompt
```
You are implementing Step 2 of Issue #317: Refactor git_operations layered architecture.
See pr_info/steps/summary.md for full context.

This step updates all source modules to use the new readers.py layer.
```

## Overview
Update all source modules to use the new layered architecture:
1. Updates `branches.py` to import from `readers.py` and removes moved functions
2. Updates `remotes.py` to import from `readers.py` and adds `rebase_onto_branch`
3. Updates `staging.py`, `file_tracking.py`, `diffs.py`, `commits.py` to import from `readers.py`
4. Updates `__init__.py` to re-export from new locations
5. Deletes `repository.py` (all functions now in `readers.py`)

---

## Part A: Update branches.py

### WHERE
`src/mcp_coder/utils/git_operations/branches.py`

### WHAT
Remove all reader functions (moved to `readers.py`) and import them instead.
Remove `rebase_onto_branch` (moved to `remotes.py`).

### HOW
1. Update imports: add imports from `.readers`
2. Remove import of `is_git_repository` from `.repository`
3. Remove these functions (now in `readers.py`):
   - `validate_branch_name`
   - `get_current_branch_name`
   - `get_default_branch_name`
   - `_check_local_default_branches`
   - `get_parent_branch_name`
   - `branch_exists`
   - `remote_branch_exists`
   - `extract_issue_number_from_branch`
4. Remove `rebase_onto_branch` (moving to `remotes.py`)

### ALGORITHM
```
1. Replace "from .repository import is_git_repository" with "from .readers import is_git_repository, validate_branch_name, branch_exists"
2. Delete validate_branch_name function definition
3. Delete get_current_branch_name function definition
4. Delete get_default_branch_name function definition
5. Delete _check_local_default_branches function definition
6. Delete get_parent_branch_name function definition
7. Delete branch_exists function definition
8. Delete remote_branch_exists function definition
9. Delete extract_issue_number_from_branch function definition
10. Delete rebase_onto_branch function definition
11. Remove unused imports (re, Repo if no longer needed)
```

### DATA - Remaining functions in branches.py
After changes, `branches.py` should only contain these **mutation** functions:
- `create_branch`
- `checkout_branch`
- `delete_branch`

### File Structure After Changes
```python
"""Branch operations for git repositories."""

import logging
from pathlib import Path
from typing import Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .readers import branch_exists, is_git_repository, validate_branch_name


def create_branch(
    branch_name: str, project_dir: Path, from_branch: Optional[str] = None
) -> bool:
    """Create a new git branch."""
    ...

def checkout_branch(branch_name: str, project_dir: Path) -> bool:
    """Checkout an existing git branch, creating from remote if needed."""
    ...

def delete_branch(
    branch_name: str,
    project_dir: Path,
    force: bool = False,
    delete_remote: bool = False,
) -> bool:
    """Delete a git branch locally and optionally from remote."""
    ...
```

---

## Part B: Update remotes.py

### WHERE
`src/mcp_coder/utils/git_operations/remotes.py`

### WHAT
1. Update imports to use `readers.py` instead of `branches.py` and `repository.py`
2. Add `rebase_onto_branch` function (moved from `branches.py`)

### HOW
1. Replace `from .branches import branch_exists` with `from .readers import branch_exists`
2. Replace `from .repository import is_git_repository` with `from .readers import is_git_repository`
3. Add `rebase_onto_branch` function at the end of the file
4. Update `rebase_onto_branch` to import `fetch_remote` directly (no circular import now)

### ALGORITHM
```
1. Update import: from .readers import branch_exists, is_git_repository
2. Remove import from .branches
3. Remove import from .repository
4. Add rebase_onto_branch function (copy from branches.py)
5. In rebase_onto_branch, remove the conditional import of fetch_remote
6. Instead, just call fetch_remote directly (it's in the same module now)
```

### DATA - rebase_onto_branch signature
```python
def rebase_onto_branch(project_dir: Path, target_branch: str) -> bool:
    """Attempt to rebase current branch onto origin/<target_branch>."""
```

### File Structure After Changes
```python
"""Git remote operations for push, fetch, and GitHub URL parsing."""

import logging
import re
from pathlib import Path
from typing import Any, Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .readers import branch_exists, is_git_repository


def git_push(project_dir: Path, force_with_lease: bool = False) -> dict[str, Any]:
    ...

def push_branch(branch_name: str, project_dir: Path, set_upstream: bool = True) -> bool:
    ...

def fetch_remote(project_dir: Path, remote: str = "origin") -> bool:
    ...

def get_github_repository_url(project_dir: Path) -> Optional[str]:
    ...

def _parse_github_url(git_url: str) -> Optional[str]:
    ...

def rebase_onto_branch(project_dir: Path, target_branch: str) -> bool:
    """Attempt to rebase current branch onto origin/<target_branch>.
    
    NOTE: This function was moved from branches.py because it's inherently
    remote-aware (operates on origin/<branch>) and required fetch_remote.
    """
    # No longer needs conditional import - fetch_remote is in same module
    ...
```

---

## Part C: Update Other Internal Modules

Update imports in these files to use `readers.py` instead of `repository.py` or `branches.py`:

### staging.py
```python
# Change:
from .repository import get_unstaged_changes, is_git_repository
# To:
from .readers import get_unstaged_changes, is_git_repository
```

### file_tracking.py
```python
# Change:
from .repository import is_git_repository
# To:
from .readers import is_git_repository
```

### diffs.py
```python
# Change:
from .branches import (
    branch_exists,
    get_current_branch_name,
    get_parent_branch_name,
    remote_branch_exists,
)
from .repository import is_git_repository
# To:
from .readers import (
    branch_exists,
    get_current_branch_name,
    get_parent_branch_name,
    is_git_repository,
    remote_branch_exists,
)
```

### commits.py
```python
# Change:
from .repository import get_full_status, get_staged_changes, is_git_repository
# To:
from .readers import get_full_status, get_staged_changes, is_git_repository
```

---

## Part D: Update __init__.py

### WHERE
`src/mcp_coder/utils/git_operations/__init__.py`

### WHAT
Update import sources to reflect new module locations while keeping the same public API.

### HOW
1. Import reader functions from `.readers` instead of `.branches` and `.repository`
2. Import `rebase_onto_branch` from `.remotes` instead of `.branches`
3. Remove import from `.repository`

### ALGORITHM
```
1. Change branch reader imports to come from .readers
2. Change repository imports to come from .readers
3. Change rebase_onto_branch import to come from .remotes
4. Remove the "from .repository import" line entirely
5. Keep __all__ list unchanged (same public API)
```

### DATA - Import changes
| Function | Old Source | New Source |
|----------|-----------|------------|
| `branch_exists` | `.branches` | `.readers` |
| `extract_issue_number_from_branch` | `.branches` | `.readers` |
| `get_current_branch_name` | `.branches` | `.readers` |
| `get_default_branch_name` | `.branches` | `.readers` |
| `get_parent_branch_name` | `.branches` | `.readers` |
| `remote_branch_exists` | `.branches` | `.readers` |
| `validate_branch_name` | `.branches` | `.readers` |
| `rebase_onto_branch` | `.branches` | `.remotes` |
| `get_full_status` | `.repository` | `.readers` |
| `get_staged_changes` | `.repository` | `.readers` |
| `get_unstaged_changes` | `.repository` | `.readers` |
| `is_git_repository` | `.repository` | `.readers` |
| `is_working_directory_clean` | `.repository` | `.readers` |

### File Content After Changes
```python
"""Git operations package - modular git utilities."""

# Branch mutation operations
from .branches import (
    checkout_branch,
    create_branch,
    delete_branch,
)

# Branch reader operations (from readers module)
from .readers import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_parent_branch_name,
    remote_branch_exists,
    validate_branch_name,
)

# Repository status operations (from readers module)
from .readers import (
    get_full_status,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
)

# Commit operations
from .commits import commit_all_changes, commit_staged_files

# Core types and utilities
from .core import CommitResult, PushResult

# Diff operations
from .diffs import get_branch_diff, get_git_diff_for_commit

# File tracking operations
from .file_tracking import git_move, is_file_tracked

# Remote operations (including rebase_onto_branch)
from .remotes import (
    fetch_remote,
    get_github_repository_url,
    git_push,
    push_branch,
    rebase_onto_branch,
)

# Staging operations
from .staging import stage_all_changes, stage_specific_files

__all__ = [
    # ... same as before, unchanged ...
]
```

---

## Part E: Delete repository.py

### WHERE
`src/mcp_coder/utils/git_operations/repository.py`

### WHAT
Delete the file entirely - all functions are now in `readers.py`.

### HOW
```bash
rm src/mcp_coder/utils/git_operations/repository.py
```

---

## Verification

```bash
# Check for import errors in all modules
python -c "from mcp_coder.utils.git_operations import *"

# Run all git_operations tests
pytest tests/utils/git_operations/ -v

# Run pylint on modified modules
pylint src/mcp_coder/utils/git_operations/

# Run mypy on modified modules
mypy src/mcp_coder/utils/git_operations/
```

---

## Notes

- All changes in this step are **atomic** - they must all succeed together
- Public API remains unchanged (`__all__` list is identical)
- Function implementations have **no logic changes** - only moved between files
- Conditional import in `rebase_onto_branch` is removed (no longer needed)
