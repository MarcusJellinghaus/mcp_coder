# Step 7: Unit Tests with Mocking

## Objective
Create comprehensive unit tests for IssueManager using mocks, following the same testing patterns as existing codebase.

## WHERE
- **File**: `tests/utils/test_issue_manager.py` (new file)

## WHAT
Unit test class with mocked GitHub API:
```python
class TestIssueManager:
    def test_init_validation(self): ...
    def test_get_issue(self): ...  
    def test_get_issues(self): ...
    def test_create_issue(self): ...
    def test_close_issue(self): ...
    def test_add_labels(self): ...
    def test_add_comment(self): ...
    # ... more test methods
```

## HOW
- Follow existing test patterns from `test_github_operations.py` and PR manager tests
- Use pytest fixtures for common setup
- Mock GitHub API calls using unittest.mock
- Test both success and error scenarios
- Use same assertion patterns as existing tests

## ALGORITHM
```
1. Create test fixtures for IssueManager setup (mock project_dir, config)
2. Mock GitHub API responses for each operation
3. Test successful operations with expected return data
4. Test error scenarios (invalid inputs, API failures)  
5. Verify logging calls and validation behavior
```

## DATA
```python
# Test fixtures and mocks needed
@pytest.fixture
def mock_issue_manager(): ...

@pytest.fixture  
def mock_github_issue(): ...

# Test data structures
sample_issue_data = IssueData(...)
sample_comment_data = CommentData(...)
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 7: Unit Tests with Mocking.

Create comprehensive unit tests in tests/utils/test_issue_manager.py following the existing testing patterns in the codebase.

Requirements:
- Follow the same test structure and patterns as existing GitHub operation tests
- Mock all GitHub API calls using unittest.mock
- Test both success and failure scenarios for each method
- Use pytest fixtures for common setup
- Include validation testing for all input parameters
- Test error handling and logging behavior
- Use same assertion patterns as existing tests

Focus on thorough unit testing with mocked dependencies for fast test execution.
```
