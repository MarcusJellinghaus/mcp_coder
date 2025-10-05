# Step 7: Create Diff Module

**Reference**: See `pr_info/steps/summary.md` for complete refactoring overview.

## Objective
Create the diff module containing functions for generating git diffs.

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
└── diff.py              # NEW (~200 lines)
```

## WHAT: Functions

```python
def get_git_diff_for_commit(project_dir: Path) -> Optional[str]:
    """Generate comprehensive git diff without modifying repository state."""

def get_branch_diff(
    project_dir: Path,
    base_branch: Optional[str] = None,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Generate git diff between current branch and base branch."""

# Internal helpers
def _generate_untracked_diff(repo: Repo, project_dir: Path) -> str:
    """Generate diff for untracked files by creating synthetic diff output."""

def _format_diff_sections(
    staged_diff: str, unstaged_diff: str, untracked_diff: str
) -> str:
    """Format diff sections with appropriate headers."""
```

## HOW: Integration

### Imports
```python
import logging
import os
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, PLACEHOLDER_HASH, logger
from .repository import is_git_repository
from .branches import get_current_branch_name, get_parent_branch_name, branch_exists
```

### Dependencies
- Uses `PLACEHOLDER_HASH` from core.py
- Uses `is_git_repository()` from repository.py
- Uses branch functions from branches.py

## ALGORITHM: Key Logic

### `get_git_diff_for_commit(project_dir)`
```
1. If not is_git_repository(), return None
2. Use _safe_repo_context() to get repo
3. Check if repo has commits (handle empty repo)
4. Get staged diff: repo.git.diff("--cached", "--unified=5", "--no-prefix")
5. Get unstaged diff: repo.git.diff("--unified=5", "--no-prefix")
6. Call _generate_untracked_diff(repo, project_dir)
7. Call _format_diff_sections() to combine all diffs
8. Return formatted diff or empty string
```

### `_generate_untracked_diff(repo, project_dir)`
```
1. Get untracked files: repo.untracked_files
2. For each untracked file:
   a. Read file content (handle binary files)
   b. Create synthetic git-style diff header
   c. Add content with + prefix for additions
3. Join all untracked file diffs
4. Return combined untracked diff string
```

### `_format_diff_sections(staged, unstaged, untracked)`
```
1. Create empty sections list
2. If staged diff not empty, add "=== STAGED CHANGES ===" section
3. If unstaged diff not empty, add "=== UNSTAGED CHANGES ===" section
4. If untracked diff not empty, add "=== UNTRACKED FILES ===" section
5. Join sections with double newlines
6. Return formatted string
```

### `get_branch_diff(project_dir, base_branch, exclude_paths)`
```
1. If not is_git_repository(), return ""
2. Auto-detect base_branch if None (use get_parent_branch_name)
3. Get current_branch using get_current_branch_name()
4. If current == base, return ""
5. Verify base_branch exists using branch_exists()
6. Build git diff command args (base...HEAD with excludes)
7. Set UTF-8 encoding environment variables
8. Execute: repo.git.diff(*diff_args)
9. Restore original environment
10. Return diff output
```

## DATA: Return Values

- `get_git_diff_for_commit()`: Optional[str]
  - Returns diff string with sections for staged/unstaged/untracked
  - Returns empty string if no changes
  - Returns None on error (invalid repo, git command failure)

- `get_branch_diff()`: str
  - Returns diff between base branch and current HEAD
  - Returns empty string on error or if current == base
  - Excludes specified paths if provided

- `_generate_untracked_diff()`: str (internal)
- `_format_diff_sections()`: str (internal)

## Implementation Steps

1. **Create `diff.py`**
   - Copy from original `git_operations.py`:
     - `_generate_untracked_diff()` (lines ~611-663)
     - `get_git_diff_for_commit()` (lines ~666-740)
     - `_format_diff_sections()` (lines ~743-756)
     - `get_branch_diff()` (lines ~1082-1155)
   - Add imports from `.core`, `.repository`, `.branches`
   - Also import `from git import Repo` for type hints
   - Preserve all docstrings and implementation

2. **Validate**
   - Run: `run_pylint_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Run: `run_mypy_check(target_directories=["src/mcp_coder/utils/git_operations"])`
   - Both should pass

## Test Strategy
**Existing tests validate behavior**:
- `tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_for_commit_*`
- `tests/utils/test_git_workflows.py::TestGetBranchDiff`
- Validation: Run `run_pytest_check(markers=["git_integration"], extra_args=["tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_for_commit_basic_functionality"])`

---

## LLM Prompt for Implementation

```
You are refactoring git_operations.py into a modular package. Read pr_info/steps/summary.md first for context.

TASK: Implement Step 7 - Create diff.py module

REQUIREMENTS:
1. Create: src/mcp_coder/utils/git_operations/diff.py
2. Import from .core: _safe_repo_context, PLACEHOLDER_HASH, logger
3. Import from .repository: is_git_repository
4. Import from .branches: get_current_branch_name, get_parent_branch_name, branch_exists
5. Also import: from git import Repo, import os (needed for environment vars)
6. Copy these functions from original git_operations.py:
   - _generate_untracked_diff()
   - get_git_diff_for_commit()
   - _format_diff_sections()
   - get_branch_diff()

COPY from: src/mcp_coder/utils/git_operations.py
Keep exact implementation, only update imports to use:
- from .core import _safe_repo_context, PLACEHOLDER_HASH, logger
- from .repository import is_git_repository
- from .branches import get_current_branch_name, get_parent_branch_name, branch_exists
- from git import Repo
- import os

VALIDATION:
- Run pylint on git_operations package
- Run mypy on git_operations package
- Run test: pytest -m git_integration tests/utils/test_git_workflows.py::TestGitWorkflows::test_get_git_diff_for_commit_basic_functionality -v

CRITICAL: Exact code copy - no modifications. Update imports only.
```
