# Step 6: Add Unit Tests for Error Handling

## Objective
Add unit tests with mocking to verify error handling and edge cases (TDD completion).

## WHERE
- File: `tests/utils/test_github_operations.py` (modify existing)

## WHAT
- Add unit test class with mocked GitHub operations
- Test configuration missing scenarios
- Test GitHub API error handling
- Test invalid input validation

## HOW
### Unit Test Structure
```python
from unittest.mock import MagicMock, patch
import pytest

class TestGitHubOperationsUnit:
    """Unit tests with mocking for GitHub operations."""
    
    @patch('mcp_coder.utils.github_operations.get_config_value')
    def test_missing_github_config_returns_empty_dict(self, mock_config):
        """Test graceful handling when GitHub config missing."""
        
    @patch('mcp_coder.utils.github_operations._get_github_client')  
    def test_github_api_error_returns_empty_dict(self, mock_client):
        """Test error handling for GitHub API failures."""
```

## ALGORITHM
```
1. Add unit test class to existing test file
2. Mock get_config_value to return None (missing config)
3. Mock GitHub client to raise exceptions
4. Test each function returns {} on errors
5. Verify functions handle invalid inputs gracefully
6. Test authentication and permission errors
```

## DATA
- **Mock scenarios**: 
  - Missing token/repo_url_integration_tests config
  - GitHub API authentication errors
  - Network/connection errors
  - Invalid PR numbers
- **Expected returns**: Empty dict {} for all error cases

## LLM Prompt
```
You are implementing Step 6 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Add unit tests to tests/utils/test_github_operations.py to verify error handling and edge cases.

Requirements:
- Add TestGitHubOperationsUnit class (separate from integration tests)
- Mock get_config_value to test missing configuration scenarios
- Mock GitHub client to test API error handling
- Test that all functions return {} on errors
- Use patterns from existing unit tests (like test_user_config.py)
- Test scenarios:
  1. Missing GitHub token/repo config
  2. GitHub API authentication errors  
  3. Invalid PR numbers
  4. Network/connection errors

Follow existing mocking patterns and ensure comprehensive error coverage. These unit tests should run fast without external dependencies.
```

## Verification
- [ ] Unit test class added to existing file
- [ ] Missing configuration tests implemented
- [ ] GitHub API error mocking implemented
- [ ] All error scenarios return empty dict
- [ ] Tests run quickly without external calls
- [ ] Mocking follows existing patterns
- [ ] Edge cases covered (invalid inputs, etc.)
- [ ] Unit tests pass consistently
