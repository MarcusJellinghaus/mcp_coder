# Step 1: Add Test for Missing TASK_TRACKER.md (TDD - Red Phase)

## Context
Following Test-Driven Development, we first write a failing test that validates the expected behavior when TASK_TRACKER.md is missing.

Refer to `pr_info/steps/summary.md` for overall architecture and design decisions.

## WHERE: File Locations
- **Test File**: `tests/workflows/create_pr/test_prerequisites.py`
- **Target**: Add new test method to `TestCheckPrerequisites` class (around line 130)

## WHAT: Test Function Signature
```python
def test_prerequisites_missing_task_tracker(
    self,
    mock_base_branch: MagicMock,
    mock_current_branch: MagicMock,
    mock_incomplete_tasks: MagicMock,
    mock_clean: MagicMock,
) -> None:
    """Test prerequisites check succeeds when TASK_TRACKER.md is missing."""
```

## HOW: Integration Points

### Imports (already exist, verify)
```python
from unittest.mock import MagicMock, patch
from pathlib import Path
from mcp_coder.workflows.create_pr.core import check_prerequisites
```

### New Import Required
```python
from mcp_coder.workflow_utils.task_tracker import TaskTrackerFileNotFoundError
```

### Decorator Pattern
```python
@patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
@patch("mcp_coder.workflows.create_pr.core.get_incomplete_tasks")
@patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
@patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
def test_prerequisites_missing_task_tracker(
    self,
    mock_base_branch: MagicMock,
    mock_current_branch: MagicMock,
    mock_incomplete_tasks: MagicMock,
    mock_clean: MagicMock,
) -> None:
```

## ALGORITHM: Test Logic (Pseudocode)
```
1. Setup: Mock git status as clean
2. Setup: Mock get_incomplete_tasks to raise TaskTrackerFileNotFoundError
3. Setup: Mock current branch as "feature-branch"
4. Setup: Mock base branch as "main"
5. Execute: Call check_prerequisites()
6. Assert: Result is True (prerequisites passed)
7. Assert: All mocks were called correctly
```

## DATA: Test Expectations

### Mock Configurations
```python
mock_clean.return_value = True  # Git is clean
mock_incomplete_tasks.side_effect = TaskTrackerFileNotFoundError(
    "TASK_TRACKER.md not found"
)
mock_current_branch.return_value = "feature-branch"
mock_base_branch.return_value = "main"
```

### Assertions
```python
assert result is True  # Prerequisites should pass

# Verify call chain
mock_clean.assert_called_once()
mock_incomplete_tasks.assert_called_once()
mock_current_branch.assert_called_once()
mock_base_branch.assert_called_once()
```

## Implementation Code

```python
@patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
@patch("mcp_coder.workflows.create_pr.core.get_incomplete_tasks")
@patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
@patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
def test_prerequisites_missing_task_tracker(
    self,
    mock_base_branch: MagicMock,
    mock_current_branch: MagicMock,
    mock_incomplete_tasks: MagicMock,
    mock_clean: MagicMock,
) -> None:
    """Test prerequisites check succeeds when TASK_TRACKER.md is missing."""
    # Arrange: Setup mocks for successful prerequisites except missing task tracker
    mock_clean.return_value = True
    mock_incomplete_tasks.side_effect = TaskTrackerFileNotFoundError(
        "TASK_TRACKER.md not found at /test/path/TASK_TRACKER.md"
    )
    mock_current_branch.return_value = "feature-branch"
    mock_base_branch.return_value = "main"

    # Act: Run prerequisites check
    result = check_prerequisites(Path("/test/project"))

    # Assert: Should pass despite missing task tracker
    assert result is True
    
    # Verify all prerequisite checks were executed
    mock_clean.assert_called_once()
    mock_incomplete_tasks.assert_called_once()
    mock_current_branch.assert_called_once()
    mock_base_branch.assert_called_once()
```

## Expected Test Result
**Status**: ❌ FAIL (Red phase - this is expected)

**Reason**: Current implementation catches all exceptions and returns False. The test will fail because `check_prerequisites()` currently returns False for TaskTrackerFileNotFoundError.

## Verification Commands

```bash
# Run only this test
pytest tests/workflows/create_pr/test_prerequisites.py::TestCheckPrerequisites::test_prerequisites_missing_task_tracker -v

# Expected output:
# FAILED - AssertionError: assert False is True
```

## LLM Prompt for Implementation

```
I need to implement Step 1 of the plan in pr_info/steps/step_1.md.

Please:
1. Read pr_info/steps/summary.md for overall context
2. Read pr_info/steps/step_1.md for detailed requirements
3. Add the import for TaskTrackerFileNotFoundError
4. Add the new test method test_prerequisites_missing_task_tracker to the TestCheckPrerequisites class
5. Place it after the existing test_prerequisites_task_tracker_exception method
6. Run the test to verify it fails (Red phase of TDD)

Follow the exact implementation code provided in step_1.md.
```

## Success Criteria
- ✅ Import statement added
- ✅ New test method added to correct location
- ✅ Test runs and FAILS (returns False instead of True)
- ✅ No syntax errors
- ✅ Pytest can discover and run the test
