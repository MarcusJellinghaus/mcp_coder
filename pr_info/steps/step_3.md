# Step 3: Extract `extract_issue_number_from_branch()` Utility Function

## LLM Prompt

```
Implement Step 3 of Issue #203: Extract shared utility function for issue number extraction.

Read pr_info/steps/summary.md for context and pr_info/steps/decisions.md for review decisions.
Follow TDD: write tests first, then implement functionality.
```

## Overview

Extract the duplicated regex logic for extracting issue numbers from branch names into a shared utility function in `git_operations/branches.py`. Then refactor both `issue_manager.py` and `core.py` to use this shared function.

## WHERE: Files to Modify

1. `tests/utils/git_operations/test_branches.py` - Add new tests
2. `src/mcp_coder/utils/git_operations/branches.py` - Add new function
3. `src/mcp_coder/utils/git_operations/__init__.py` - Export new function
4. `src/mcp_coder/utils/__init__.py` - Export new function (if needed)
5. `src/mcp_coder/utils/github_operations/issue_manager.py` - Refactor to use shared function
6. `src/mcp_coder/workflows/create_pr/core.py` - Refactor to use shared function

## WHAT: New Function Signature

```python
def extract_issue_number_from_branch(branch_name: str) -> Optional[int]:
    """Extract issue number from branch name pattern '{issue_number}-title'.
    
    Args:
        branch_name: Branch name to extract issue number from
        
    Returns:
        Issue number as integer if found, None otherwise
        
    Example:
        >>> extract_issue_number_from_branch("123-feature-name")
        123
        >>> extract_issue_number_from_branch("feature-branch")
        None
    """
```

## HOW: Integration Points

### New Import in `branches.py`
```python
import re  # Add if not already present
```

### Export in `git_operations/__init__.py`
```python
from .branches import extract_issue_number_from_branch
```

### Import in `issue_manager.py`
```python
from mcp_coder.utils.git_operations.branches import (
    get_current_branch_name,
    extract_issue_number_from_branch,  # NEW
)
```

### Import in `core.py`
```python
from mcp_coder.utils.git_operations.branches import extract_issue_number_from_branch
```

## ALGORITHM: Core Logic

```python
def extract_issue_number_from_branch(branch_name: str) -> Optional[int]:
    if not branch_name:
        return None
    match = re.match(r"^(\d+)-", branch_name)
    if match:
        return int(match.group(1))
    return None
```

## DATA: Return Values

- `int`: Issue number extracted from branch name (e.g., `123`)
- `None`: If branch name doesn't match pattern or is empty

## Tests to Add

### Test 1: `test_extract_issue_number_from_branch_valid`

```python
def test_extract_issue_number_from_branch_valid() -> None:
    """Tests extraction from valid branch names."""
    assert extract_issue_number_from_branch("123-feature-name") == 123
    assert extract_issue_number_from_branch("1-fix") == 1
    assert extract_issue_number_from_branch("999-long-branch-name-here") == 999
```

### Test 2: `test_extract_issue_number_from_branch_invalid`

```python
def test_extract_issue_number_from_branch_invalid() -> None:
    """Tests extraction from invalid branch names returns None."""
    assert extract_issue_number_from_branch("feature-branch") is None
    assert extract_issue_number_from_branch("main") is None
    assert extract_issue_number_from_branch("feature-123-name") is None  # Number not at start
```

### Test 3: `test_extract_issue_number_from_branch_edge_cases`

```python
def test_extract_issue_number_from_branch_edge_cases() -> None:
    """Tests edge cases for issue number extraction."""
    assert extract_issue_number_from_branch("") is None
    assert extract_issue_number_from_branch("123") is None  # No hyphen after number
    assert extract_issue_number_from_branch("-feature") is None  # No number before hyphen
```

## Refactoring Details

### In `issue_manager.py` (update_workflow_label method)

**Before:**
```python
# Step 2: Extract issue number from branch name using regex
match = re.match(r"^(\d+)-", actual_branch_name)
if not match:
    logger.warning(
        f"Branch '{actual_branch_name}' does not follow {{issue_number}}-title pattern"
    )
    return False

issue_number = int(match.group(1))
```

**After:**
```python
# Step 2: Extract issue number from branch name
issue_number = extract_issue_number_from_branch(actual_branch_name)
if issue_number is None:
    logger.warning(
        f"Branch '{actual_branch_name}' does not follow {{issue_number}}-title pattern"
    )
    return False
```

### In `core.py` (validate_branch_issue_linkage function)

**Before:**
```python
# 2. Extract issue number from branch name using regex
match = re.match(r"^(\d+)-", branch_name)
if not match:
    logger.warning(
        f"Branch name '{branch_name}' does not start with issue number"
    )
    return None
issue_number = int(match.group(1))
```

**After:**
```python
# 2. Extract issue number from branch name
issue_number = extract_issue_number_from_branch(branch_name)
if issue_number is None:
    logger.warning(
        f"Branch name '{branch_name}' does not start with issue number"
    )
    return None
```

### Cleanup: Remove unused `re` import from `core.py`

After refactoring, check if `re` module is still used in `core.py`. If not, remove the import.

## Verification

After implementation:
1. Run new tests: `pytest tests/utils/git_operations/test_branches.py -v -k "extract_issue"`
2. Run existing branch tests: `pytest tests/utils/git_operations/test_branches.py -v`
3. Run issue manager tests: `pytest tests/utils/github_operations/test_issue_manager_label_update.py -v`
4. Run workflow tests: `pytest tests/workflows/create_pr/test_workflow.py -v`
5. Verify no regressions with full test suite
