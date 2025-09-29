# Step 10: Comprehensive Integration Tests

## Objective
Create additional comprehensive integration tests that cover edge cases and additional scenarios beyond the basic issue lifecycle.

## WHERE
- **File**: `tests/utils/test_issue_manager_integration.py` (enhance existing file)

## WHAT
Additional integration test scenarios:
```python
@pytest.mark.github_integration
def test_multiple_issues_filtering(): ...

@pytest.mark.github_integration  
def test_label_edge_cases(): ...

@pytest.mark.github_integration
def test_error_handling_scenarios(): ...
```

## HOW
- Use `@pytest.mark.github_integration` marker on all test methods
- Test edge cases and scenarios not covered in the basic lifecycle test
- Test error conditions that should raise exceptions vs return empty data
- Use real GitHub API with proper authentication

## ALGORITHM
```
1. Test get_issues() with various filtering options (multiple issues, different states, label filtering)
2. Test label operations with edge cases (non-existent labels, empty label lists)
3. Test error scenarios that should trigger different error handling paths
4. Validate that the hybrid error handling works correctly with real API
```

## DATA
```python
# Additional integration test coverage
- Multiple issues management
- Complex label filtering scenarios  
- Error handling validation
- Performance with multiple operations
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 10: Comprehensive Integration Tests.

Add additional integration test methods to the existing tests/utils/test_issue_manager_integration.py file.

Requirements:
- Use @pytest.mark.github_integration marker on all new test methods
- Test scenarios not covered in the basic lifecycle test from previous steps
- Focus on edge cases: multiple issues, complex filtering, error conditions
- Test the hybrid error handling approach with real GitHub API
- Test get_issues() filtering capabilities with multiple test issues
- Validate that auth/permission errors raise exceptions while other errors return empty data

Create comprehensive test coverage while using the configured test repository for all real API calls.
```
