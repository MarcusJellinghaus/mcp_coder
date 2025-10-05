# Step 5: Create Commits Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the commits module containing functions for creating git commits.

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
├── repository.py        # From Step 2
├── file_tracking.py     # From Step 3
├── staging.py           # From Step 4
└── commits.py           # NEW (~150 lines)
```

## WHAT: Functions

```python
def commit_staged_files(message: str, project_dir: Path) -> CommitResult:
    """Create a commit from currently staged files."""

def commit_all_changes(message: str, project_dir: Path) -> CommitResult:
    """Stage all unstaged changes and commit them in one operation."""
```

## HOW: Integration

### Imports
```python
import logging
from pathlib import Path

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import (
    _safe_repo_context,
    CommitResult,
    GIT_SHORT_HASH_LENGTH,
    logger,
)
from .repository import is_git_repository, get_staged_changes
from .staging import stage_all_changes
```

### Dependencies
- Uses `CommitResult` type from core.py
- Uses `is_git_repository()`, `get_staged_changes()` from repository.py
- Uses `stage_all_changes()` from staging.py

## ALGORITHM: Key Logic

### `commit_staged_files(message, project_dir)`
```
1. Validate message not empty/whitespace
2. If not is_git_repository(), return error result
3. Check get_staged_changes() - if empty, return error
4. Use _safe_repo_context() to get repo
5. Execute: commit = repo.index.commit(message.strip())
6. Get short hash: commit.hexsha[:GIT_SHORT_HASH_LENGTH]
7. Return success result with commit_hash
```

### `commit_all_changes(message, project_dir)`
```
1. If not is_git_repository(), return error result
2. Call stage_all_changes(project_dir)
3. If staging failed, return error result
4. Call commit_staged_files(message, project_dir)
5. Return commit result (success or failure)
```

## DATA: Return Values

Both functions return `CommitResult`:
```python
{
    "success": bool,
    "commit_hash": Optional[str],  # 7-char short hash on success
    "error": Optional[str]          # Error message on failure
}
```

Success case:
```python
{"success": True, "commit_hash": "a1b2c3d", "error": None}
```

Failure cases:
```python
{"success": False, "commit_hash": None, "error": "Commit message cannot be empty"}
{"success": False, "commit_hash": None, "error": "No staged files to commit"}
{"success": False, "commit_hash": None, "error": "Git error creating commit: ..."}
```

## Implementation Steps

1. **Create `commits.py`**
   - Copy from original `git_operations.py`:
     - `commit_staged_files()` function (lines ~487-548)
     - `commit_all_changes()` function (lines ~551-608)
   - Add imports from `.core`, `.repository`, `.staging`
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_commit_workflows`
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_new_project_to_first_commit`
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitWorkflows::test_commit_workflows"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 5 - Create commits.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/commits.py
2. Import from .core: _safe_repo_context, CommitResult, GIT_SHORT_HASH_LENGTH, logger
3. Import from .repository: is_git_repository, get_staged_changes
4. Import from .staging: stage_all_changes
5. Copy these functions from original git_operations.py:
   - commit_staged_files()
   - commit_all_changes()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, CommitResult, GIT_SHORT_HASH_LENGTH, logger
- from .repository import is_git_repository, get_staged_changes
- from .staging import stage_all_changes

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Run test: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitWorkflows::test_commit_workflows -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
