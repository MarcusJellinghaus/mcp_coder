# Step 2: Implement get_issue() Method (TDD)

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 2: Add get_issue() method to IssueManager using Test-Driven Development.

Part A - Write Unit Tests First:
1. test_get_issue_success() - Mock successful retrieval with assignees
2. test_get_issue_invalid_number() - Test validation (0, -1)
3. test_get_issue_auth_error_raises() - Test auth errors (401, 403)

Part B - Implement Method:
1. Add get_issue() method after create_issue() in IssueManager
2. Follow existing patterns (decorators, validation, error handling)
3. Map GitHub Issue object to IssueData with assignees

Follow the summary document for architectural context.
```

## WHERE

### Tests
**File**: `tests/utils/github_operations/test_issue_manager.py`
**Location**: After existing test methods, before end of TestIssueManagerUnit class

### Implementation
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
**Location**: After `create_issue()` method (line ~150)

## WHAT

### Part A: Unit Tests
```python
def test_get_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
    """Test successful issue retrieval with assignees."""

def test_get_issue_invalid_number(self, tmp_path: Path) -> None:
    """Test getting issue with invalid number."""

def test_get_issue_auth_error_raises(self, mock_github: Mock, tmp_path: Path) -> None:
    """Test that auth errors are raised for get_issue."""
```

### Part B: Implementation
```python
@log_function_call
@_handle_github_errors(
    default_return=IssueData(
        number=0,
        title="",
        body="",
        state="",
        labels=[],
        assignees=[],
        user=None,
        created_at=None,
        updated_at=None,
        url="",
        locked=False,
    )
)
def get_issue(self, issue_number: int) -> IssueData:
    """Retrieve issue details by number."""
```

## HOW

### Integration Points - Tests
- Mock decorators: `@patch("mcp_coder.utils.github_operations.base_manager.Github")`
- Mock GitHub API responses for Issue object
- Mock assignees as list of user objects with `.login` attribute

### Integration Points - Implementation
- Decorators: `@log_function_call`, `@_handle_github_errors`
- Validation: Use existing `_validate_issue_number()`
- Repository: Use existing `_get_repository()`
- API call: `repo.get_issue(issue_number)`

## ALGORITHM

### Test Setup
```
1. Create mock GitHub Issue object with assignees
2. Mock issue.assignees as list with login attributes
3. Mock repo.get_issue() to return mock issue
4. Call manager.get_issue(issue_number)
5. Assert all fields including assignees list
```

### Implementation Logic
```
1. Validate issue_number (return empty if invalid)
2. Get repository (return empty if None)
3. Call repo.get_issue(issue_number)
4. Map issue.assignees to list of usernames
5. Return IssueData with all fields including assignees
```

## DATA

### Test Mock Data
```python
mock_assignee1.login = "user1"
mock_assignee2.login = "user2"
mock_issue.assignees = [mock_assignee1, mock_assignee2]
```

### Method Return
```python
IssueData(
    number=123,
    title="Test Issue",
    body="Description",
    state="open",
    labels=["bug"],
    assignees=["user1", "user2"],  # NEW
    user="creator",
    created_at="2023-01-01T00:00:00Z",
    updated_at="2023-01-01T00:00:00Z",
    url="https://github.com/test/repo/issues/123",
    locked=False
)
```

### Error Cases
- Invalid number (0, -1): Returns empty IssueData with number=0
- Auth error (401, 403): Raises GithubException
- Not found (404): Returns empty IssueData with number=0

## TDD Verification Steps
1. Write all 3 unit tests first
2. Run tests - they should FAIL (method doesn't exist yet)
3. Implement get_issue() method
4. Run tests - they should PASS
5. Verify with pytest: `-k test_get_issue`
