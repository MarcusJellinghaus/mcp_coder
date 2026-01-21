# Step 1: Create Unit Tests for `set_status` Command

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Approach**: Test-Driven Development

## LLM Prompt
```
Implement Step 1 from pr_info/steps/summary.md:
Create unit tests for the `set_status` CLI command in `tests/cli/commands/test_set_status.py`.
Follow the test patterns from `tests/cli/commands/test_define_labels.py`.
Do not implement the actual command yet - only the tests.
```

## WHERE
- **File**: `tests/cli/commands/test_set_status.py`

## WHAT - Test Classes and Methods

```python
class TestSetStatusHelpers:
    """Test helper functions."""
    
    def test_get_status_labels_from_config(labels_config_path: Path) -> None:
        """Test loading status labels from config."""
    
    def test_validate_status_label_valid() -> None:
        """Test validation accepts valid status labels."""
    
    def test_validate_status_label_invalid() -> None:
        """Test validation rejects invalid labels."""


class TestComputeNewLabels:
    """Test label computation logic."""
    
    def test_compute_replaces_status_label() -> None:
        """Test that existing status-* labels are replaced."""
    
    def test_compute_preserves_non_status_labels() -> None:
        """Test that non-status labels are preserved."""
    
    def test_compute_with_no_existing_status() -> None:
        """Test adding status when none exists."""


class TestExecuteSetStatus:
    """Test CLI execute function."""
    
    def test_execute_success_with_branch_detection() -> None:
        """Test successful execution with auto-detected issue."""
    
    def test_execute_success_with_explicit_issue() -> None:
        """Test successful execution with --issue flag."""
    
    def test_execute_invalid_label_returns_one() -> None:
        """Test invalid label name returns exit code 1."""
    
    def test_execute_no_issue_detected_returns_one() -> None:
        """Test returns 1 when branch doesn't match pattern."""
    
    def test_execute_github_error_returns_one() -> None:
        """Test returns 1 on GitHub API error."""
```

## HOW - Integration Points

```python
# Imports
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Fixtures to use
@pytest.fixture
def labels_config_path() -> Path:
    """Use existing fixture from conftest.py"""

@pytest.fixture  
def mock_issue_manager() -> MagicMock:
    """Mock IssueManager for GitHub operations."""
```

## ALGORITHM - Core Test Logic

```
# test_compute_replaces_status_label
1. current_labels = {"status-03:planning", "bug", "enhancement"}
2. new_status = "status-05:plan-ready"
3. all_status_names = load from config
4. result = compute_new_labels(current_labels, new_status, all_status_names)
5. assert result == {"status-05:plan-ready", "bug", "enhancement"}

# test_execute_success_with_branch_detection
1. Mock get_current_branch_name -> "123-feature-name"
2. Mock extract_issue_number_from_branch -> 123
3. Mock IssueManager.get_issue -> returns issue with labels
4. Mock IssueManager.set_labels -> returns success
5. Call execute_set_status(args)
6. Assert return code == 0
7. Assert set_labels called with correct labels
```

## DATA - Test Data Structures

```python
# Mock issue data for tests
MOCK_ISSUE_DATA = {
    "number": 123,
    "title": "Test Issue",
    "labels": ["status-03:planning", "bug"],
    "state": "open",
    # ... other IssueData fields
}

# Valid status labels (subset for tests)
VALID_STATUS_LABELS = [
    "status-01:created",
    "status-05:plan-ready", 
    "status-08:ready-pr",
]

# Expected args namespace
MOCK_ARGS = argparse.Namespace(
    status_label="status-05:plan-ready",
    issue=None,  # or 123 for explicit
    project_dir=None,
)
```

## Expected Test Count
- ~6-8 focused unit tests (per Decision #7, let TDD drive actual count):
  - Label validation (1-2 tests)
  - Label computation (2-3 tests)
  - Execute function (3-4 tests)
