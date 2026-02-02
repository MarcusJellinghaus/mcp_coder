# Step 2: Issue Initialization in define-labels

## LLM Prompt
```
Implement Step 2 of Issue #340. Reference: pr_info/steps/summary.md

Add issue initialization functionality to define-labels command.
Issues without any workflow status label should be initialized with `status-01:created`.
Dry-run mode should preview but not apply changes.

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
def check_status_labels(
    issue: IssueData,
    workflow_label_names: set[str]
) -> tuple[int, list[str]]:
    """Check how many workflow status labels an issue has.
    
    Returns:
        Tuple of (count, list_of_status_labels)
    """

def initialize_issues(
    issues: list[IssueData],
    workflow_label_names: set[str],
    created_label_name: str,
    issue_manager: IssueManager,
    dry_run: bool = False
) -> list[int]:
    """Initialize issues without status labels.
    
    Returns:
        List of issue numbers that were (or would be) initialized
    """
```

### Test Classes

```python
class TestCheckStatusLabels:
    """Test check_status_labels function."""
    
    def test_no_status_labels_returns_zero(self) -> None: ...
    def test_single_status_label_returns_one(self) -> None: ...
    def test_multiple_status_labels_returns_count(self) -> None: ...
    def test_ignores_non_workflow_labels(self) -> None: ...


class TestInitializeIssues:
    """Test initialize_issues function."""
    
    def test_initializes_issues_without_labels(self) -> None: ...
    def test_skips_issues_with_labels(self) -> None: ...
    def test_dry_run_does_not_call_api(self) -> None: ...
    def test_returns_initialized_issue_numbers(self) -> None: ...
```

---

## HOW

### Imports to Add
```python
from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.github_operations.label_config import build_label_lookups
```

### Integration Points
- Called from `execute_define_labels()` after label sync
- Uses `IssueManager.add_labels()` for applying labels
- Uses `build_label_lookups()` to get workflow label names

---

## ALGORITHM

### check_status_labels
```
1. Get issue's labels list
2. Filter to only labels in workflow_label_names set
3. Return (len(filtered), filtered_list)
```

### initialize_issues
```
1. For each issue in issues:
2.   count, _ = check_status_labels(issue, workflow_label_names)
3.   If count == 0:
4.     If not dry_run: issue_manager.add_labels(issue_number, created_label_name)
5.     Add issue_number to initialized list
6. Return initialized list
```

---

## DATA

### Input
- `issues: list[IssueData]` - Open issues from repository
- `workflow_label_names: set[str]` - All valid status label names
- `created_label_name: str` - Typically `"status-01:created"`

### Output
- `list[int]` - Issue numbers that were initialized

---

## VERIFICATION

```bash
pytest tests/cli/commands/test_define_labels.py::TestCheckStatusLabels -v
pytest tests/cli/commands/test_define_labels.py::TestInitializeIssues -v
```
