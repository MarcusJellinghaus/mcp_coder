# Step 2: Create Repository Module (Status & Validation)

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the repository module containing repository validation, status checking, and change detection functions.

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
└── repository.py        # NEW (~150 lines)
```

## WHAT: Functions

```python
def is_git_repository(project_dir: Path) -> bool:
    """Check if the project directory is a git repository."""

def get_staged_changes(project_dir: Path) -> list[str]:
    """Get list of files currently staged for commit."""

def get_unstaged_changes(project_dir: Path) -> dict[str, list[str]]:
    """Get list of files with unstaged changes (modified and untracked)."""

def get_full_status(project_dir: Path) -> dict[str, list[str]]:
    """Get comprehensive status of all changes: staged, modified, and untracked files."""

def is_working_directory_clean(project_dir: Path) -> bool:
    """Check if working directory has no uncommitted changes."""
```

## HOW: Integration

### Imports
```python
import logging
from pathlib import Path
from typing import Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
```

### Used By (Future Steps)
- `staging.py`: Uses `get_full_status()`, `get_unstaged_changes()`
- `commits.py`: Uses `get_staged_changes()`, `is_git_repository()`
- `diff.py`: Uses `is_git_repository()`
- `branches.py`: Uses `is_git_repository()`
- `remotes.py`: Uses `is_git_repository()`

## ALGORITHM: Key Logic

### `is_git_repository(project_dir)`
```
1. Try to create Repo object via _safe_repo_context(project_dir)
2. If successful, return True
3. If InvalidGitRepositoryError, return False
4. Log errors and return False for other exceptions
```

### `get_staged_changes(project_dir)`
```
1. If not is_git_repository(), return []
2. Use _safe_repo_context() to get repo
3. Execute: repo.git.diff("--cached", "--name-only")
4. Split output by newlines, filter empty strings
5. Return list of staged file paths
```

### `get_unstaged_changes(project_dir)`
```
1. If not is_git_repository(), return {modified: [], untracked: []}
2. Use _safe_repo_context() to get repo
3. Execute: repo.git.status("--porcelain", "-u")
4. Parse each line: check working tree status (second char)
5. Separate into modified and untracked lists
6. Return dict with both lists
```

### `get_full_status(project_dir)`
```
1. Call get_staged_changes(project_dir)
2. Call get_unstaged_changes(project_dir)
3. Combine into dict with staged, modified, untracked keys
4. Return combined status dict
```

### `is_working_directory_clean(project_dir)`
```
1. If not is_git_repository(), raise ValueError
2. Call get_full_status(project_dir)
3. Sum lengths of staged, modified, untracked lists
4. Return True if sum == 0, else False
```

## DATA: Return Values

- `is_git_repository()`: bool
- `get_staged_changes()`: list[str] (relative paths)
- `get_unstaged_changes()`: dict[str, list[str]] with keys "modified", "untracked"
- `get_full_status()`: dict[str, list[str]] with keys "staged", "modified", "untracked"
- `is_working_directory_clean()`: bool (raises ValueError if not git repo)

## Implementation Steps

1. **Create `repository.py`**
   - Copy from original `git_operations.py`:
     - `is_git_repository()` function (lines ~117-135)
     - `get_staged_changes()` function (lines ~238-269)
     - `get_unstaged_changes()` function (lines ~272-327)
     - `get_full_status()` function (lines ~330-369)
     - `is_working_directory_clean()` function (lines ~901-921)
   - Add imports from `.core`
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitWorkflows` - Uses all repository functions
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitWorkflows::test_new_project_to_first_commit"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 2 - Create repository.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/repository.py
2. Import from .core: _safe_repo_context, logger
3. Copy these functions from original git_operations.py:
   - is_git_repository() 
   - get_staged_changes()
   - get_unstaged_changes()
   - get_full_status()
   - is_working_directory_clean()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, logger

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package  
- Run sample test: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitWorkflows::test_new_project_to_first_commit -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
