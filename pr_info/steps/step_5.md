# Step 5: coordinator issue-stats Core Functions

## LLM Prompt
```
Implement Step 5 of Issue #340. Reference: pr_info/steps/summary.md

Create the core functions for the coordinator issue-stats command.
Migrate logic from workflows/issue_stats.py to the new CLI module.

Follow TDD: Write tests first, then implement.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/coordinator/test_issue_stats.py` | Create new |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | Create new |

---

## WHAT

### New File: `issue_stats.py`

```python
"""Issue statistics command for coordinator package."""

from typing import Any

from ....utils.github_operations.issue_manager import IssueData


def validate_issue_labels(
    issue: IssueData,
    valid_status_labels: set[str]
) -> tuple[bool, str]:
    """Validate that issue has exactly one valid status label.
    
    Returns:
        Tuple of (is_valid, error_type: "" | "no_status" | "multiple_status")
    """

def filter_ignored_issues(
    issues: list[IssueData],
    ignore_labels: list[str]
) -> list[IssueData]:
    """Filter out issues that have any of the ignored labels."""

def group_issues_by_category(
    issues: list[IssueData],
    labels_config: dict[str, Any]
) -> dict[str, dict[str, list[IssueData]]]:
    """Group issues by category and status label.
    
    Returns:
        Dict with keys: 'human_action', 'bot_pickup', 'bot_busy', 'errors'
    """

def display_statistics(
    grouped_issues: dict[str, dict[str, list[IssueData]]],
    labels_config: dict[str, Any],
    repo_url: str,
    filter_category: str = "all",
    show_details: bool = False
) -> None:
    """Display formatted statistics to console."""
```

### Test Classes

```python
class TestValidateIssueLabels:
    """Test validate_issue_labels function."""
    
    def test_single_valid_label_returns_valid(self) -> None: ...
    def test_no_label_returns_no_status(self) -> None: ...
    def test_multiple_labels_returns_multiple_status(self) -> None: ...


class TestFilterIgnoredIssues:
    """Test filter_ignored_issues function."""
    
    def test_empty_ignore_list_returns_all(self) -> None: ...
    def test_filters_issues_with_ignored_labels(self) -> None: ...


class TestGroupIssuesByCategory:
    """Test group_issues_by_category function."""
    
    def test_groups_by_human_action(self) -> None: ...
    def test_groups_by_bot_pickup(self) -> None: ...
    def test_groups_by_bot_busy(self) -> None: ...
    def test_groups_errors_separately(self) -> None: ...
    def test_includes_empty_labels_in_structure(self) -> None: ...


class TestDisplayStatistics:
    """Test display_statistics function."""
    
    def test_displays_all_categories(self, capsys) -> None: ...
    def test_filter_human_shows_only_human(self, capsys) -> None: ...
    def test_filter_bot_shows_pickup_and_busy(self, capsys) -> None: ...
    def test_details_mode_shows_issue_links(self, capsys) -> None: ...
```

---

## HOW

### Imports
```python
from typing import Any
from ....utils.github_operations.issue_manager import IssueData
```

### Test Fixtures (copy from existing test file)
```python
@pytest.fixture
def test_labels_config() -> dict[str, Any]:
    """Load test labels configuration."""
    config_path = Path(__file__).parent.parent.parent.parent / "workflows" / "config" / "test_labels.json"
    # ... load and return

@pytest.fixture  
def sample_issues() -> list[IssueData]:
    """Create sample issues for testing."""
    # ... create test data
```

---

## ALGORITHM

### validate_issue_labels
```
1. Filter issue labels to only those in valid_status_labels
2. If count == 0: return (False, "no_status")
3. If count > 1: return (False, "multiple_status")
4. Return (True, "")
```

### group_issues_by_category
```
1. Build label_to_category lookup from labels_config
2. Initialize result with empty dicts for each category
3. Initialize each label's list as empty in its category
4. For each issue:
5.   Validate labels, route to errors or appropriate category
6. Return grouped structure
```

### display_statistics
```
1. Determine categories_to_display based on filter_category
2. For each category:
3.   Print header, then each label with count
4.   If show_details: print issue links
5. Print validation errors section
6. Print totals line
```

---

## DATA

### GroupedIssues Structure
```python
{
    'human_action': {
        'status-01:created': [IssueData, ...],
        'status-04:plan-review': [],
        ...
    },
    'bot_pickup': {...},
    'bot_busy': {...},
    'errors': {
        'no_status': [IssueData, ...],
        'multiple_status': [IssueData, ...]
    }
}
```

---

## VERIFICATION

```bash
pytest tests/cli/commands/coordinator/test_issue_stats.py -v
```
