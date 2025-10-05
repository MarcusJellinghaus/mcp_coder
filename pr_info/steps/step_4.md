# Step 4: Create Staging Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the staging module containing functions for staging files for commit.

## WHERE: File Structure
```
src/mcp_coder/utils/git_operations/
├── __init__.py
├── core.py              # From Step 1
├── repository.py        # From Step 2
├── file_tracking.py     # From Step 3
└── staging.py           # NEW (~120 lines)
```

## WHAT: Functions

```python
def stage_specific_files(files: list[Path], project_dir: Path) -> bool:
    """Stage specific files for commit."""

def stage_all_changes(project_dir: Path) -> bool:
    """Stage all unstaged changes (both modified and untracked files) for commit."""
```

## HOW: Integration

### Imports
```python
import logging
from pathlib import Path

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, _normalize_git_path, logger
from .repository import is_git_repository, get_unstaged_changes
```

### Used By (Future Steps)
- `commits.py`: Uses `stage_all_changes()` in `commit_all_changes()`

## ALGORITHM: Key Logic

### `stage_specific_files(files, project_dir)`
```
1. If not is_git_repository(project_dir), return False
2. If files list empty, return True (no-op success)
3. For each file: validate exists and normalize path
4. If any file invalid (not exists, outside project), return False
5. Use _safe_repo_context() to get repo
6. Execute: repo.index.add(relative_paths)
7. Return True on success, False on GitCommandError
```

### `stage_all_changes(project_dir)`
```
1. If not is_git_repository(project_dir), return False
2. Call get_unstaged_changes(project_dir)
3. Combine modified + untracked into all_unstaged_files
4. If no unstaged changes, return True (no-op success)
5. Use _safe_repo_context() to get repo
6. Execute: repo.git.add("--all")
7. Return True on success, False on GitCommandError
```

## DATA: Return Values

- `stage_specific_files()`: bool
- `stage_all_changes()`: bool

Both return:
- True: Staging succeeded (or no-op case)
- False: Staging failed or invalid repository

## Implementation Steps

1. **Create `staging.py`**
   - Copy from original `git_operations.py`:
     - `stage_specific_files()` function (lines ~372-429)
     - `stage_all_changes()` function (lines ~432-484)
   - Add imports from `.core` and `.repository`
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_staging_specific_files_workflow`
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_staging_all_changes_workflow`
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitWorkflows::test_staging_all_changes_workflow"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 4 - Create staging.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/staging.py
2. Import from .core: _safe_repo_context, _normalize_git_path, logger
3. Import from .repository: is_git_repository, get_unstaged_changes
4. Copy these functions from original git_operations.py:
   - stage_specific_files()
   - stage_all_changes()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, _normalize_git_path, logger
- from .repository import is_git_repository, get_unstaged_changes

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Run test: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitWorkflows::test_staging_all_changes_workflow -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
