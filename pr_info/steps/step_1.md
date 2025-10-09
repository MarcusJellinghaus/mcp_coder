# Step 1: Modify IssueData TypedDict

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 1: Modify the IssueData TypedDict to add the assignees field.

Requirements:
- Add assignees: List[str] field to IssueData TypedDict
- Field represents list of GitHub usernames assigned to work on the issue
- Place after labels field, before user field
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

### Field Ordering
Place `assignees` after `labels` to maintain logical grouping:
- Issue metadata (number, title, body, state)
- Categorization (labels, assignees)
- Audit trail (user, timestamps, url, locked)

## Verification
- Run mypy to verify TypedDict is valid
