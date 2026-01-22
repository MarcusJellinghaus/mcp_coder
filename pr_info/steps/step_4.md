# Step 4: Reorganize Test Files

## LLM Prompt
```
You are implementing Step 4 of Issue #317: Refactor git_operations layered architecture.
See pr_info/steps/summary.md for full context.

This step reorganizes test files to match the new module structure.
```

## Overview
Reorganize test files to mirror the new source structure:
1. Create `test_readers.py` with tests for reader functions
2. Update `test_branches.py` to keep only mutation function tests
3. Update `test_remotes.py` to include `rebase_onto_branch` tests
4. Delete `test_repository.py`

---

## Part A: Create test_readers.py

### WHERE
`tests/utils/git_operations/test_readers.py`

### WHAT
New test file for all reader functions.

### HOW
1. Copy `TestRepositoryOperations` class from `test_repository.py`
2. Copy `TestValidateBranchName` class from `test_branches.py`
3. Copy `TestExtractIssueNumberFromBranch` class from `test_branches.py`
4. Copy `TestRemoteBranchExists` class from `test_branches.py`
5. Copy tests for `branch_exists`, `get_current_branch_name`, `get_default_branch_name`, `get_parent_branch_name`

### File Structure
```python
"""Tests for git repository reader operations."""

from pathlib import Path

import pytest
from git import Repo

from mcp_coder.utils.git_operations import (
    branch_exists,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
    get_full_status,
    get_parent_branch_name,
    get_staged_changes,
    get_unstaged_changes,
    is_git_repository,
    is_working_directory_clean,
    remote_branch_exists,
    validate_branch_name,
)


@pytest.mark.git_integration
class TestRepositoryReaders:
    """Tests for repository status reader functions."""
    # ... tests from test_repository.py ...


class TestBranchValidation:
    """Tests for branch name validation."""
    # ... tests from test_branches.py TestValidateBranchName ...


class TestBranchNameExtraction:
    """Tests for extracting issue numbers from branch names."""
    # ... tests from test_branches.py TestExtractIssueNumberFromBranch ...


@pytest.mark.git_integration
class TestBranchExistence:
    """Tests for branch existence checks."""
    # ... tests for branch_exists, remote_branch_exists ...


@pytest.mark.git_integration
class TestBranchNameReaders:
    """Tests for branch name reader functions."""
    # ... tests for get_current_branch_name, get_default_branch_name, get_parent_branch_name ...
```

---

## Part B: Update test_branches.py

### WHERE
`tests/utils/git_operations/test_branches.py`

### WHAT
Remove tests for functions that moved to `readers.py` and `remotes.py`.

### HOW
1. Remove `TestValidateBranchName` class
2. Remove `TestExtractIssueNumberFromBranch` class
3. Remove `TestRemoteBranchExists` class
4. Remove `TestRebaseOntoBranch` class
5. Keep only tests for mutation functions: `create_branch`, `checkout_branch`, `delete_branch`

---

## Part C: Update test_remotes.py

### WHERE
`tests/utils/git_operations/test_remotes.py`

### WHAT
Add tests for `rebase_onto_branch`.

### HOW
1. Add import for `rebase_onto_branch`
2. Copy `TestRebaseOntoBranch` class from `test_branches.py`

---

## Part D: Delete test_repository.py

### WHERE
`tests/utils/git_operations/test_repository.py`

### WHAT
Delete the file - all tests moved to `test_readers.py`.

### HOW
```bash
rm tests/utils/git_operations/test_repository.py
```

---

## Verification

```bash
# Run all git_operations tests
pytest tests/utils/git_operations/ -v

# Verify test count is unchanged
pytest tests/utils/git_operations/ --collect-only | grep "test session starts" -A 5
```

---

## Notes

- Tests use package-level imports - no changes needed to import statements
- Test logic remains unchanged - only file locations change
- Total test count should remain the same before and after
