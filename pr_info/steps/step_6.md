# Step 6: Add Workflow Tests

## Context
See `pr_info/steps/summary.md` for full architectural context.

This step adds unit tests for the `run_create_pr_workflow()` function to ensure proper error handling and workflow orchestration.

## Objective
Create essential tests for workflow orchestration function with focused coverage of critical paths.

---

## WHERE
**File to create:** `tests/workflows/create_pr/test_workflow.py`

---

## WHAT - Test Coverage

### Test 1: Complete Success Flow
Test the happy path where all steps complete successfully.

### Test 2: Prerequisites Fail
Test early exit when prerequisites check returns False.

### Test 3: PR Creation Fails
Test workflow exits when PR creation fails.

### Test 4: Generate Summary Exception
Test workflow handles exceptions from `generate_pr_summary()`.

---

## HOW - Implementation

### Test Structure
```python
"""Tests for create_pr workflow orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from mcp_coder.workflows.create_pr.core import run_create_pr_workflow


class TestRunCreatePrWorkflow:
    """Test suite for run_create_pr_workflow orchestration."""
```

### Required Mocks
All tests will mock these functions:
- `check_prerequisites`
- `generate_pr_summary`
- `git_push`
- `create_pull_request`
- `cleanup_repository`
- `is_working_directory_clean`
- `commit_all_changes`

---

## Test Implementations

### Test 1: Complete Success
```python
@patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
@patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
@patch("mcp_coder.workflows.create_pr.core.git_push")
@patch("mcp_coder.workflows.create_pr.core.create_pull_request")
@patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
@patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
@patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
@patch("mcp_coder.workflows.create_pr.core.git_push")
def test_workflow_complete_success(self, mock_push2, mock_commit, mock_clean, 
                                   mock_cleanup, mock_create_pr, mock_push1,
                                   mock_generate, mock_prereqs):
    """Test successful workflow with all steps completing."""
    # Setup mocks
    mock_prereqs.return_value = True
    mock_generate.return_value = ("Test Title", "Test Body")
    mock_push1.return_value = {"success": True}
    mock_create_pr.return_value = True
    mock_cleanup.return_value = True
    mock_clean.return_value = False  # Has changes to commit
    mock_commit.return_value = {"success": True, "commit_hash": "abc123"}
    mock_push2.return_value = {"success": True}
    
    # Execute
    result = run_create_pr_workflow(Path("/test"), "claude", "cli")
    
    # Verify
    assert result == 0
    mock_prereqs.assert_called_once()
    mock_generate.assert_called_once_with(Path("/test"), "claude", "cli")
    mock_create_pr.assert_called_once()
```

### Test 2: Prerequisites Fail
```python
@patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
def test_workflow_prerequisites_fail(self, mock_prereqs):
    """Test workflow exits when prerequisites fail."""
    mock_prereqs.return_value = False
    
    result = run_create_pr_workflow(Path("/test"), "claude", "cli")
    
    assert result == 1
    mock_prereqs.assert_called_once_with(Path("/test"))
```

### Test 3: PR Creation Fails
```python
@patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
@patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
@patch("mcp_coder.workflows.create_pr.core.git_push")
@patch("mcp_coder.workflows.create_pr.core.create_pull_request")
def test_workflow_pr_creation_fails(self, mock_create_pr, mock_push,
                                    mock_generate, mock_prereqs):
    """Test workflow exits when PR creation fails."""
    mock_prereqs.return_value = True
    mock_generate.return_value = ("Title", "Body")
    mock_push.return_value = {"success": True}
    mock_create_pr.return_value = False  # PR creation fails
    
    result = run_create_pr_workflow(Path("/test"), "claude", "cli")
    
    assert result == 1
    mock_create_pr.assert_called_once()
```

### Test 4: Generate Summary Exception
```python
@patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
@patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
def test_workflow_generate_summary_exception(self, mock_generate, mock_prereqs):
    """Test workflow handles generate_pr_summary exceptions."""
    mock_prereqs.return_value = True
    mock_generate.side_effect = ValueError("LLM failed")
    
    result = run_create_pr_workflow(Path("/test"), "claude", "cli")
    
    assert result == 1
    mock_generate.assert_called_once()
```

---

## VALIDATION

### Test Execution
```bash
# Run new workflow tests
pytest tests/workflows/create_pr/test_workflow.py -v

# Expected: All 4 tests PASS
```

### Code Quality
```bash
# Pylint check
pylint tests/workflows/create_pr/test_workflow.py

# Mypy check
mypy tests/workflows/create_pr/test_workflow.py
```

---

## LLM Prompt for This Step

```
I'm implementing Step 6 of the create_PR to CLI command conversion.

Context: See pr_info/steps/summary.md for architecture.

Task: Add unit tests for workflow orchestration.

Step 6 Details: Read pr_info/steps/step_6.md

Instructions:
1. Create tests/workflows/create_pr/test_workflow.py
2. Implement 4 essential tests as specified in step file
3. Run tests: pytest tests/workflows/create_pr/test_workflow.py -v
4. Run code quality checks
5. Commit with message: "Add workflow orchestration tests"

Keep tests focused and minimal - just the 4 essential scenarios.
```

---

## Verification Checklist

- [ ] File created: `tests/workflows/create_pr/test_workflow.py`
- [ ] Test 1: Complete success flow implemented
- [ ] Test 2: Prerequisites fail implemented
- [ ] Test 3: PR creation fails implemented
- [ ] Test 4: Generate summary exception implemented
- [ ] All tests pass: `pytest tests/workflows/create_pr/test_workflow.py -v`
- [ ] Pylint passes
- [ ] Mypy passes
- [ ] Commit created

---

## Dependencies

### Required Before This Step
- ✅ Step 2 completed (workflow core exists)
- ✅ `run_create_pr_workflow()` function exists

### Blocks
- Step 10 (final validation needs all tests)

---

## Notes

- **Minimal coverage:** Only 4 essential tests, not comprehensive
- **Focus on critical paths:** Success, prerequisite failure, PR failure, exception handling
- **Mock all dependencies:** Tests verify orchestration logic, not individual functions
- **Quick to implement:** Should take ~30 minutes
