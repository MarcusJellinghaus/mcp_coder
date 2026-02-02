# Step 3: Validation and Staleness Detection in define-labels

## LLM Prompt
```
Implement Step 3 of Issue #340. Reference: pr_info/steps/summary.md

Add validation functions to detect:
1. Issues with multiple status labels (errors)
2. Stale bot_busy processes exceeding timeout (warnings)

Follow TDD: Write tests first, then implement.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_define_labels.py` | Add test classes |
| `src/mcp_coder/cli/commands/define_labels.py` | Add functions |

---

## WHAT

### New Functions in `define_labels.py`

```python
def calculate_elapsed_minutes(timestamp_str: str) -> int:
    """Calculate minutes elapsed since given ISO timestamp.
    
    Args:
        timestamp_str: ISO format timestamp (may have 'Z' suffix)
    Returns:
        Integer minutes elapsed
    """

def check_stale_bot_process(
    issue: IssueData,
    label_name: str,
    timeout_minutes: int,
    issue_manager: IssueManager
) -> tuple[bool, int | None]:
    """Check if a bot_busy label has exceeded its timeout threshold.
    
    Returns:
        Tuple of (is_stale, elapsed_minutes or None if not found)
    """

def validate_issues(
    issues: list[IssueData],
    labels_config: dict[str, Any],
    issue_manager: IssueManager,
    dry_run: bool = False
) -> ValidationResults:
    """Validate all issues for errors and warnings.
    
    Returns:
        ValidationResults with errors, warnings, ok lists
    """
```

### Type Definition
```python
from typing import TypedDict

class ValidationResults(TypedDict):
    initialized: list[int]
    errors: list[dict[str, Any]]      # {'issue': int, 'labels': list[str]}
    warnings: list[dict[str, Any]]    # {'issue': int, 'label': str, 'elapsed': int, 'threshold': int}
    ok: list[int]
    skipped: int
```

### Test Classes

```python
class TestCalculateElapsedMinutes:
    """Test calculate_elapsed_minutes function."""
    
    def test_calculates_minutes_from_iso_timestamp(self) -> None: ...
    def test_handles_z_suffix(self) -> None: ...
    def test_handles_timezone_offset(self) -> None: ...


class TestCheckStaleBotProcess:
    """Test check_stale_bot_process function."""
    
    def test_returns_false_when_under_threshold(self) -> None: ...
    def test_returns_true_when_over_threshold(self) -> None: ...
    def test_returns_none_when_no_labeled_event(self) -> None: ...


class TestValidateIssues:
    """Test validate_issues function."""
    
    def test_detects_multiple_status_labels_as_errors(self) -> None: ...
    def test_detects_stale_bot_process_as_warning(self) -> None: ...
    def test_marks_valid_issues_as_ok(self) -> None: ...
    def test_skips_staleness_check_in_dry_run(self) -> None: ...
```

---

## HOW

### Imports to Add
```python
from datetime import datetime, timezone
```

### Integration Points
- `check_stale_bot_process` uses `issue_manager.get_issue_events()`
- `validate_issues` uses `build_label_lookups()` for category mapping
- Timeout values come from `labels_config["workflow_labels"][i]["stale_timeout_minutes"]`

---

## ALGORITHM

### calculate_elapsed_minutes
```
1. Replace 'Z' suffix with '+00:00'
2. Parse ISO timestamp with fromisoformat()
3. Get current UTC time
4. Return (now - timestamp).total_seconds() / 60 as int
```

### check_stale_bot_process
```
1. Get events for issue via issue_manager.get_issue_events()
2. Filter to "labeled" events matching label_name
3. If no events found, return (False, None)
4. Find most recent event by created_at
5. Calculate elapsed = calculate_elapsed_minutes(event.created_at)
6. Return (elapsed > timeout_minutes, elapsed)
```

### validate_issues
```
1. Build label lookups (name_to_category, name_to_timeout)
2. For each issue:
3.   count, labels = check_status_labels(issue)
4.   If count > 1: add to errors
5.   If count == 1 and category == "bot_busy" and not dry_run:
6.     Check staleness, add to warnings if stale
7.   Else: add to ok
8. Return ValidationResults
```

---

## DATA

### ValidationResults Example
```python
{
    'initialized': [12, 45],
    'errors': [
        {'issue': 23, 'labels': ['status-01:created', 'status-03:planning']}
    ],
    'warnings': [
        {'issue': 78, 'label': 'status-06:implementing', 'elapsed': 150, 'threshold': 120}
    ],
    'ok': [1, 2, 3, 5, 6],
    'skipped': 2
}
```

---

## VERIFICATION

```bash
pytest tests/cli/commands/test_define_labels.py::TestCalculateElapsedMinutes -v
pytest tests/cli/commands/test_define_labels.py::TestCheckStaleBotProcess -v
pytest tests/cli/commands/test_define_labels.py::TestValidateIssues -v
```
