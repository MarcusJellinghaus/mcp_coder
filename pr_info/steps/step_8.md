# Step 8: Integration Tests

## Objective
Create integration tests that use real GitHub API calls, marked with `github_integration` pytest marker for optional execution.

## WHERE
- **File**: `tests/utils/test_issue_manager_integration.py` (new file)

## WHAT
Integration test class with real API calls:
```python
@pytest.mark.github_integration
class TestIssueManagerIntegration:
    def test_real_github_issue_operations(self): ...
    def test_real_label_management(self): ...
    def test_real_comment_operations(self): ...
    def test_full_issue_lifecycle(self): ...
```

## HOW
- Use `@pytest.mark.github_integration` marker (same as existing integration tests)
- Follow patterns from existing GitHub integration tests
- Use real GitHub repository for testing (same as PR manager tests)
- Include setup/teardown for test data cleanup
- Test against actual GitHub API with authentication

## ALGORITHM
```
1. Set up test repository and authentication (same as PR integration tests)
2. Test basic issue operations (create, get, close) against real API
3. Test label management with real repository labels
4. Test comment operations with real issue comments
5. Clean up test data after each test
```

## DATA
```python
# Integration test configuration
@pytest.mark.github_integration
class TestIssueManagerIntegration:
    # Uses real GitHub API - requires authentication
    # Marked for optional execution in CI/CD
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 8: Integration Tests.

Create integration tests in tests/utils/test_issue_manager_integration.py using real GitHub API calls.

Requirements:
- Use @pytest.mark.github_integration marker on all test methods
- Follow the same patterns as existing GitHub integration tests in the codebase
- Test against real GitHub API with proper authentication
- Include proper setup/teardown for test data management
- Test full issue lifecycle scenarios (create → comment → label → close)
- Use same test repository setup as existing PR integration tests

These tests should validate the actual GitHub API integration works correctly.
```
