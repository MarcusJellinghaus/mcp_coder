# Step 3: Update `diffs.py` - Remove Auto-Detection

## LLM Prompt
```
Implement Step 3 of Issue #388: Update diffs.py to remove auto-detection.

Reference: pr_info/steps/summary.md for full context.

This step removes the auto-detection logic from get_branch_diff() to avoid
cross-layer dependencies. Callers must now explicitly provide base_branch
or handle the None case.
```

## Overview

Remove the `get_parent_branch_name` import and auto-detection from `get_branch_diff()`. When `base_branch` is `None`, log an error and return empty string.

---

## WHERE: Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/utils/git_operations/diffs.py` | Remove auto-detection |
| `tests/utils/git_operations/test_diffs.py` | Update tests |

---

## WHAT: Changes to `diffs.py`

### Remove Import
```python
# BEFORE
from .readers import (
    branch_exists,
    get_current_branch_name,
    get_parent_branch_name,  # DELETE THIS
    is_git_repository,
    remote_branch_exists,
)

# AFTER
from .readers import (
    branch_exists,
    get_current_branch_name,
    is_git_repository,
    remote_branch_exists,
)
```

### Update `get_branch_diff()` Function

```python
def get_branch_diff(
    project_dir: Path,
    base_branch: Optional[str] = None,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Generate git diff between current branch and base branch.

    Args:
        project_dir: Path to the project directory containing git repository
        base_branch: Base branch to compare against. If None, returns empty 
            string with error log. Callers should use detect_base_branch() 
            to determine the base branch before calling this function.
        exclude_paths: List of paths to exclude from diff

    Returns:
        Git diff string, or empty string if base_branch is None or on error
        
    Note:
        - Uses three-dot notation (base...HEAD) to show changes on current branch
        - If base_branch doesn't exist locally but exists on origin,
          falls back to using origin/{base_branch} for comparison.
    """
```

### Replace Auto-Detection Logic

```python
# BEFORE (lines ~78-83)
# Auto-detect base branch if not provided
if base_branch is None:
    base_branch = get_parent_branch_name(project_dir)
    if base_branch is None:
        logger.error("Could not determine base branch for diff")
        return ""
    logger.debug("Auto-detected base branch: %s", base_branch)

# AFTER
# Require explicit base branch - no auto-detection
if base_branch is None:
    logger.error(
        "base_branch is required. Use detect_base_branch() from "
        "workflow_utils.base_branch to determine the base branch."
    )
    return ""
```

---

## HOW: Why This Change

**Rationale:** Avoiding cross-layer dependency

The alternative was to import `detect_base_branch` from `workflow_utils`:
```python
# This would create: utils.git_operations → workflow_utils dependency
from mcp_coder.workflow_utils.base_branch import detect_base_branch
```

This violates the architecture where `utils` is a lower-level layer than `workflow_utils`. The KISS solution is to remove auto-detection entirely and require callers to be explicit.

**Callers must now:**
1. Call `detect_base_branch()` to get the base branch
2. Handle `None` return from `detect_base_branch()`
3. Pass explicit `base_branch` to `get_branch_diff()`

---

## ALGORITHM: N/A

No algorithm changes - just removal of auto-detection logic.

---

## DATA: N/A

No data structure changes.

---

## TEST: Update Test Cases

### File: `tests/utils/git_operations/test_diffs.py`

#### Remove/Update Auto-Detection Tests

If there are tests that rely on auto-detection, update them:

```python
# BEFORE - test that relied on auto-detection
def test_get_branch_diff_auto_detects_base(self, ...):
    result = get_branch_diff(project_dir)  # No base_branch
    assert result != ""

# AFTER - test explicit base_branch requirement
def test_get_branch_diff_returns_empty_when_no_base_branch(self, ...):
    """get_branch_diff returns empty string when base_branch is None."""
    result = get_branch_diff(project_dir, base_branch=None)
    assert result == ""
```

#### Add New Test for Error Case

```python
def test_get_branch_diff_logs_error_when_no_base_branch(
    self, git_repo_with_commit: tuple[Repo, Path], caplog
) -> None:
    """get_branch_diff logs error when base_branch is None."""
    _, project_dir = git_repo_with_commit
    
    with caplog.at_level(logging.ERROR):
        result = get_branch_diff(project_dir, base_branch=None)
    
    assert result == ""
    assert "base_branch is required" in caplog.text
```

---

## ACCEPTANCE CRITERIA

- [ ] `get_parent_branch_name` import removed from `diffs.py`
- [ ] Auto-detection logic removed from `get_branch_diff()`
- [ ] Returns empty string with error log when `base_branch` is `None`
- [ ] Docstring updated to document new behavior
- [ ] Tests updated to reflect explicit base_branch requirement
- [ ] No cross-layer imports introduced
