# Step 2: IssueManager.list_issues() Method

## LLM Prompt
```
Implement Step 2 from pr_info/steps/summary.md: Add list_issues() method to IssueManager class with GitHub API pagination support.

Follow Test-Driven Development:
1. Write failing unit tests for list_issues() method
2. Implement the method with pagination handling
3. Verify tests pass with mocked GitHub API
4. Write integration test (optional, marked with github_integration)
5. Run all code quality checks using MCP tools

Use ONLY MCP filesystem tools for all file operations (mcp__filesystem__*).
Reference existing IssueManager patterns from src/mcp_coder/utils/github_operations/issue_manager.py
```

## WHERE: File Paths

### Files to MODIFY
```
src/mcp_coder/utils/github_operations/issue_manager.py    # Add list_issues() method
tests/utils/github_operations/test_issue_manager.py       # Add unit tests
```

## WHAT: Main Function

### Function Signature
```python
@log_function_call
@_handle_github_errors(default_return=[])
def list_issues(
    self,
    state: str = "all",
    include_pull_requests: bool = False
) -> List[IssueData]:
    """List all issues in the repository with pagination support.
    
    Args:
        state: Issue state filter - 'open', 'closed', or 'all' (default: 'all')
        include_pull_requests: Whether to include PRs in results (default: False)
    
    Returns:
        List of IssueData dictionaries with issue information, or empty list on error
        
    Raises:
        GithubException: For authentication or permission errors
        
    Example:
        >>> issues = manager.list_issues(state='open', include_pull_requests=False)
        >>> print(f"Found {len(issues)} open issues")
        >>> for issue in issues:
        ...     print(f"#{issue['number']}: {issue['title']}")
    """
```

### Return Data Structure
```python
# List[IssueData] where IssueData is:
{
    "number": 123,
    "title": "Issue title",
    "body": "Issue description",
    "state": "open",  # or "closed"
    "labels": ["status-01:created", "bug"],
    "assignees": ["username"],
    "user": "author_username",
    "created_at": "2025-10-12T10:30:00",
    "updated_at": "2025-10-12T15:45:00",
    "url": "https://github.com/owner/repo/issues/123",
    "locked": False
}
```

## HOW: Integration Points

### Decorators (Follow Existing Pattern)
```python
@log_function_call                       # From mcp_coder.utils.log_utils
@_handle_github_errors(default_return=[])  # From base_manager.py
```

### Dependencies
```python
from typing import List
from .base_manager import BaseGitHubManager, _handle_github_errors
from mcp_coder.utils.log_utils import log_function_call
```

### GitHub API Pagination
```python
# PyGithub handles pagination with PaginatedList
# Iterate through all pages automatically:
for issue in repo.get_issues(state=state):
    # Process each issue
    pass
```

## ALGORITHM: List Issues with Filtering

```
FUNCTION list_issues(state, include_pull_requests):
    repo = _get_repository()
    IF repo IS None:
        LOG error
        RETURN []
    
    issues_list = []
    FOR EACH issue IN repo.get_issues(state=state):
        IF NOT include_pull_requests AND issue.pull_request IS NOT None:
            CONTINUE  # Skip pull requests
        
        issue_data = convert_to_IssueData(issue)
        APPEND issue_data TO issues_list
    
    RETURN issues_list
```

## DATA: Test Cases

### Unit Tests (test_issue_manager.py)
```python
def test_list_issues_default_parameters(mock_repo):
    """Test list_issues with default parameters (all, no PRs)"""
    # Mock repo.get_issues() to return issues without PRs
    # Verify: state='all', PRs filtered out
    pass

def test_list_issues_open_only(mock_repo):
    """Test list_issues filters by state='open'"""
    # Mock repo.get_issues(state='open')
    # Verify: only open issues returned
    pass

def test_list_issues_include_pull_requests(mock_repo):
    """Test list_issues includes PRs when flag=True"""
    # Mock repo.get_issues() with PRs
    # Verify: PRs included in results
    pass

def test_list_issues_pagination_handled(mock_repo):
    """Test list_issues handles GitHub API pagination"""
    # Mock repo.get_issues() returning paginated results (30+ items)
    # Verify: all pages fetched and returned
    pass

def test_list_issues_empty_repository(mock_repo):
    """Test list_issues returns empty list for repo with no issues"""
    # Mock repo.get_issues() returning empty PaginatedList
    # Verify: empty list returned
    pass

def test_list_issues_github_error_handling(mock_repo):
    """Test list_issues handles GitHub API errors gracefully"""
    # Mock repo.get_issues() raising GithubException
    # Verify: empty list returned, error logged
    pass
```

### Integration Test (Optional, marked with github_integration)
```python
@pytest.mark.github_integration
def test_list_issues_real_repository():
    """Integration test with real GitHub API (slow, requires auth)"""
    # Uses real IssueManager with test repository
    # Verifies actual pagination and filtering
    pass
```

## Implementation Pattern (Following Existing Code)

### Example from get_issue() to follow:
```python
@log_function_call
@_handle_github_errors(default_return=IssueData(...))
def get_issue(self, issue_number: int) -> IssueData:
    # Validate input
    if not self._validate_issue_number(issue_number):
        return IssueData(...)
    
    # Get repository
    repo = self._get_repository()
    if repo is None:
        logger.error("Failed to get repository")
        return IssueData(...)
    
    # Call GitHub API
    github_issue = repo.get_issue(issue_number)
    
    # Convert to IssueData
    return IssueData(
        number=github_issue.number,
        title=github_issue.title,
        # ... all fields
    )
```

### Apply same pattern to list_issues():
1. Validate inputs (state parameter)
2. Get repository via `_get_repository()`
3. Call GitHub API: `repo.get_issues(state=state)`
4. Filter PRs if needed: check `issue.pull_request`
5. Convert each to IssueData
6. Return list

## Implementation Checklist
- [ ] Add list_issues() method to IssueManager class
- [ ] Follow existing code patterns (decorators, error handling)
- [ ] Implement pagination (iterate through PaginatedList)
- [ ] Filter pull requests based on flag
- [ ] Write 6 unit tests with mocked GitHub API
- [ ] Optional: Write 1 integration test marked with github_integration
- [ ] Run fast unit tests: `mcp__code-checker__run_pytest_check` with exclusions
- [ ] Verify all tests pass

## Quality Checks
```python
# Fast unit tests (recommended for development):
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# With integration tests (slow, requires GitHub token):
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto"],
    markers=["github_integration"]
)

# Run mypy for type checking:
mcp__code-checker__run_mypy_check()

# Run pylint for code quality:
mcp__code-checker__run_pylint_check()
```

## Expected Test Output
```
tests/utils/github_operations/test_issue_manager.py::test_list_issues_default_parameters PASSED
tests/utils/github_operations/test_issue_manager.py::test_list_issues_open_only PASSED
tests/utils/github_operations/test_issue_manager.py::test_list_issues_include_pull_requests PASSED
tests/utils/github_operations/test_issue_manager.py::test_list_issues_pagination_handled PASSED
tests/utils/github_operations/test_issue_manager.py::test_list_issues_empty_repository PASSED
tests/utils/github_operations/test_issue_manager.py::test_list_issues_github_error_handling PASSED
```

## Notes
- PyGithub's `get_issues()` returns a PaginatedList that automatically handles pagination
- Just iterate through it normally: `for issue in repo.get_issues():`
- Check `issue.pull_request` field: if not None, it's a PR
- Follow exact same error handling pattern as existing methods
- Use `@log_function_call` decorator for automatic logging
- Use `@_handle_github_errors` decorator for consistent error handling
