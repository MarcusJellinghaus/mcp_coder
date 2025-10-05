# Step 3: Create File Tracking Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the file tracking module containing functions for checking file tracking status and moving files within git.

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
├── repository.py        # From Step 2
└── file_tracking.py     # NEW (~80 lines)
```

## WHAT: Functions

```python
def is_file_tracked(file_path: Path, project_dir: Path) -> bool:
    """Check if a file is tracked by git."""

def git_move(source_path: Path, dest_path: Path, project_dir: Path) -> bool:
    """Move a file using git mv command."""
```

## HOW: Integration

### Imports
```python
import logging
from pathlib import Path

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, _normalize_git_path, logger
from .repository import is_git_repository
```

### Dependencies
- Uses `is_git_repository()` from repository.py
- Uses `_safe_repo_context()`, `_normalize_git_path()` from core.py

## ALGORITHM: Key Logic

### `is_file_tracked(file_path, project_dir)`
```
1. If not is_git_repository(project_dir), return False
2. Try to normalize file_path relative to project_dir
3. If ValueError (outside project), return False
4. Use _safe_repo_context() to get repo
5. Execute: repo.git.ls_files(git_path)
6. Return True if git_path in result, else False
```

### `git_move(source_path, dest_path, project_dir)`
```
1. If not is_git_repository(project_dir), return False
2. Normalize both paths using _normalize_git_path()
3. If ValueError (outside project), log error and return False
4. Use _safe_repo_context() to get repo
5. Execute: repo.git.mv(source_git, dest_git)
6. Return True on success, raise GitCommandError on failure
```

## DATA: Return Values

- `is_file_tracked()`: bool
- `git_move()`: bool (raises GitCommandError on git mv failure)

## Implementation Steps

1. **Create `file_tracking.py`**
   - Copy from original `git_operations.py`:
     - `is_file_tracked()` function (lines ~138-178)
     - `git_move()` function (lines ~181-221)
   - Add imports from `.core` and `.repository`
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- Tests use these functions indirectly through higher-level operations
- No direct unit tests for these functions
- Integration tests will validate in final step

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 3 - Create file_tracking.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/file_tracking.py
2. Import from .core: _safe_repo_context, _normalize_git_path, logger
3. Import from .repository: is_git_repository
4. Copy these functions from original git_operations.py:
   - is_file_tracked()
   - git_move()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, _normalize_git_path, logger
- from .repository import is_git_repository

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Confirm ~80 lines total

CRITICAL: Exact code copy - no modifications. Update imports only.
```
