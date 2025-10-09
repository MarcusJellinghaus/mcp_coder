# Step 3: Update Existing Methods to Populate Assignees

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 3: Update existing methods to populate assignees field.

Requirements:
- Update 6 existing methods to populate assignees from GitHub API response
- Update test mocks to include assignees field
- Methods to update:
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
**Methods**: All 6 methods that return `IssueData`

### Tests
**File**: `tests/utils/github_operations/test_issue_manager.py`
**Tests**: All test mocks that create `IssueData` objects

## WHAT

### Implementation Pattern
Add assignees field to all `IssueData` returns in the 6 methods:
```python
assignees=[assignee.login for assignee in github_issue.assignees],
```

### Test Mock Pattern
Add assignees field to all mock `IssueData` objects:
```python
"assignees": []
```

## HOW

### Implementation
- Locate each method's `IssueData` return statement
- Add assignees line after the labels line
- Use the same list comprehension pattern as labels

### Test Mocks
- Find all places where test code creates mock `IssueData` return values
- Add `"assignees": []` to each mock
- TypedDict requires all fields to be present

## Verification
1. Run mypy to verify all IssueData objects are complete
2. Run unit tests to ensure mocks are correct
3. All 6 methods should consistently return assignees
