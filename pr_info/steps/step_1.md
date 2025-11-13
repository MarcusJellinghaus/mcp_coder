# Step 1: Create Test Infrastructure for Label Update Feature

## Context
This is the first step in implementing auto-label updates. Following TDD principles, we create comprehensive tests before implementing the actual functionality. This establishes clear requirements and validates our design.

**Reference**: See `pr_info/steps/summary.md` for complete architectural overview.

## Objective
Create test file with complete mock infrastructure to validate label update behavior including happy path, error cases, and edge cases.

## WHERE: File Structure
```
tests/utils/github_operations/test_issue_manager_label_update.py  (CREATE)
  └─ New test module for label update functionality
```

## WHAT: Test Functions to Implement

### 1. Test Class Setup
```python
class TestIssueManagerLabelUpdate:
    """Test suite for IssueManager.update_workflow_label() method."""
```

### 2. Test Functions (8 total)
```python
def test_update_workflow_label_success_happy_path(mock_github, tmp_path)
    # Tests successful label transition with all prerequisites met

def test_update_workflow_label_invalid_branch_name(mock_github, tmp_path)
    # Tests branch name that doesn't match {number}-{title} pattern

def test_update_workflow_label_branch_not_linked(mock_github, tmp_path)
    # Tests branch that exists but isn't linked to the issue

def test_update_workflow_label_already_correct_state(mock_github, tmp_path)
    # Tests idempotent behavior - issue already has target label

def test_update_workflow_label_missing_source_label(mock_github, tmp_path)
    # Tests transition when issue doesn't have source label

def test_update_workflow_label_label_not_in_config(mock_github, tmp_path)
    # Tests when internal_id doesn't exist in labels.json

def test_update_workflow_label_github_api_error(mock_github, tmp_path)
    # Tests GitHub API failure during label update

def test_update_workflow_label_no_branch_provided(mock_github, tmp_path)
    # Tests automatic branch name detection from git
```

## HOW: Integration Points

### Imports Required
```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mcp_coder.utils.github_operations.issue_manager import (
    IssueManager,
    IssueData,
)
from mcp_coder.utils.github_operations.issue_branch_manager import (
    IssueBranchManager,
)
```

### Mock Infrastructure
```python
@pytest.fixture
def mock_github():
    """Mock GitHub client and repository."""
    # Returns mock with repo, issue, labels configured

@pytest.fixture
def mock_label_config():
    """Mock label configuration loading."""
    # Returns test label config with implementing/code_review

@pytest.fixture  
def mock_git_operations():
    """Mock git operations for branch name detection."""
    # Returns mock for get_current_branch_name()
```

## ALGORITHM: Test Flow Pattern

### Happy Path Test Flow
```
1. Setup: Create mock repo with issue #123, branch "123-feature"
2. Mock: get_linked_branches() returns ["123-feature"]
3. Mock: Label config returns valid label names
4. Call: update_workflow_label("implementing", "code_review")
5. Assert: set_labels() called with correct new label set
6. Assert: Returns True
```

### Error Case Test Flow
```
1. Setup: Create mock with specific error condition
2. Call: update_workflow_label() with test parameters
3. Assert: Returns False (non-blocking)
4. Assert: Appropriate log message emitted
5. Assert: No exceptions raised
```

## DATA: Test Data Structures

### Mock Issue Data
```python
MOCK_ISSUE = IssueData(
    number=123,
    title="Test Feature",
    body="Test body",
    state="open",
    labels=["status-06:implementing", "bug"],
    assignees=[],
    user="testuser",
    created_at="2024-01-01T00:00:00Z",
    updated_at="2024-01-01T00:00:00Z",
    url="https://github.com/test/repo/issues/123",
    locked=False,
)
```

### Mock Label Config
```python
MOCK_LABELS_CONFIG = {
    "workflow_labels": [
        {
            "internal_id": "implementing",
            "name": "status-06:implementing",
            "color": "bfdbfe",
            "description": "Code being written",
            "category": "bot_busy"
        },
        {
            "internal_id": "code_review",
            "name": "status-07:code-review",
            "color": "f59e0b",
            "description": "Implementation complete",
            "category": "human_action"
        }
    ],
    "ignore_labels": []
}
```

## Implementation Details

### Test Assertions Pattern
```python
# For successful transitions
assert result is True
mock_set_labels.assert_called_once()
args = mock_set_labels.call_args[0]
assert "status-07:code-review" in args
assert "status-06:implementing" not in args

# For error cases
assert result is False
# Verify appropriate logging
assert "WARNING" in caplog.text or "ERROR" in caplog.text
```

### Mock Setup Pattern
```python
# Mock IssueManager dependencies
with patch.object(IssueManager, '_get_repository') as mock_repo:
    with patch('mcp_coder.utils.github_operations.label_config.load_labels_config') as mock_config:
        with patch.object(IssueBranchManager, 'get_linked_branches') as mock_branches:
            # Setup return values
            mock_branches.return_value = ["123-feature"]
            mock_config.return_value = MOCK_LABELS_CONFIG
            
            # Run test
            manager = IssueManager(project_dir=tmp_path)
            result = manager.update_workflow_label(...)
```

## Validation Checklist
- [ ] All 8 test functions implemented with clear docstrings
- [ ] Mock fixtures properly isolate GitHub API calls
- [ ] Tests cover happy path and all error conditions
- [ ] Test assertions validate both return value and side effects
- [ ] Log message assertions included for error cases
- [ ] Tests use tmp_path for any file system operations
- [ ] No actual GitHub API calls made (all mocked)
- [ ] Tests follow pytest conventions and best practices

## Next Step Preview
**Step 2** will implement the actual `update_workflow_label()` method to make these tests pass, following the single-function KISS design.

---

## LLM Prompt for This Step

```
You are implementing Step 1 of the auto-label update feature for mcp-coder.

CONTEXT:
Read pr_info/steps/summary.md for complete architectural overview.
This step creates comprehensive test infrastructure following TDD principles.

TASK:
Create tests/utils/github_operations/test_issue_manager_label_update.py with:
1. Complete mock infrastructure (fixtures for GitHub API, label config, git ops)
2. Eight test functions covering happy path and error cases
3. Clear assertions validating behavior and return values
4. Proper use of pytest conventions

REQUIREMENTS:
- All GitHub API calls must be mocked (no real API calls)
- Tests should validate both return values and side effects
- Include log message assertions for error cases
- Follow existing test patterns in tests/utils/github_operations/
- Use tmp_path fixture for any file system operations

REFERENCE THIS STEP:
pr_info/steps/step_1.md (contains detailed specifications)

After implementation, run code quality checks:
1. mcp__code-checker__run_pylint_check
2. mcp__code-checker__run_pytest_check with fast unit tests
3. mcp__code-checker__run_mypy_check
```
