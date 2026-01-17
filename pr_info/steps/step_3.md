# Step 3: Remove BASE_BRANCH File Support and Standardize Logging

## Overview

Remove the `BASE_BRANCH` file detection from parent branch logic and standardize branch name formatting in log messages. This simplifies the detection logic to: GitHub PR base branch → default branch fallback.

## LLM Prompt

```
Implement Step 3 of the auto-rebase feature as described in pr_info/steps/summary.md.

1. Remove BASE_BRANCH file support from _get_rebase_target_branch() function
2. Update related tests to remove BASE_BRANCH file test cases
3. Standardize branch name formatting in log messages (no quotes)
Follow TDD: update tests first, then modify implementation.
```

---

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/workflows/implement/test_core.py` | REMOVE test cases for BASE_BRANCH file functionality |
| `src/mcp_coder/workflows/implement/core.py` | MODIFY `_get_rebase_target_branch()` to remove BASE_BRANCH file logic |
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY log messages to use consistent formatting |

---

## WHAT: Function Changes

### Modified: `_get_rebase_target_branch()` in core.py

```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.
    
    Detection priority:
    1. GitHub PR base branch (if open PR exists for current branch)
    2. Default branch (main/master) via get_default_branch_name()
    
    Args:
        project_dir: Path to the project directory
    
    Returns:
        Branch name to rebase onto, or None if detection fails
    
    Note:
        All errors are handled gracefully - returns None on any failure.
        Debug logging indicates which detection method was used.
    """
```

### Modified: Log messages in branches.py

**Current inconsistent formatting:**
```python
logger.info(f"Successfully rebased onto origin/{target_branch}")
logger.info(f"Already up-to-date with origin/{target_branch}")
```

**Standardized formatting (no quotes around branch names):**
```python
logger.info(f"Successfully rebased onto origin/{target_branch}")
logger.info(f"Already up-to-date with origin/{target_branch}")
```

---

## ALGORITHM: Simplified Detection Logic

```python
def _get_rebase_target_branch(project_dir):
    # 1. Get current branch name
    current_branch = get_current_branch_name(project_dir)
    if not current_branch:
        return None
    
    # 2. Try GitHub PR lookup
    try:
        pr_manager = PullRequestManager(project_dir)
        open_prs = pr_manager.list_pull_requests(state="open")
        for pr in open_prs:
            if pr["head_branch"] == current_branch:
                logger.debug("Parent branch detected from: GitHub PR")
                return pr["base_branch"]
    except Exception:
        pass  # Continue to next method
    
    # 3. Fall back to default branch (removed BASE_BRANCH file step)
    default = get_default_branch_name(project_dir)
    if default:
        logger.debug("Parent branch detected from: default branch")
    return default
```

---

## TEST CASES TO REMOVE

### From TestGetRebaseTargetBranch class:

```python
# REMOVE these test methods:
def test_returns_base_branch_file_content(...)
def test_pr_takes_priority_over_file(...)

# KEEP these test methods (unchanged):
def test_returns_pr_base_branch(...)
def test_returns_default_branch_as_fallback(...)
def test_returns_none_when_no_current_branch(...)
```

---

## IMPLEMENTATION NOTES

1. **Simplified Logic**: Remove entire BASE_BRANCH file handling block (steps 3-4 in original algorithm)

2. **Test Cleanup**: Remove any test setup that creates `pr_info/BASE_BRANCH` files

3. **Logging Standardization**: Review all log messages in `rebase_onto_branch()` and ensure branch names are formatted consistently without quotes

4. **Documentation Impact**: Update step documentation to reflect the simplified detection priority

---

## DATA: Updated Detection Sources

| Priority | Source | Example |
|----------|--------|---------|
| 1 | GitHub PR base_branch | PR targeting `develop` → returns `develop` |
| 2 | Default branch | No PR found → returns `main` or `master` |

**Removed**: `pr_info/BASE_BRANCH` file source

---

## VERIFICATION

After implementation:
1. All tests should pass with BASE_BRANCH file logic removed
2. Log messages should use consistent formatting
3. Detection logic should work correctly with just PR → default fallback
4. No references to BASE_BRANCH file should remain in code or tests