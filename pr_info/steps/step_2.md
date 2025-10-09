# Step 2: Implement get_issue() Method and Update Existing Methods

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 2: Add get_issue() method and update existing methods to include assignees field.

Part A - Write Unit Test:
- test_get_issue_success() - Mock successful retrieval with assignees

Part B - Implement get_issue() Method:
- Add get_issue() method after create_issue() in IssueManager
- Follow existing patterns (decorators, validation, error handling)
- Map GitHub Issue object to IssueData with assignees

Part C - Update Existing Methods:
- Add assignees=[] to IssueData returns in 6 existing methods:
  - create_issue()
  - close_issue()
  - reopen_issue()
  - add_labels()
  - remove_labels()
  - set_labels()

Follow the summary document for architectural context.
```

## WHERE

### Test
**File**: `tests/utils/github_operations/test_issue_manager.py`
**Location**: After existing test methods, before end of TestIssueManagerUnit class

### Implementation
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
**Locations**: 
- New method after `create_issue()` (line ~150)
- Updates to 6 existing methods throughout file

## WHAT

### Part A: Unit Test
```python
def test_get_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
    """Test successful issue retrieval with assignees."""
```

### Part B: get_issue() Implementation
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

### Part C: Update Existing Methods
Add to all IssueData returns:
```python
assignees=[assignee.login for assignee in github_issue.assignees],
```

## HOW

### Integration Points - Test
- Mock decorators: `@patch("mcp_coder.utils.github_operations.base_manager.Github")`
- Mock GitHub API responses for Issue object
- Mock assignees as list of user objects with `.login` attribute

### Integration Points - Implementation
- **get_issue()**: Use `@log_function_call`, `@_handle_github_errors`, `_validate_issue_number()`, `_get_repository()`
- **Existing methods**: Add assignees list comprehension after labels (follow same pattern)

## ALGORITHM

### Test Setup
```
1. Create mock GitHub Issue object with assignees
2. Mock issue.assignees as list with login attributes
3. Mock repo.get_issue() to return mock issue
4. Call manager.get_issue(issue_number)
5. Assert all fields including assignees list
```

### get_issue() Implementation
```
1. Validate issue_number (return empty if invalid)
2. Get repository (return empty if None)
3. Call repo.get_issue(issue_number)
4. Map issue.assignees to list of usernames
5. Return IssueData with all fields including assignees
```

### Existing Methods Update
```
For each of 6 methods:
1. Locate the IssueData return statement
2. Add assignees line after labels
3. Use same list comprehension pattern
```

## DATA

### Test Mock Data
```python
mock_assignee1.login = "user1"
mock_assignee2.login = "user2"
mock_issue.assignees = [mock_assignee1, mock_assignee2]
```

### get_issue() Return
```python
IssueData(
    number=123,
    title="Test Issue",
    body="Description",
    state="open",
    labels=["bug"],
    assignees=["user1", "user2"],
    user="creator",
    created_at="2023-01-01T00:00:00Z",
    updated_at="2023-01-01T00:00:00Z",
    url="https://github.com/test/repo/issues/123",
    locked=False
)
```

### Updated Pattern for Existing Methods
```python
return IssueData(
    number=github_issue.number,
    title=github_issue.title,
    body=github_issue.body or "",
    state=github_issue.state,
    labels=[label.name for label in github_issue.labels],
    assignees=[assignee.login for assignee in github_issue.assignees],  # ADD
    user=github_issue.user.login if github_issue.user else None,
    created_at=(
        github_issue.created_at.isoformat() if github_issue.created_at else None
    ),
    updated_at=(
        github_issue.updated_at.isoformat() if github_issue.updated_at else None
    ),
    url=github_issue.html_url,
    locked=github_issue.locked,
)
```

## Verification
1. Run pytest: test_get_issue_success should pass
2. Verify mypy type checking passes
3. Check existing method tests still pass
