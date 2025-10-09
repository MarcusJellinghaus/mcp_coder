# Step 2: Implement get_issue() Method and Update Existing Methods

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 2: Add get_issue() method and unit test.

Requirements:
- Write unit test: test_get_issue_success() - Mock successful retrieval with assignees
- Implement get_issue() method after create_issue() in IssueManager
- Follow existing patterns (decorators, validation, error handling)
- Map GitHub Issue object to IssueData, including assignees from API response

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

### Unit Test
```python
def test_get_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
    """Test successful issue retrieval with assignees."""
```

### get_issue() Implementation
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

### Integration Points
- Mock GitHub API Issue object with assignees list
- Use existing decorators: `@log_function_call`, `@_handle_github_errors`
- Use existing helpers: `_validate_issue_number()`, `_get_repository()`
- Map `github_issue.assignees` to list of usernames

## Example Implementation Pattern
```python
assignees=[assignee.login for assignee in github_issue.assignees],
```

## Verification
1. Run pytest: test_get_issue_success should pass
2. Verify mypy type checking passes
3. Check existing method tests still pass
