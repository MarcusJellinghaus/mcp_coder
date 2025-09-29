# Step 1: Unit Tests for LabelsManager Validation

## Context
Create unit tests for LabelsManager class validation and initialization, following TDD approach. Tests written first, implementation follows in Step 2.

## WHERE

### Test File
```
tests/utils/test_github_operations.py
```

Add new test class `TestLabelsManagerUnit` after existing `TestPullRequestManagerUnit` class.

## WHAT

### Test Class and Methods

```python
class TestLabelsManagerUnit:
    """Unit tests for LabelsManager with mocked dependencies."""
    
    def test_initialization_requires_project_dir(self) -> None
    def test_initialization_requires_git_repository(self) -> None
    def test_initialization_requires_github_token(self) -> None
    def test_label_name_validation(self, tmp_path: Path) -> None
    def test_color_validation(self, tmp_path: Path) -> None
```

## HOW

### Imports Needed
```python
from mcp_coder.utils.github_operations import LabelsManager
from mcp_coder.utils.github_operations.labels_manager import LabelData
```

### Integration Pattern
- Use existing `tmp_path` fixture from pytest
- Mock `get_config_value` for token validation
- Follow same test structure as `TestPullRequestManagerUnit`

## ALGORITHM

### Validation Test Logic
```
1. Setup: Create temp directory, init git repo if needed
2. Mock: Patch get_config_value to return test token
3. Action: Try to create LabelsManager with invalid inputs
4. Assert: Verify appropriate ValueError raised with message
5. Cleanup: None needed (tmp_path auto-cleaned)
```

## DATA

### Test Inputs
- Valid label name: `"bug"`, `"feature-request"`
- Invalid label names: `""`, `"   "`, names with `#` or `@`
- Valid colors: `"FF0000"`, `"#FF0000"`, `"00ff00"`, `"#00FF00"` (6-char hex with or without #)
- Invalid colors: `"red"`, `"12345"`, `"GGGGGG"`, `"#12345"`

### Expected Outputs
- Validation failures: `ValueError` with descriptive message
- Empty operations: `{}` (empty dict) or `[]` (empty list)

## LLM Prompt

```
Implement unit tests for LabelsManager initialization and validation.

Context: Read pr_info/steps/summary.md for overview.
Reference: tests/utils/test_github_operations.py -> TestPullRequestManagerUnit class

Tasks:
1. Add TestLabelsManagerUnit class after TestPullRequestManagerUnit
2. Implement 5 test methods as specified in pr_info/steps/step_1.md
3. Follow existing test patterns for git repo setup and token mocking
4. Test validation rules:
   - Label names: non-empty strings without special chars (#, @, /)
   - Colors: 6-character hex strings (accepts both "FF0000" and "#FF0000" formats)
5. Use pytest.raises for ValueError assertions

Run: pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
Expected: All tests FAIL (no implementation yet - TDD approach)
```

## Notes

- Tests should FAIL initially (TDD red phase)
- Use `with pytest.raises(ValueError, match="...")` for exception tests
- Mock GitHub API - no real network calls in unit tests
- Keep tests simple and focused on one thing each
