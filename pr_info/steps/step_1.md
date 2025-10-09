# Step 1: Add get_issue() Method to IssueManager

## LLM Prompt
```
Read pr_info/steps/summary.md and this step file. Implement the get_issue() method in IssueManager following TDD approach:
1. First write unit tests in test_issue_manager.py
2. Then implement the method in issue_manager.py
Follow existing patterns and conventions from the codebase.
```

## WHERE
- **Test File**: `tests/utils/github_operations/test_issue_manager.py`
- **Implementation File**: `src/mcp_coder/utils/github_operations/issue_manager.py`

## WHAT

### Test Functions
```python
def test_get_issue_success(mock_github: Mock, tmp_path: Path) -> None
def test_get_issue_invalid_number(tmp_path: Path) -> None
def test_get_issue_auth_error_raises(mock_github: Mock, tmp_path: Path) -> None
def test_get_issue_not_found_error(mock_github: Mock, tmp_path: Path) -> None
```

### Implementation Function
```python
@log_function_call
@_handle_github_errors(default_return=IssueData(...))
def get_issue(self, issue_number: int) -> IssueData
```

## HOW

### Integration Points
1. **Decorators**: 
   - `@log_function_call` - From `mcp_coder.utils.log_utils`
   - `@_handle_github_errors(default_return=...)` - From base_manager.py

2. **Dependencies**:
   - Use `self._validate_issue_number()` for validation
   - Use `self._get_repository()` to access GitHub repo
   - Call `repo.get_issue(issue_number)` from PyGithub

3. **Error Handling**:
   - Decorator handles GithubException (re-raises auth errors)
   - Return empty IssueData on validation failure

## ALGORITHM

### Test Algorithm (test_get_issue_success)
```
1. Setup: Create git repo, mock GitHub API responses
2. Mock: Issue object with all fields populated
3. Execute: Call manager.get_issue(123)
4. Assert: Verify returned IssueData matches mock values
5. Assert: Verify repo.get_issue() was called once
```

### Implementation Algorithm
```
1. Validate issue_number using _validate_issue_number()
2. Get repository using _get_repository()
3. Fetch issue: github_issue = repo.get_issue(issue_number)
4. Convert to IssueData with all fields
5. Return IssueData dictionary
```

## DATA

### Input
- `issue_number: int` - Issue number to fetch (must be positive)

### Output - IssueData TypedDict
```python
{
    "number": int,           # Issue number
    "title": str,            # Issue title
    "body": str,             # Issue description
    "state": str,            # "open" or "closed"
    "labels": List[str],     # Label names
    "user": Optional[str],   # Username of creator
    "created_at": Optional[str],  # ISO format timestamp
    "updated_at": Optional[str],  # ISO format timestamp
    "url": str,              # HTML URL
    "locked": bool           # Lock status
}
```

### Error Cases
- Returns empty IssueData (all zeros/empty) if:
  - issue_number is invalid (≤ 0)
  - Repository access fails
  - Issue not found (handled by decorator)
- Raises GithubException if:
  - Authentication error (401)
  - Permission error (403)

## Test Patterns to Follow

```python
@pytest.mark.git_integration
class TestIssueManagerUnit:
    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
        # Setup git repo with origin remote
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")
        
        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        # ... set all other fields
        
        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        
        # Execute and assert
        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)
            result = manager.get_issue(123)
            
            assert result["number"] == 123
            mock_repo.get_issue.assert_called_once_with(123)
```

## Implementation Pattern to Follow

```python
@log_function_call
@_handle_github_errors(
    default_return=IssueData(
        number=0,
        title="",
        body="",
        state="",
        labels=[],
        user=None,
        created_at=None,
        updated_at=None,
        url="",
        locked=False,
    )
)
def get_issue(self, issue_number: int) -> IssueData:
    """Get issue data from GitHub.
    
    Args:
        issue_number: Issue number to fetch
        
    Returns:
        IssueData with issue information, or empty dict on error
        
    Raises:
        GithubException: For authentication or permission errors
    """
    # Validate and fetch following existing patterns
    # Convert PyGithub Issue to IssueData TypedDict
    # Return result
```
