# Step 7: Cleanup - Remove Duplicate `_get_issue_status()`

## LLM Prompt

```
Implement Step 7 of Issue #400 (see pr_info/steps/summary.md for context).

This step removes the duplicate `_get_issue_status()` function from status.py.

Follow TDD: Update any tests first if needed, then remove the duplication.
```

## Overview

Remove the duplicate `_get_issue_status()` function from `status.py` and use `get_issue_status()` from `helpers.py` instead (see Decision #6 and #12).

---

## Part A: Check for Usage

### WHERE
- `src/mcp_coder/workflows/vscodeclaude/status.py`

### WHAT

The function `_get_issue_status()` at lines 186-196 duplicates `get_issue_status()` from `helpers.py`.

**Current usage in status.py:**
```python
def _get_issue_status(issue: IssueData) -> str:
    """Get the status label from an issue."""
    for label in issue["labels"]:
        if label.startswith("status-"):
            return label
    return ""
```

Used in `display_status_table()` for eligible issues display.

---

## Part B: Update Import and Remove Function

### HOW

1. Add import: `from .helpers import get_issue_status`
2. Replace usage of `_get_issue_status(issue)` with `get_issue_status(issue)`
3. Delete the `_get_issue_status()` function

### ALGORITHM

```
1. Search for all usages of _get_issue_status in status.py
2. Replace with get_issue_status from helpers
3. Remove the function definition
4. Verify tests still pass
```

---

## Part C: Verification

After implementation, run:
```bash
pytest tests/workflows/vscodeclaude/test_status.py -v
```

All tests should pass, confirming:
1. No remaining references to `_get_issue_status`
2. `get_issue_status` from helpers works correctly
