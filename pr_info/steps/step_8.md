# Step 8: Create Remotes Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the remotes module containing all remote repository operations (push, fetch, GitHub URL parsing).

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
├── repository.py        # From Step 2
├── file_tracking.py     # From Step 3
├── staging.py           # From Step 4
├── commits.py           # From Step 5
├── branches.py          # From Step 6
├── diff.py              # From Step 7
└── remotes.py           # NEW (~150 lines)
```

## WHAT: Functions

```python
def git_push(project_dir: Path) -> dict[str, Any]:
    """Push current branch to origin remote."""

def push_branch(branch_name: str, project_dir: Path, set_upstream: bool = True) -> bool:
    """Push a git branch to origin remote."""

def fetch_remote(project_dir: Path, remote: str = "origin") -> bool:
    """Fetch latest changes from remote repository."""

def get_github_repository_url(project_dir: Path) -> Optional[str]:
    """Get GitHub repository URL from git remote origin."""

# Internal helper
def _parse_github_url(git_url: str) -> Optional[str]:
    """Parse git URL and convert to GitHub HTTPS format."""
```

## HOW: Integration

### Imports
```python
import logging
import re
from pathlib import Path
from typing import Any, Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .repository import is_git_repository
from .branches import branch_exists
```

### Dependencies
- Uses `_safe_repo_context()` from core.py
- Uses `is_git_repository()` from repository.py
- Uses `branch_exists()` from branches.py

## ALGORITHM: Key Logic

### `git_push(project_dir)`
```
1. If not is_git_repository(), return error dict
2. Use _safe_repo_context() to get repo
3. Get current_branch = repo.active_branch.name
4. Execute: repo.git.push("origin", current_branch)
5. Return {success: True, error: None} on success
6. Return {success: False, error: msg} on GitCommandError
```

### `push_branch(branch_name, project_dir, set_upstream)`
```
1. Validate branch_name not empty
2. If not is_git_repository(), return False
3. Check branch_exists(), return False if not
4. Check origin remote exists, return False if not
5. If set_upstream: repo.git.push("--set-upstream", "origin", branch_name)
6. Else: repo.git.push("origin", branch_name)
7. Return True on success, False on GitCommandError
```

### `fetch_remote(project_dir, remote)`
```
1. Validate remote name not empty
2. If not is_git_repository(), return False
3. Check remote exists in repo.remotes, return False if not
4. Execute: repo.git.fetch(remote)
5. Return True on success, False on GitCommandError
```

### `get_github_repository_url(project_dir)`
```
1. If not is_git_repository(), return None
2. Check 'origin' remote exists, return None if not
3. Get origin URL: repo.remotes.origin.url
4. Call _parse_github_url(origin_url)
5. Return parsed GitHub URL or None
```

### `_parse_github_url(git_url)`
```
1. Define regex pattern for GitHub URLs (SSH and HTTPS)
2. Match pattern against git_url
3. If no match, return None
4. Extract owner and repo_name from match groups
5. Return formatted HTTPS URL: https://github.com/{owner}/{repo_name}
```

## DATA: Return Values

- `git_push()`: dict[str, Any]
  ```python
  {"success": True, "error": None}  # On success
  {"success": False, "error": "error message"}  # On failure
  ```

- `push_branch()`: bool
- `fetch_remote()`: bool  
- `get_github_repository_url()`: Optional[str] (HTTPS GitHub URL or None)
- `_parse_github_url()`: Optional[str] (internal helper)

## Implementation Steps

1. **Create `remotes.py`**
   - Copy from original `git_operations.py`:
     - `git_push()` (lines ~759-791)
     - `get_github_repository_url()` (lines ~794-826)
     - `_parse_github_url()` (lines ~1480-1502)
     - `push_branch()` (lines ~1321-1381)
     - `fetch_remote()` (lines ~1384-1423)
   - Add imports from `.core`, `.repository`, `.branches`
   - Also import `re` for URL parsing
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_git_push_*`
- `tests/utils/test_git_workflows.py::TestGitBranchOperations::test_push_branch_*`
- `tests/utils/test_git_workflows.py::TestGitBranchOperations::test_fetch_remote_*`
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitWorkflows::test_git_push_basic_workflow"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 8 - Create remotes.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/remotes.py
2. Import from .core: _safe_repo_context, logger
3. Import from .repository: is_git_repository
4. Import from .branches: branch_exists
5. Also import: import re (for URL parsing)
6. Copy these functions from original git_operations.py:
   - git_push()
   - push_branch()
   - fetch_remote()
   - get_github_repository_url()
   - _parse_github_url()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, logger
- from .repository import is_git_repository
- from .branches import branch_exists
- import re

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Run test: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitWorkflows::test_git_push_basic_workflow -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
