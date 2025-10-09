# Implementation Summary: Add get_issue() Method to IssueManager

## Overview
Add read-only `get_issue()` method to retrieve issue details by number, extending `IssueData` TypedDict to include assignees field.

## Architectural Changes

### Data Structure Changes
**Modified TypedDict: `IssueData`**
- **Add field**: `assignees: List[str]` - List of GitHub usernames assigned to work on the issue
- **Distinction**: Separates issue creator (`user`) from assignees (workers)
- **Impact**: All existing methods returning `IssueData` must include this field

### New Functionality
**Method: `get_issue(issue_number: int) -> IssueData`**
- **Purpose**: Read-only retrieval of issue details
- **Location**: `IssueManager` class, after `create_issue()` method
- **Pattern**: Follows existing decorator/validation/error-handling patterns
- **Return**: Complete issue metadata including assignees

## Design Decisions

1. **TypedDict Extension**: Add `assignees` field to support team collaboration use cases
2. **Backward Compatibility**: Accept breaking changes to existing methods for consistency
3. **Error Handling**: 404 (not found) returns empty IssueData via decorator (consistent with existing pattern)
4. **Defensive Programming**: Handle optional datetime fields with conditional checks
5. **Test Strategy**: Unit tests with mocked GitHub API (TDD approach)

## Files to Modify

### Source Code
1. **`src/mcp_coder/utils/github_operations/issue_manager.py`**
   - Modify `IssueData` TypedDict (add `assignees` field)
   - Add `get_issue()` method after `create_issue()`
   - Update 6 existing methods to include `assignees=[]` in their returns:
     - `create_issue()`
     - `close_issue()`
     - `reopen_issue()`
     - `add_labels()`
     - `remove_labels()`
     - `set_labels()`

### Tests
2. **`tests/utils/github_operations/test_issue_manager.py`**
   - Add 1 unit test for `get_issue()`:
     - `test_get_issue_success()`

3. **`tests/utils/github_operations/test_issue_manager_integration.py`**
   - Extend one existing test to call `get_issue()` and verify round-trip

## Implementation Steps

**Step 1**: Modify `IssueData` TypedDict
**Step 2**: Implement `get_issue()` method, unit test, and update existing methods to include `assignees=[]`
**Step 3**: Run quality checks and extend integration test

## Success Criteria

- ✅ `get_issue()` retrieves issue by number
- ✅ All methods return consistent `IssueData` with `assignees` field
- ✅ All unit tests pass
- ✅ Integration test verifies real API behavior
- ✅ All quality checks pass (pylint, pytest, mypy)
- ✅ Type hints are complete and correct
