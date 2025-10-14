# Step 3: Implement Core Validation Logic

## Goal
Implement the three core validation functions that detect label issues: missing status labels, duplicate status labels, and stale bot processes.

## Context
These are the heart of the validation system. Each function should be simple, focused, and testable. They process individual issues and return structured results.

## WHERE
**File**: `workflows/validate_labels.py`

## WHAT

### Function 1: Build Label Lookup
```python
def build_label_lookups(labels_config: Dict[str, Any]) -> tuple[
    dict[str, str],           # internal_id -> label_name
    set[str],                 # All workflow label names
    dict[str, str],           # label_name -> category
    dict[str, str]            # label_name -> internal_id
]:
    """Build lookup dictionaries from label configuration.
    
    Args:
        labels_config: Loaded label configuration from JSON
        
    Returns:
        Tuple of (id_to_name, all_names, name_to_category, name_to_id)
    """
```

### Function 2: Check Status Labels
```python
def check_status_labels(
    issue: IssueData,
    workflow_label_names: set[str]
) -> tuple[int, list[str]]:
    """Check how many workflow status labels an issue has.
    
    Args:
        issue: Issue data from IssueManager
        workflow_label_names: Set of all valid workflow label names
        
    Returns:
        Tuple of (count, list_of_status_labels)
        
    Example:
        >>> count, labels = check_status_labels(issue, workflow_names)
        >>> if count == 0:
        ...     print("Issue needs initialization")
        >>> elif count > 1:
        ...     print(f"ERROR: Multiple labels: {labels}")
    """
```

### Function 3: Check Stale Bot Process
```python
def check_stale_bot_process(
    issue: IssueData,
    label_name: str,
    internal_id: str,
    issue_manager: IssueManager
) -> tuple[bool, Optional[int]]:
    """Check if a bot_busy label has exceeded its timeout threshold.
    
    Args:
        issue: Issue data
        label_name: The bot_busy label name to check
        internal_id: The internal_id of the label (for timeout lookup)
        issue_manager: IssueManager instance for API calls
        
    Returns:
        Tuple of (is_stale, elapsed_minutes)
        - is_stale: True if label exceeded timeout
        - elapsed_minutes: Minutes since label was applied, or None if not found
        
    Algorithm:
        1. Get events for issue via issue_manager.get_issue_events()
        2. Filter to "labeled" events with matching label_name
        3. Find most recent such event
        4. Calculate elapsed time from event timestamp to now
        5. Compare against STALE_TIMEOUTS[internal_id]
        6. Return (is_stale, elapsed_minutes)
    """
```

### Function 4: Process All Issues
```python
def process_issues(
    issues: List[IssueData],
    labels_config: Dict[str, Any],
    issue_manager: IssueManager,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Process all issues and collect validation results.
    
    Args:
        issues: List of issues to process
        labels_config: Label configuration
        issue_manager: IssueManager for API operations
        dry_run: If True, don't make any changes
        
    Returns:
        Results dictionary with structure:
        {
            "processed": 123,
            "skipped": 5,
            "initialized": [issue_numbers],
            "errors": [{"issue": 45, "labels": ["label1", "label2"]}],
            "warnings": [{"issue": 67, "label": "planning", "elapsed": 20}],
            "ok": [issue_numbers]
        }
    """
```

## HOW

### Integration Points
- **DateTime handling**: Use `datetime.fromisoformat()` and `datetime.now(timezone.utc)`
- **Filtering**: Use `labels_config.get("ignore_labels", [])` to filter issues
- **Label operations**: Use `issue_manager.add_labels()` for initialization (unless dry_run)

## ALGORITHM

### build_label_lookups()
```python
# 1. Initialize empty dicts and set
# 2. Loop through labels_config["workflow_labels"]
# 3. For each label, populate all lookup structures
# 4. Return tuple of lookups
```

### check_status_labels()
```python
# 1. Get issue["labels"] list
# 2. Filter to only those in workflow_label_names
# 3. Return (len(status_labels), status_labels)
```

### check_stale_bot_process()
```python
# 1. Check if internal_id in STALE_TIMEOUTS, return (False, None) if not
# 2. Get events: issue_manager.get_issue_events(issue["number"])
# 3. Filter events: event["event"] == "labeled" AND event["label"] == label_name
# 4. Find most recent: max(filtered, key=lambda e: e["created_at"])
# 5. Parse timestamp: datetime.fromisoformat(event["created_at"])
# 6. Calculate elapsed: (datetime.now(timezone.utc) - timestamp).total_seconds() / 60
# 7. Check stale: elapsed > STALE_TIMEOUTS[internal_id]
# 8. Return (is_stale, int(elapsed))
```

### process_issues()
```python
# 1. Build label lookups
# 2. Filter ignored issues (any with ignore_labels)
# 3. Initialize results dict
# 4. Loop through filtered issues:
#    a. Check status labels count
#    b. If 0: initialize with "created" (unless dry_run), log, record
#    c. If 1: check if bot_busy, then check stale, log, record
#    d. If 2+: log ERROR, record
#    e. Log per-issue status
# 5. Return results dict
```

## DATA

### Results Structure
```python
{
    "processed": 47,           # Total issues processed
    "skipped": 3,              # Issues with ignore labels
    "initialized": [12, 45],   # Issue numbers that got "created" label
    "errors": [                # Issues with multiple status labels
        {"issue": 23, "labels": ["status-01:created", "status-03:planning"]},
        {"issue": 56, "labels": ["status-04:plan-review", "status-06:implementing"]}
    ],
    "warnings": [              # Stale bot processes
        {"issue": 78, "label": "status-03:planning", "elapsed": 20}
    ],
    "ok": [1, 2, 3, 5, 7]     # Issue numbers that are valid
}
```

## Tests to Write

**File**: `tests/workflows/test_validate_labels.py`

Add comprehensive tests:
```python
def test_build_label_lookups():
    """Test building lookup dictionaries from config"""
    
def test_check_status_labels_none():
    """Test issue with no status labels"""
    
def test_check_status_labels_one():
    """Test issue with one status label"""
    
def test_check_status_labels_multiple():
    """Test issue with multiple status labels"""
    
def test_check_stale_bot_process_not_stale():
    """Test bot process within timeout"""
    
def test_check_stale_bot_process_is_stale():
    """Test bot process exceeding timeout"""
    
def test_check_stale_bot_process_no_events():
    """Test when no label events found"""
    
def test_process_issues_mixed_scenarios(mock_issue_manager):
    """Test processing issues with various validation states"""
    
def test_process_issues_dry_run(mock_issue_manager):
    """Test dry-run doesn't make API calls"""
    
def test_process_issues_with_ignore_labels():
    """Test filtering of ignored issues"""
```

## LLM Prompt for Implementation

```
Please implement Step 3 from pr_info/steps/step_3.md

Review the summary at pr_info/steps/summary.md for context.

Key requirements:
- Implement build_label_lookups() to create lookup structures
- Implement check_status_labels() to count workflow labels
- Implement check_stale_bot_process() with event timeline checking
- Implement process_issues() to orchestrate validation
- Use datetime with timezone.utc for time calculations
- Follow existing patterns from issue_stats.py for filtering
- Add comprehensive unit tests with mocking

After implementation:
1. Run quality checks: pylint, pytest, mypy
2. Fix any issues found
3. Verify all edge cases are handled (no events, no labels, etc.)
4. Provide commit message
```

## Definition of Done
- [ ] build_label_lookups() implemented and tested
- [ ] check_status_labels() implemented and tested
- [ ] check_stale_bot_process() implemented with proper datetime handling
- [ ] process_issues() implemented with filtering and API calls
- [ ] Dry-run mode properly prevents API calls
- [ ] All unit tests passing with good coverage
- [ ] Edge cases handled (no events, no labels, etc.)
- [ ] All quality checks pass (pylint, pytest, mypy)
