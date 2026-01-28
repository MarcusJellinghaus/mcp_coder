# Step 2: Fix Git Operations Internal Layering

## LLM Prompt

```
Read pr_info/steps/summary.md for context. Implement Step 2: Move needs_rebase from branches.py to workflows.py.

This step fixes the same-layer import violation within git_operations by moving the orchestration function to the workflows layer.
```

## WHERE: File Paths

### Files to Modify
- `src/mcp_coder/utils/git_operations/branches.py` (remove needs_rebase)
- `src/mcp_coder/utils/git_operations/workflows.py` (add needs_rebase)
- `src/mcp_coder/utils/git_operations/__init__.py` (update exports)
- `src/mcp_coder/workflow_utils/branch_status.py` (update import)
- `tests/utils/git_operations/test_branches.py` (move needs_rebase tests if any)

## WHAT: Main Functions

### Function to Move: `needs_rebase`

```python
def needs_rebase(
    project_dir: Path, target_branch: Optional[str] = None
) -> Tuple[bool, str]:
    """Detect if current branch needs rebasing onto target branch.

    Args:
        project_dir: Path to git repository
        target_branch: Branch to check against (defaults to auto-detect)

    Returns:
        (needs_rebase, reason) where:
        - needs_rebase: True if rebase is needed, False otherwise
        - reason: Description of status ("up-to-date", "3 commits behind", "error: <reason>")
    """
```

## HOW: Integration Points

### Current Dependencies (in branches.py)
```python
from .core import _safe_repo_context, logger
from .readers import (
    get_current_branch_name,
    get_default_branch_name,
    is_git_repository,
)
from .remotes import fetch_remote  # THIS CAUSES THE VIOLATION
```

### New Dependencies (in workflows.py)
```python
from .core import _safe_repo_context
from .readers import (
    get_current_branch_name,
    get_default_branch_name,
    is_git_repository,
)
from .remotes import fetch_remote  # ALLOWED: workflows can import from any layer
```

## ALGORITHM: Core Logic

```
1. Check if project_dir is a git repository
2. Fetch from remote to get latest refs
3. Get current branch name
4. Determine target branch (param or default)
5. Count commits between HEAD and origin/target
6. Return (True, "N commits behind") or (False, "up-to-date")
```

## DATA: Return Values

No changes to return type:
```python
Tuple[bool, str]  # (needs_rebase, reason)
```

## Changes Required

### 1. Remove from `branches.py`

Remove:
- The `from .remotes import fetch_remote` import
- The entire `needs_rebase` function (~80 lines)

### 2. Add to `workflows.py`

Add imports:
```python
from typing import Optional, Tuple
from git.exc import GitCommandError, InvalidGitRepositoryError
from .readers import get_current_branch_name, get_default_branch_name
from .remotes import fetch_remote
```

Add the `needs_rebase` function (copy from branches.py).

### 3. Update `__init__.py`

The export should already work since `__init__.py` likely imports from multiple submodules. Verify `needs_rebase` is exported.

### 4. Update `branch_status.py`

After Step 1, the import in `branch_status.py` should be:
```python
from mcp_coder.utils.git_operations import needs_rebase
```
This will work regardless of which submodule exports it.

### 5. Move Tests (if any)

Check `tests/utils/git_operations/test_branches.py` for `needs_rebase` tests and move them to `test_workflows.py`.

## Success Criteria

- [ ] `needs_rebase` removed from `branches.py`
- [ ] `needs_rebase` added to `workflows.py`
- [ ] No import of `remotes` in `branches.py`
- [ ] `import-linter` passes for git_operations_internal_layering contract
- [ ] All tests pass
