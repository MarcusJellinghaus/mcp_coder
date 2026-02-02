# Step 5: Update `implement/core.py` for `None` Handling

## LLM Prompt
```
Implement Step 5 of Issue #388: Update implement/core.py for None handling.

Reference: pr_info/steps/summary.md for full context.

This step updates the rebase target detection in implement/core.py to handle 
the new None return value from detect_base_branch() (was checking for "unknown").
```

## Overview

Update `_get_rebase_target_branch()` in `implement/core.py` to handle the new `None` return value from `detect_base_branch()` instead of checking for `"unknown"`.

---

## WHERE: Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/implement/core.py` | Update `None` check |
| `tests/workflows/implement/test_core.py` | Update tests if needed |

---

## WHAT: Changes to `implement/core.py`

### Current Code (around line 570-580)

```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.

    Uses shared detect_base_branch() function for detection.

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails
    """
    result = detect_base_branch(project_dir)
    return None if result == "unknown" else result  # CHECK FOR "unknown"
```

### Updated Code

```python
def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.

    Uses shared detect_base_branch() function for detection.

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails
    """
    return detect_base_branch(project_dir)  # Now returns None directly on failure
```

---

## HOW: Simplification

The code becomes simpler because:
- **Before:** `detect_base_branch()` returned `"unknown"` on failure, required conversion to `None`
- **After:** `detect_base_branch()` returns `None` directly, no conversion needed

The function `_get_rebase_target_branch()` now just passes through the result.

---

## ALGORITHM: N/A

No algorithm changes - just removing the `"unknown"` → `None` conversion.

---

## DATA: N/A

No data structure changes.

---

## TEST: Verify Existing Tests

### File: `tests/workflows/implement/test_core.py`

Check if there are tests for `_get_rebase_target_branch()` that mock `detect_base_branch()` to return `"unknown"`. If so, update them:

```python
# BEFORE (if exists)
@patch("mcp_coder.workflows.implement.core.detect_base_branch")
def test_rebase_target_returns_none_for_unknown(self, mock_detect):
    mock_detect.return_value = "unknown"
    result = _get_rebase_target_branch(Path("/test"))
    assert result is None

# AFTER
@patch("mcp_coder.workflows.implement.core.detect_base_branch")
def test_rebase_target_returns_none_when_detection_fails(self, mock_detect):
    mock_detect.return_value = None
    result = _get_rebase_target_branch(Path("/test"))
    assert result is None
```

### Verify `_attempt_rebase_and_push()` Still Works

The calling function `_attempt_rebase_and_push()` already handles `None`:

```python
def _attempt_rebase_and_push(project_dir: Path) -> bool:
    target = _get_rebase_target_branch(project_dir)
    if target:  # Already handles None correctly
        logger.info("Rebasing onto origin/%s...", target)
        ...
    else:
        logger.debug("Could not detect parent branch for rebase")
        return False
```

No changes needed to `_attempt_rebase_and_push()`.

---

## ACCEPTANCE CRITERIA

- [ ] `_get_rebase_target_branch()` no longer checks for `"unknown"`
- [ ] Function simply returns `detect_base_branch()` result directly
- [ ] Any tests mocking `"unknown"` return updated to mock `None`
- [ ] Rebase workflow still works correctly with `None` handling
- [ ] All implement workflow tests pass
