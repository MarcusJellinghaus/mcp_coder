# Step 1: Extend IssueManager with Events API Support

## Goal
Add event timeline retrieval capability to `IssueManager` class to support stale bot process detection.

## Context
The GitHub Issues API provides an events timeline that tracks when labels were added/removed. We need this to detect how long an issue has been in a bot_busy state (planning, implementing, pr_creating).

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`

## WHAT

### New Enum for Event Types
```python
class IssueEventType(str, Enum):
    """Enum for GitHub issue event types."""
    # Label events
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    
    # State events
    CLOSED = "closed"
    REOPENED = "reopened"
    
    # Assignment events
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    
    # Milestone events
    MILESTONED = "milestoned"
    DEMILESTONED = "demilestoned"
    
    # Reference events
    REFERENCED = "referenced"
    CROSS_REFERENCED = "cross-referenced"
    
    # Interaction events
    COMMENTED = "commented"
    MENTIONED = "mentioned"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    
    # Title/Lock events
    RENAMED = "renamed"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    
    # PR-specific events (included for completeness)
    REVIEW_REQUESTED = "review_requested"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    CONVERTED_TO_DRAFT = "converted_to_draft"
    READY_FOR_REVIEW = "ready_for_review"
```

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
def get_issue_events(
    self, 
    issue_number: int,
    filter_by_type: Optional[IssueEventType] = None
) -> List[EventData]:
    """Get timeline events for an issue.
    
    Args:
        issue_number: Issue number to get events for
        filter_by_type: Optional event type to filter by (e.g., IssueEventType.LABELED)
                       If None, returns all event types
        
    Returns:
        List of EventData dicts with event information
        
    Raises:
        GithubException: For authentication, permission, or API errors
        
    Note:
        Returns ALL event types by default. Currently, the validation workflow
        only uses label events (labeled/unlabeled), but other event types are
        available for future use.
        
    Example:
        >>> # Get all events
        >>> events = manager.get_issue_events(123)
        >>> # Get only labeled events
        >>> labeled = manager.get_issue_events(123, IssueEventType.LABELED)
        >>> for event in labeled:
        ...     print(f"Label '{event['label']}' added at {event['created_at']}")
    """
```

## HOW

### Integration Points
- **Decorators**: Use existing `@log_function_call` only (no error handler - let exceptions propagate)
- **Imports**: Add `from enum import Enum` to imports, already have `List`, `Optional`, `TypedDict`
- **Pattern**: Follow same validation pattern as existing methods
- **Error Handling**: Unlike other methods, this one raises on API errors per Decision #1

### Location in File
- Add `IssueEventType` enum after imports, before TypedDicts (around line 50)
- Add `EventData` TypedDict after `LabelData` (around line 90)
- Add `get_issue_events()` method at end of class (after `set_labels()`)

## ALGORITHM

```python
# 1. Validate issue_number using existing _validate_issue_number()
# 2. Get repository using existing _get_repository()
# 3. Get issue: github_issue = repo.get_issue(issue_number)
# 4. Get events: github_events = github_issue.get_events()
# 5. Loop through events, convert to EventData:
#    - For each event, extract event type
#    - If filter_by_type is provided:
#      * Skip event if event.event != filter_by_type.value
#    - Extract label name for labeled/unlabeled events (event.label.name if exists)
#    - For other events, set label field to None
#    - Format timestamp to ISO string (event.created_at.isoformat())
#    - Extract actor username (event.actor.login if exists)
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
- Add `from enum import Enum` to imports
- Add IssueEventType enum after imports, before TypedDicts (around line 50)
- Add EventData TypedDict after LabelData (around line 90)
- Add get_issue_events() method at end of IssueManager class
- Method signature: get_issue_events(self, issue_number: int, filter_by_type: Optional[IssueEventType] = None)
- Follow existing patterns: use @log_function_call decorator, validation
- Note: No @_handle_github_errors decorator - exceptions should propagate (see Decisions.md #1 and #18)
- Implement filtering logic if filter_by_type is provided
- Use PyGithub's issue.get_events() API
- Add unit tests to tests/utils/github_operations/test_issue_manager.py

After implementation:
1. Run quality checks: pylint, pytest, mypy
2. Fix any issues found
3. Provide commit message
```

## Definition of Done
- [ ] IssueEventType enum added with all ~22 event types
- [ ] EventData TypedDict added with proper fields
- [ ] get_issue_events() method implemented with filter_by_type parameter
- [ ] Method follows existing validation patterns
- [ ] Filtering logic works correctly when filter_by_type is provided
- [ ] Unit tests added and passing (including filter tests)
- [ ] All quality checks pass (pylint, pytest, mypy)
- [ ] Code properly documented with docstrings
