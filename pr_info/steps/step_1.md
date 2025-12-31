# Step 1: Write Tests for Simplified Repository Identifier Handling

## Overview
Following TDD principles, create comprehensive tests for the new simplified repository identifier handling before implementing changes.

## LLM Prompt
```
Implement test cases for coordinator repository identifier handling as specified in pr_info/steps/summary.md. 

Requirements:
1. Test cache file naming with "owner/repo" format inputs
2. Test edge cases (no slash, multiple slashes, empty strings)
3. Verify no spurious warnings are logged
4. Ensure existing cache functionality continues to work

Follow the test patterns in the existing codebase and use pytest fixtures for setup.
```

## WHERE: File Paths
- **Primary**: `tests/utils/test_coordinator_cache.py`
- **Helper**: Add test utilities if needed in existing test structure

## WHAT: Main Functions

### Test Functions to Add/Modify
```python
def test_repo_identifier_parsing_valid_format()
def test_repo_identifier_parsing_edge_cases()
def test_cache_file_naming_no_warnings()
def test_existing_cache_functionality_preserved()
```

### Test Data Structures
```python
@pytest.fixture
def repo_test_cases():
    return [
        ("owner/repo", "owner", "repo"),
        ("org-name/repo-name", "org-name", "repo-name"), 
        ("owner/repo/subdir", "owner", "repo/subdir"),  # Edge case
        ("just-repo", None, "just-repo"),  # No slash
        ("", None, ""),  # Empty
    ]
```

## HOW: Integration Points
- **Import**: `from src.mcp_coder.cli.commands.coordinator import get_cached_eligible_issues`
- **Mocking**: Mock `IssueManager` to avoid GitHub API calls
- **Logging**: Capture log output to verify no warnings
- **Fixtures**: Use existing coordinator test fixtures

## ALGORITHM: Core Test Logic
```python
# For each test case:
1. Create mock IssueManager with test repo_full_name
2. Call get_cached_eligible_issues() 
3. Capture log output during execution
4. Assert no "Using fallback cache naming" warnings
5. Verify cache file path follows owner_repo.issues.json pattern
6. Confirm function returns expected results
```

## DATA: Expected Test Outcomes

### Return Values
- **Function Output**: `List[IssueData]` (same as before)
- **Cache File Path**: `Path` object with correct naming pattern
- **Log Messages**: No warnings containing "Using fallback cache naming"

### Test Assertions
```python
# Cache file naming
assert cache_path.name == "owner_repo.issues.json"

# No spurious warnings
assert "Using fallback cache naming" not in caplog.text

# Function still works
assert isinstance(result, list)
assert all(isinstance(issue, dict) for issue in result)
```

## Implementation Notes
- **Mock Strategy**: Mock GitHub API calls to focus on identifier parsing logic
- **Log Capture**: Use `pytest.caplog` to verify warning elimination
- **Parametrize**: Use `@pytest.mark.parametrize` for testing multiple repo format cases
- **Isolation**: Ensure tests don't affect real cache files or GitHub API calls