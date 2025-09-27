# Step 3: Write Failing Integration Test (TDD)

## Objective
Create integration test that fails with current empty implementations, driving the real implementation.

## WHERE
- File: `tests/utils/test_github_operations.py` (new file)

## WHAT
- Single integration test class with roundtrip test
- Conditional skipping when GitHub credentials unavailable
- Test that creates → reads → closes a PR
- Proper cleanup and error handling

## HOW
### Test Structure
```python
"""Integration tests for GitHub operations."""

import pytest
from mcp_coder.utils.github_operations import (
    create_pull_request,
    get_pull_request, 
    close_pull_request
)
from mcp_coder.utils.user_config import get_config_value

@pytest.mark.github_integration
class TestGitHubOperationsIntegration:
    """Integration tests requiring GitHub API access."""
    
    def test_create_read_close_pr_roundtrip(self):
        """Test complete PR lifecycle: create → read → close."""
        # This will fail initially due to empty dict returns
```

## ALGORITHM
```
1. Import required functions and pytest
2. Check for GitHub configuration, skip if missing
3. Create PR with unique branch name (timestamp-based)
4. Assert PR creation returned number and url
5. Read PR details and verify data
6. Close PR and verify state change
```

## DATA
- **Input**: GitHub token and repo URL from config
- **Expected assertions**:
  - create_pull_request returns dict with 'number' and 'url' keys
  - get_pull_request returns dict with 'number', 'title', 'state', 'url' keys  
  - close_pull_request returns dict with 'number' and 'state' keys
- **Test data**: Unique branch names, test PR title/body

## LLM Prompt
```
You are implementing Step 3 of the GitHub Pull Request Operations feature as described in pr_info/steps/summary.md.

Create tests/utils/test_github_operations.py with a failing integration test that will drive our implementation.

Requirements:
- Create TestGitHubOperationsIntegration class with @pytest.mark.github_integration
- Implement test_create_read_close_pr_roundtrip method
- Skip test gracefully if GitHub config missing (check token and repo_url_integration_tests)
- Test should fail initially because functions return empty dicts
- Use unique branch names with timestamp to avoid conflicts
- Follow existing integration test patterns from the codebase
- Include proper cleanup even if test fails

The test should verify:
1. create_pull_request returns dict with 'number' and 'url'
2. get_pull_request returns dict with PR details
3. close_pull_request returns dict with updated state

This failing test will drive our implementation in the next step.
```

## Verification
- [ ] Test file created with proper imports
- [ ] @pytest.mark.github_integration marker applied
- [ ] Graceful skipping when config missing
- [ ] Test currently fails due to empty dict returns
- [ ] Unique branch naming implemented
- [ ] Proper assertions for expected return data
- [ ] Cleanup logic included
