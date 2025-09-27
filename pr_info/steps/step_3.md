# Step 3: Write Failing Integration Test (TDD)

## Objective
Create integration test using PullRequestManager that fails with current empty implementations, driving the real implementation.

## WHERE
- File: `tests/utils/test_github_operations.py` (new file)

## WHAT
- Single integration test class using PullRequestManager instance
- Conditional skipping when GitHub credentials unavailable
- Test that creates → reads → lists → closes → merges a PR using manager
- Proper cleanup and error handling

## HOW
### Test Structure
```python
"""Integration tests for GitHub operations."""

import pytest
from datetime import datetime
from mcp_coder.utils.github_operations import PullRequestManager, create_pr_manager
from mcp_coder.utils.user_config import get_config_value

@pytest.mark.github_integration
class TestPullRequestManagerIntegration:
    """Integration tests requiring GitHub API access."""
    
    @pytest.fixture
    def pr_manager(self):
        """Create PullRequestManager instance for testing."""
        test_repo_url = get_config_value("github.test_repo_url")
        token = get_config_value("github.token")
        
        if not test_repo_url or not token:
            pytest.skip("GitHub configuration missing - add github.test_repo_url and github.token to config")
        
        return PullRequestManager(test_repo_url, token)
    
    def test_pr_manager_lifecycle(self, pr_manager):
        """Test complete PR lifecycle: create → read → list → close."""
        # This will fail initially due to empty dict returns
```

## ALGORITHM
```
1. Import PullRequestManager and create_pr_manager
2. Create pytest fixture for manager instance with config validation
3. Skip test gracefully if GitHub config missing
4. Create PR with unique branch name (timestamp-based)
5. Assert PR creation returned number and url
6. Read PR details and verify data matches
7. List PRs and verify created PR appears in results
8. Close PR and verify state change
9. Test factory function works correctly
10. Test manager properties return expected types
11. Include cleanup in finally block
```

## DATA
- **Input**: GitHub token and repo URL from config
- **Expected assertions**:
  - create_pull_request returns dict with 'number' and 'url' keys
  - get_pull_request returns dict with 'number', 'title', 'state' keys  
  - list_pull_requests returns list containing created PR
  - close_pull_request returns dict with 'number' and updated 'state'
  - Factory function returns PullRequestManager instance
  - Properties return string values
- **Test data**: Unique branch names with timestamp, test PR title/body

## LLM Prompt
```
You are implementing Step 3 of the GitHub Pull Request Operations feature using the updated PullRequestManager approach.

Create tests/utils/test_github_operations.py with failing integration tests that will drive our PullRequestManager implementation.

Requirements:
- Create TestPullRequestManagerIntegration class with @pytest.mark.github_integration
- Create pr_manager pytest fixture that checks config and skips if missing
- Implement test_pr_manager_lifecycle method for complete PR workflow
- Add test_factory_function to verify create_pr_manager works
- Add test_manager_properties to verify repository_name and default_branch
- Skip tests gracefully if GitHub config missing (check token and test_repo_url)
- Tests should fail initially because methods return empty dicts/lists
- Use unique branch names with timestamp to avoid conflicts
- Follow existing integration test patterns from the codebase
- Include proper cleanup in finally block
- Use PullRequestManager instance throughout, not individual functions

The test should verify:
1. create_pull_request returns dict with 'number' and 'url'
2. get_pull_request returns dict with PR details
3. list_pull_requests returns list with PR in results
4. close_pull_request returns dict with updated state
5. Factory function creates proper manager instance
6. Properties return expected string types

These failing tests will drive our implementation in the next step.
```

## Verification
- [ ] Test file created with proper imports
- [ ] @pytest.mark.github_integration marker applied
- [ ] Graceful skipping when config missing
- [ ] pr_manager fixture creates PullRequestManager instance
- [ ] test_pr_manager_lifecycle tests complete workflow
- [ ] test_factory_function verifies create_pr_manager
- [ ] test_manager_properties verifies properties
- [ ] Tests currently fail due to empty dict/list returns
- [ ] Unique branch naming implemented
- [ ] Proper assertions for expected return data
- [ ] Cleanup logic included in finally block
