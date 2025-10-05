# Step 6: Create Branches Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the branches module containing all branch-related operations (query, create, checkout, etc.).

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
├── repository.py        # From Step 2
├── file_tracking.py     # From Step 3
├── staging.py           # From Step 4
├── commits.py           # From Step 5
└── branches.py          # NEW (~250 lines)
```

## WHAT: Functions

```python
def get_current_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the current active branch."""

def get_default_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the default branch from git remote HEAD reference."""

def get_parent_branch_name(project_dir: Path) -> Optional[str]:
    """Get the name of the parent branch (main or master)."""

def create_branch(branch_name: str, project_dir: Path, from_branch: Optional[str] = None) -> bool:
    """Create a new git branch."""

def checkout_branch(branch_name: str, project_dir: Path) -> bool:
    """Checkout an existing git branch."""

def branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists locally."""

# Internal helper
def _check_local_default_branches(repo: Repo) -> Optional[str]:
    """Check for common default branch names in local repository."""
```

## HOW: Integration

### Imports
```python
import logging
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .repository import is_git_repository
```

### Used By (Future Steps)
- `diff.py`: Uses `get_current_branch_name()`, `branch_exists()`
- `remotes.py`: Uses `get_current_branch_name()`, `branch_exists()`

## ALGORITHM: Key Logic

### `get_current_branch_name(project_dir)`
```
1. If not is_git_repository(), return None
2. Use _safe_repo_context() to get repo
3. Try: current_branch = repo.active_branch.name
4. If TypeError (detached HEAD), return None
5. Return current_branch name
```

### `get_default_branch_name(project_dir)`
```
1. If not is_git_repository(), return None
2. Check if 'origin' remote exists
3. If no origin, call _check_local_default_branches()
4. Try: result = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
5. If success, parse branch name from result
6. If GitCommandError, fall back to _check_local_default_branches()
7. Return branch name or None
```

### `_check_local_default_branches(repo)`
```
1. Get all branch names: [branch.name for branch in repo.branches]
2. Check for "main" first, return if found
3. Check for "master", return if found
4. Return None if neither exists
```

### `create_branch(branch_name, project_dir, from_branch)`
```
1. Validate branch_name not empty, contains no invalid chars
2. If not is_git_repository(), return False
3. Check if branch already exists, return False if yes
4. If from_branch specified: repo.git.checkout("-b", branch_name, from_branch)
5. Else: repo.git.checkout("-b", branch_name)
6. Return True on success, False on GitCommandError
```

### `checkout_branch(branch_name, project_dir)`
```
1. Validate branch_name not empty
2. If not is_git_repository(), return False
3. Check if branch exists locally, return False if not
4. Check if already on target branch, return True if yes
5. Execute: repo.git.checkout(branch_name)
6. Return True on success, False on GitCommandError
```

### `branch_exists(project_dir, branch_name)`
```
1. If not is_git_repository() or empty branch_name, return False
2. Use _safe_repo_context() to get repo
3. Get branch names: [branch.name for branch in repo.branches]
4. Return True if branch_name in list, else False
```

## DATA: Return Values

- `get_current_branch_name()`: Optional[str] (None if detached HEAD or invalid repo)
- `get_default_branch_name()`: Optional[str] (None if no default found)
- `get_parent_branch_name()`: Optional[str] (delegates to get_default_branch_name)
- `create_branch()`: bool
- `checkout_branch()`: bool
- `branch_exists()`: bool
- `_check_local_default_branches()`: Optional[str] (internal helper)

## Implementation Steps

1. **Create `branches.py`**
   - Copy from original `git_operations.py`:
     - `get_current_branch_name()` (lines ~924-958)
     - `get_default_branch_name()` (lines ~961-1021)
     - `_check_local_default_branches()` (lines ~1024-1051)
     - `get_parent_branch_name()` (lines ~1054-1079)
     - `create_branch()` (lines ~1158-1223)
     - `checkout_branch()` (lines ~1226-1279)
     - `branch_exists()` (lines ~1282-1318)
   - Add imports from `.core` and `.repository`
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitBranchOperations`
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitBranchOperations"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 6 - Create branches.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/branches.py
2. Import from .core: _safe_repo_context, logger
3. Import from .repository: is_git_repository
4. Also import: from git import Repo (needed for _check_local_default_branches)
5. Copy these functions from original git_operations.py:
   - get_current_branch_name()
   - get_default_branch_name()
   - _check_local_default_branches()
   - get_parent_branch_name()
   - create_branch()
   - checkout_branch()
   - branch_exists()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, logger
- from .repository import is_git_repository
- from git import Repo (for type hints in _check_local_default_branches)

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Run tests: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitBranchOperations -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
