# Step 3: Update Existing Methods for Assignees Field

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 3: Update all existing methods that return IssueData to include the assignees field.

Requirements:
- Add assignees=[] to all IssueData returns in existing methods
- Update corresponding unit tests to verify assignees field
- Maintain consistency across all methods
- Follow defensive programming for datetime fields

Affected methods:
- create_issue()
- close_issue()
- reopen_issue()
- add_labels()
- remove_labels()
- set_labels()

Follow the summary document for architectural context.
```

## WHERE

### Implementation
**File**: `src/mcp_coder/utils/github_operations/issue_manager.py`

**Methods to modify** (6 methods):
1. `create_issue()` - Line ~150
2. `close_issue()` - Line ~413
3. `reopen_issue()` - Line ~478
4. `add_labels()` - Line ~714
5. `remove_labels()` - Line ~779
6. `set_labels()` - Line ~844

### Tests
**File**: `tests/utils/github_operations/test_issue_manager.py`

**Tests to verify** (6 tests):
1. `test_create_issue_success()`
2. `test_close_issue_success()`
3. `test_reopen_issue_success()`
4. `test_add_labels_success()`
5. `test_remove_labels_success()`
6. `test_set_labels_success()`

## WHAT

### Implementation Pattern
For each method returning `IssueData`, add:
```python
return IssueData(
    number=github_issue.number,
    title=github_issue.title,
    body=github_issue.body or "",
    state=github_issue.state,
    labels=[label.name for label in github_issue.labels],
    assignees=[assignee.login for assignee in github_issue.assignees],  # ADD THIS
    user=github_issue.user.login if github_issue.user else None,
    created_at=(
        github_issue.created_at.isoformat() if github_issue.created_at else None
    ),
    updated_at=(
        github_issue.updated_at.isoformat() if github_issue.updated_at else None
    ),
    url=github_issue.html_url,
    locked=github_issue.locked,
)
```

### Test Pattern
For each test, update mock setup and assertions:
```python
# Mock setup - add assignees
mock_assignee = MagicMock()
mock_assignee.login = "testuser"
mock_issue.assignees = [mock_assignee]

# Assertion - verify assignees
assert result["assignees"] == ["testuser"]
```

## HOW

### Integration Points
- **No new imports** - List comprehension pattern already used for labels
- **Defensive programming** - Handle empty assignees list like labels
- **Mock consistency** - Use same MagicMock pattern for assignee objects

### Error Handling
All error cases already return empty IssueData, update to include:
```python
IssueData(
    number=0,
    # ... other fields ...
    assignees=[],  # ADD THIS
)
```

## ALGORITHM

### Implementation Steps
```
1. For each of 6 methods returning IssueData:
   a. Add assignees list comprehension after labels
   b. Update all error return paths to include assignees=[]
2. Verify syntax and field ordering
3. Ensure defensive programming maintained
```

### Test Update Steps
```
1. For each corresponding test:
   a. Add mock assignee object with login attribute
   b. Set mock_issue.assignees to list of assignees
   c. Add assertion for assignees field
2. Run tests to verify changes work correctly
```

## DATA

### Assignees Field Format
```python
# Empty assignees (common case)
assignees=[]

# Single assignee
assignees=["user1"]

# Multiple assignees
assignees=["user1", "user2", "user3"]

# List comprehension
assignees=[assignee.login for assignee in github_issue.assignees]
```

### Updated IssueData Examples
```python
# Success case
IssueData(
    number=123,
    title="Issue",
    body="Body",
    state="open",
    labels=["bug"],
    assignees=["dev1", "dev2"],
    user="creator",
    created_at="2023-01-01T00:00:00Z",
    updated_at="2023-01-01T00:00:00Z",
    url="https://github.com/test/repo/issues/123",
    locked=False
)

# Error case
IssueData(
    number=0,
    title="",
    body="",
    state="",
    labels=[],
    assignees=[],  # NEW
    user=None,
    created_at=None,
    updated_at=None,
    url="",
    locked=False
)
```

## Verification
1. Run pytest on updated tests
2. Verify mypy type checking passes
3. Check no regression in existing functionality
