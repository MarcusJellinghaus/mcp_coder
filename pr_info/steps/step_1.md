# Step 1: Extend IssueManager with Events API Support

## Goal
Add event timeline retrieval capability to `IssueManager` class to support stale bot process detection.

## Context
The GitHub Issues API provides an events timeline that tracks when labels were added/removed. We need this to detect how long an issue has been in a bot_busy state (planning, implementing, pr_creating).

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`

## WHAT

### New TypedDict
```python
class EventData(TypedDict):
    """TypedDict for issue event data structure."""
    event: str           # Event type (e.g., "labeled", "unlabeled")
    label: Optional[str] # Label name (for label events)
    created_at: str      # ISO format timestamp
    actor: Optional[str] # GitHub username who performed action
```

### New Method
```python
@log_function_call
def get_issue_events(self, issue_number: int) -> List[EventData]:
    """Get timeline events for an issue.
    
    Args:
        issue_number: Issue number to get events for
        
    Returns:
        List of EventData dicts with event information
        
    Raises:
        GithubException: For authentication, permission, or API errors
        
    Example:
        >>> events = manager.get_issue_events(123)
        >>> for event in events:
        ...     if event['event'] == 'labeled':
        ...         print(f"Label '{event['label']}' added at {event['created_at']}")
    """
```

## HOW

### Integration Points
- **Decorators**: Use existing `@log_function_call` only (no error handler - let exceptions propagate)
- **Imports**: Already have `List`, `Optional`, `TypedDict` imports
- **Pattern**: Follow same validation pattern as existing methods
- **Error Handling**: Unlike other methods, this one raises on API errors per Decision #1

### Location in File
- Add `EventData` TypedDict after `LabelData` (around line 70)
- Add `get_issue_events()` method at end of class (after `set_labels()`)

## ALGORITHM

```python
# 1. Validate issue_number using existing _validate_issue_number()
# 2. Get repository using existing _get_repository()
# 3. Get issue: github_issue = repo.get_issue(issue_number)
# 4. Get events: github_events = github_issue.get_events()
# 5. Loop through events, convert to EventData:
#    - Only include events with event type
#    - Extract label name for labeled/unlabeled events
#    - Format timestamp to ISO string
#    - Extract actor username
# 6. Return list of EventData dicts
```

## DATA

### Return Structure
```python
[
    {
        "event": "labeled",
        "label": "status-03:planning",
        "created_at": "2025-10-14T10:30:00Z",
        "actor": "octocat"
    },
    {
        "event": "commented",
        "label": None,
        "created_at": "2025-10-14T10:31:00Z", 
        "actor": "user123"
    }
]
```

## Tests to Write

**File**: `tests/utils/github_operations/test_issue_manager.py`

Add test cases:
```python
def test_get_issue_events_success(mock_github_manager):
    """Test successful event retrieval"""
    
def test_get_issue_events_invalid_issue_number(mock_github_manager):
    """Test with invalid issue number returns empty list"""
    
def test_get_issue_events_filter_label_events(mock_github_manager):
    """Test that labeled/unlabeled events include label names"""
```

## LLM Prompt for Implementation

```
Please implement Step 1 from pr_info/steps/step_1.md

Review the summary at pr_info/steps/summary.md for context.

Key requirements:
- Add EventData TypedDict after LabelData around line 70
- Add get_issue_events() method at end of IssueManager class
- Follow existing patterns: use @log_function_call decorator, validation
- Note: No @_handle_github_errors decorator - exceptions should propagate (see Decisions.md)
- Use PyGithub's issue.get_events() API
- Add unit tests to tests/utils/github_operations/test_issue_manager.py

After implementation:
1. Run quality checks: pylint, pytest, mypy
2. Fix any issues found
3. Provide commit message
```

## Definition of Done
- [ ] EventData TypedDict added with proper fields
- [ ] get_issue_events() method implemented with decorators
- [ ] Method follows existing validation patterns
- [ ] Unit tests added and passing
- [ ] All quality checks pass (pylint, pytest, mypy)
- [ ] Code properly documented with docstrings
