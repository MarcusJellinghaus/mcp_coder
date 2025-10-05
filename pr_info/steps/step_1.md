# Step 1: Create Core Module (Foundation Layer)

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the foundation module containing core utilities, context managers, and shared infrastructure used by all other git operations modules.

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py          # Empty initially, populated in Step 9
└── core.py              # NEW - Core utilities (~80 lines)
```

## WHAT: Functions & Components

### Imports & Setup
```python
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, TypedDict, Any

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

logger = logging.getLogger(__name__)
```

### Constants
```python
PLACEHOLDER_HASH = "0" * 7
GIT_SHORT_HASH_LENGTH = 7
```

### Type Definitions
```python
class CommitResult(TypedDict):
    """Result of a git commit operation."""
    success: bool
    commit_hash: Optional[str]
    error: Optional[str]

class PushResult(TypedDict):
    """Result of a git push operation."""
    success: bool
    error: Optional[str]
```

### Functions
```python
def _close_repo_safely(repo: Repo) -> None:
    """Safely close a GitPython repository to prevent handle leaks on Windows."""

@contextmanager
def _safe_repo_context(project_dir: Path) -> Iterator[Repo]:
    """Context manager for safely handling GitPython repository objects."""

def _normalize_git_path(path: Path, base_dir: Path) -> str:
    """Convert a path to git-compatible format."""
```

## HOW: Integration

### Imports in Other Modules (Future Steps)
```python
# In repository.py, staging.py, etc.
from .core import (
    _safe_repo_context,
    _normalize_git_path,
    CommitResult,
    PushResult,
    PLACEHOLDER_HASH,
    GIT_SHORT_HASH_LENGTH,
    logger,
)
```

## ALGORITHM: Key Logic

### `_close_repo_safely(repo)`
```
1. Try to terminate any active git command processes
2. If process still running after 0.1s, force kill
3. Close repository object if it has close method
4. Log errors but don't raise (best effort cleanup)
5. Return (cleanup always succeeds)
```

### `_safe_repo_context(project_dir)`
```
1. Initialize repo = None
2. Try: Create Repo object from project_dir
3. Yield repo to caller
4. Finally: Call _close_repo_safely(repo) if repo exists
5. Ensures cleanup even on exceptions
```

### `_normalize_git_path(path, base_dir)`
```
1. Calculate relative_path = path.relative_to(base_dir)
2. Convert to string
3. Replace backslashes with forward slashes
4. Return git-compatible path string
5. Raise ValueError if path not relative to base_dir
```

## DATA: Return Values

- `_close_repo_safely()`: None (side effects only)
- `_safe_repo_context()`: Iterator[Repo] (context manager)
- `_normalize_git_path()`: str (forward-slash path)
- `CommitResult`: TypedDict with success, commit_hash, error keys
- `PushResult`: TypedDict with success, error keys

## Implementation Steps

1. **Create package directory**
   ```bash
   mkdir -p src/mcp_coder/utils/git_operations
   ```

2. **Create empty `__init__.py`**
   ```bash
   touch src/mcp_coder/utils/git_operations/__init__.py
   ```

3. **Create `core.py`**
   - Copy from original `git_operations.py`:
     - All imports and logger setup
     - Constants: `PLACEHOLDER_HASH`, `GIT_SHORT_HASH_LENGTH`
     - Type definitions: `CommitResult`, `PushResult`
     - Functions: `_close_repo_safely()`, `_safe_repo_context()`, `_normalize_git_path()`
   - Preserve all docstrings and comments
   - Preserve exact implementation (no modifications)

4. **Validate**
   - File should be ~80 lines
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass (no imports from other modules yet)

## Test Strategy
**No new tests needed** - these are internal utilities tested indirectly through public API tests in subsequent steps.

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package structure. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 1 - Create core.py module

REQUIREMENTS:
1. Create directory: src/mcp_coder/utils/git_operations/
2. Create empty file: src/mcp_coder/utils/git_operations/__init__.py
3. Create core.py with:
   - All imports and logger setup from original git_operations.py
   - Constants: PLACEHOLDER_HASH, GIT_SHORT_HASH_LENGTH
   - Type definitions: CommitResult, PushResult
   - Functions: _close_repo_safely(), _safe_repo_context(), _normalize_git_path()

COPY from: src/mcp_coder/utils/git_operations.py
- Lines 1-14: imports and logger
- Lines 16-17: constants
- Lines 20-34: type definitions (CommitResult, PushResult)
- Lines 37-70: _close_repo_safely() function
- Lines 73-94: _safe_repo_context() function  
- Lines 97-114: _normalize_git_path() function

VALIDATION:
- Run pylint on new module
- Run mypy on new module
- Confirm ~80 lines total

CRITICAL: Copy exact code - no modifications, no optimizations. Pure refactoring only.
```
