# Step 5: coordinator issue-stats Core Functions

## LLM Prompt
```
Implement Step 5 of Issue #340. Reference: pr_info/steps/summary.md

Move the core functions from workflows/issue_stats.py to coordinator/issue_stats.py.
Update imports and verify existing tests pass with new paths.

Approach: Move existing tested code rather than rewriting.
```

---

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | Create new (move functions from workflows/) |
| `tests/cli/commands/coordinator/test_issue_stats.py` | Create new (move tests from workflows/) |

### Source Files (to move from)
| Source | Destination |
|--------|-------------|
| `workflows/issue_stats.py` | `src/mcp_coder/cli/commands/coordinator/issue_stats.py` |
| `tests/workflows/test_issue_stats.py` | `tests/cli/commands/coordinator/test_issue_stats.py` |

---

## WHAT

### Move Functions from `workflows/issue_stats.py`

The following functions already exist and are tested. Move them to the new location:

```python
# Functions to move (preserve signatures and implementation)
validate_issue_labels(issue, valid_status_labels) -> tuple[bool, str]
filter_ignored_issues(issues, ignore_labels) -> list[IssueData]
group_issues_by_category(issues, labels_config) -> dict
display_statistics(grouped, labels_config, repo_url, filter_category, show_details) -> None
format_issue_line(issue, repo_url, max_title_length) -> str
truncate_title(title, max_length) -> str
```

### Test Classes

Move existing tests from `tests/workflows/test_issue_stats.py`. The file contains 50+ tests covering:
- `TestValidateIssueLabels` - validation logic
- `TestFilterIgnoredIssues` - ignore label filtering  
- `TestGroupIssuesByCategory` - category grouping
- `TestDisplayStatistics` - output formatting
- Argument parsing tests
- Integration tests

**Update imports from:**
```python
from workflows.issue_stats import ...
```

**To:**
```python
from mcp_coder.cli.commands.coordinator.issue_stats import ...
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
