# Step 2: Update issues.py - Numeric Prefix Sorting

## LLM Prompt

```
Implement Step 2 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Replace VSCODECLAUDE_PRIORITY constant with numeric prefix extraction for sorting.

Requirements:
- Remove import of VSCODECLAUDE_PRIORITY from types.py
- Extract priority from label names using regex r'status-(\d+):'
- Sort descending (higher number = higher priority = later stages first)
- Maintain identical sorting behavior (status-10 > status-07 > status-04 > status-01)
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | MODIFY - Replace sorting logic |
| `tests/workflows/vscodeclaude/test_issues.py` | MODIFY - Update/add sorting tests |

## WHAT

### Function Changes

**Remove:**
```python
from .types import VSCODECLAUDE_PRIORITY
```

**Add:**
```python
import re
```

**Modify:** `_filter_eligible_vscodeclaude_issues()` sorting logic

### Function Signature (unchanged)
```python
def _filter_eligible_vscodeclaude_issues(
    all_issues: list[IssueData],
    github_username: str,
) -> list[IssueData]:
```

## HOW

### Integration Points
- Function signature unchanged - no impact on callers
- Behavior unchanged - same sorting order

### Imports
```python
import re  # Add at top of file
# Remove: from .types import VSCODECLAUDE_PRIORITY
```

## ALGORITHM

```python
def _get_status_priority(label: str) -> int:
    """Extract numeric priority from status label (higher = more priority)."""
    match = re.search(r'status-(\d+):', label)
    return int(match.group(1)) if match else 0

# In sorting:
# Sort by priority descending (higher number = higher priority)
eligible_issues.sort(key=lambda issue: max(
    (_get_status_priority(label) for label in issue["labels"]),
    default=0
), reverse=True)
```

## DATA

### Input
Issues with labels like `["status-07:code-review"]`, `["status-01:created"]`

### Output
Same as before - issues sorted with later stages first:
1. `status-10:pr-created` (priority 10)
2. `status-07:code-review` (priority 7)
3. `status-04:plan-review` (priority 4)
4. `status-01:created` (priority 1)

## TEST IMPLEMENTATION

### File: `tests/workflows/vscodeclaude/test_issues.py`

**Add new test class for priority extraction:**

```python
class TestNumericPriorityExtraction:
    """Test numeric priority extraction from status labels."""

    def test_extracts_priority_from_standard_labels(self) -> None:
        """Extracts numeric priority from status-NN:name format."""
        from mcp_coder.workflows.vscodeclaude.issues import _get_status_priority
        
        assert _get_status_priority("status-10:pr-created") == 10
        assert _get_status_priority("status-07:code-review") == 7
        assert _get_status_priority("status-04:plan-review") == 4
        assert _get_status_priority("status-01:created") == 1

    def test_returns_zero_for_non_status_labels(self) -> None:
        """Returns 0 for labels that don't match pattern."""
        from mcp_coder.workflows.vscodeclaude.issues import _get_status_priority
        
        assert _get_status_priority("bug") == 0
        assert _get_status_priority("priority-high") == 0
        assert _get_status_priority("Overview") == 0
        assert _get_status_priority("") == 0
```

**Update existing sorting test to not rely on VSCODECLAUDE_PRIORITY:**

The existing `test_get_eligible_issues_priority_order` test should continue to work unchanged - it tests behavior, not implementation.

## FULL CODE CHANGE

### issues.py - Replace sorting section

**Before:**
```python
from .types import VSCODECLAUDE_PRIORITY

# ... in _filter_eligible_vscodeclaude_issues():

    # Sort by VSCODECLAUDE_PRIORITY (lower index = higher priority)
    priority_map = {label: i for i, label in enumerate(VSCODECLAUDE_PRIORITY)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        return len(VSCODECLAUDE_PRIORITY)  # Lowest priority

    eligible_issues.sort(key=get_priority)
```

**After:**
```python
import re

# ... add helper function at module level:

def _get_status_priority(label: str) -> int:
    """Extract numeric priority from status label.
    
    Args:
        label: Label name like "status-07:code-review"
        
    Returns:
        Numeric priority (e.g., 7) or 0 if not a status label
    """
    match = re.search(r'status-(\d+):', label)
    return int(match.group(1)) if match else 0

# ... in _filter_eligible_vscodeclaude_issues():

    # Sort by numeric prefix descending (higher number = higher priority)
    def get_issue_priority(issue: IssueData) -> int:
        """Get max priority from issue's status labels."""
        return max(
            (_get_status_priority(label) for label in issue["labels"]),
            default=0
        )

    eligible_issues.sort(key=get_issue_priority, reverse=True)
```

## VERIFICATION

After implementation:
1. Run sorting tests: `pytest tests/workflows/vscodeclaude/test_issues.py -v -k "priority"`
2. Run all issue tests: `pytest tests/workflows/vscodeclaude/test_issues.py -v`
3. Verify identical behavior: issues should sort status-10 > status-07 > status-04 > status-01
