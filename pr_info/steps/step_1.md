# Step 1: Modify IssueData TypedDict

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 1: Modify the IssueData TypedDict to add the assignees field.

Requirements:
- Add assignees: List[str] field to IssueData TypedDict
- Field represents list of GitHub usernames assigned to work on the issue
- Maintain alphabetical field ordering in TypedDict
- No implementation code changes yet (only type definition)

Follow the summary document for architectural context.
```

## WHERE
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
**Lines**: ~25-39 (IssueData TypedDict definition)

## WHAT
Modify `IssueData` TypedDict class to include new field:

```python
class IssueData(TypedDict):
    """TypedDict for issue data structure."""
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    assignees: List[str]  # NEW FIELD
    user: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    url: str
    locked: bool
```

## HOW

### Integration Points
- Import: `from typing import List, Optional, TypedDict` (already exists)
- Used by: All methods returning `IssueData` in `IssueManager` class

### Field Ordering
Place `assignees` after `labels` to maintain logical grouping:
- Issue metadata (number, title, body, state)
- Categorization (labels, assignees)
- Audit trail (user, timestamps, url, locked)

## ALGORITHM
```
1. Locate IssueData TypedDict definition (line ~25)
2. Add field: assignees: List[str]
3. Position after labels field, before user field
4. Add docstring comment if needed
5. Verify syntax is valid TypedDict
```

## DATA

### Input
N/A (type definition only)

### Output
Modified TypedDict structure:
```python
IssueData = {
    "number": int,
    "title": str,
    "body": str,
    "state": str,
    "labels": List[str],
    "assignees": List[str],  # NEW
    "user": Optional[str],
    "created_at": Optional[str],
    "updated_at": Optional[str],
    "url": str,
    "locked": bool
}
```

## Verification
- Run mypy to verify TypedDict is valid
- No runtime tests yet (only type definition change)
