# Step 2: Remove `get_parent_branch_name()` and Update Exports

## LLM Prompt
```
Implement Step 2 of Issue #388: Remove get_parent_branch_name() function.

Reference: pr_info/steps/summary.md for full context.

This step removes the deprecated function and all its re-exports from 
the codebase. The function always returned main/master which caused 
the bug this issue fixes.
```

## Overview

Remove `get_parent_branch_name()` from `readers.py` and remove all re-exports from `__init__.py` files.

---

## WHERE: Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/utils/git_operations/readers.py` | Remove function |
| `src/mcp_coder/utils/git_operations/__init__.py` | Remove re-export |
| `src/mcp_coder/utils/__init__.py` | Remove re-export |
| `tests/utils/git_operations/test_readers.py` | Remove tests |

---

## WHAT: Code to Remove

### From `readers.py`
Remove the entire function (approximately lines 270-295):
```python
# DELETE THIS ENTIRE FUNCTION
def get_parent_branch_name(project_dir: Path) -> Optional[str]:
    """
    Get the name of the parent branch (main or master).
    ...
    """
    logger.debug("Getting parent branch name for %s", project_dir)
    main_branch = get_default_branch_name(project_dir)
    if main_branch:
        logger.debug("Parent branch identified as: %s", main_branch)
    else:
        logger.debug("No main branch found, cannot determine parent branch")
    return main_branch
```

### From `git_operations/__init__.py`
Remove from imports:
```python
# REMOVE this line from the import block
from .readers import (
    ...
    get_parent_branch_name,  # DELETE
    ...
)
```

Remove from `__all__`:
```python
__all__ = [
    ...
    "get_parent_branch_name",  # DELETE
    ...
]
```

### From `utils/__init__.py`
Remove from imports:
```python
# REMOVE this line from the import block
from .git_operations import (
    ...
    get_parent_branch_name,  # DELETE
    ...
)
```

Remove from `__all__`:
```python
__all__ = [
    ...
    "get_parent_branch_name",  # DELETE
    ...
]
```

---

## HOW: Verification Steps

After removal, verify no remaining references:
```bash
# Should return no results (except test file being deleted)
grep -r "get_parent_branch_name" src/
grep -r "get_parent_branch_name" tests/
```

---

## TEST: Remove Test Class

### From `tests/utils/git_operations/test_readers.py`

Remove this test:
```python
# DELETE THIS TEST
def test_get_parent_branch_name(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test get_parent_branch_name returns parent branch."""
    repo, project_dir = git_repo_with_commit

    # Get initial branch name
    initial_branch = get_current_branch_name(project_dir)

    # Create feature branch
    repo.git.checkout("-b", "feature-branch")

    # Parent should be the initial branch
    parent = get_parent_branch_name(project_dir)
    assert parent == initial_branch
```

Also remove the import:
```python
# REMOVE from imports
from mcp_coder.utils.git_operations import (
    ...
    get_parent_branch_name,  # DELETE
    ...
)
```

---

## DATA: N/A

No data structures changed in this step.

---

## ACCEPTANCE CRITERIA

- [ ] `get_parent_branch_name()` removed from `readers.py`
- [ ] Re-export removed from `git_operations/__init__.py`
- [ ] Re-export removed from `utils/__init__.py`
- [ ] Test removed from `test_readers.py`
- [ ] `grep -r "get_parent_branch_name" src/` returns no results
- [ ] All existing tests still pass (no broken imports)
