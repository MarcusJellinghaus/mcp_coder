# Design Decisions

## Decision Log

### 1. Assignees Field Scope
**Decision**: All methods returning `IssueData` populate assignees from GitHub API response

**Rationale**: 
- GitHub API already returns assignees in all responses (create, close, reopen, labels)
- No additional API calls needed
- Simpler than hardcoding `assignees=[]` - just map what's already there
- More useful for callers who want assignee info after any operation

### 2. TypedDict Field Definition
**Decision**: Add `assignees: List[str]` (not `Optional[List[str]]`)

**Rationale**:
- Always returning a list is cleaner than nullable field
- No null checks needed in consuming code
- Consistent with existing `labels` field pattern

### 3. Test Coverage Strategy
**Decision**: Update all existing test mocks to include `assignees` field

**Rationale**:
- TypedDict requires all fields to be present
- Mock return values must match the updated `IssueData` structure
- Add `assignees=[]` to existing test mocks for 6 methods

### 4. Unit Test Scope for get_issue()
**Decision**: Only `test_get_issue_success()` - no error case tests

**Rationale**:
- Decorator `@_handle_github_errors` already handles error cases
- Testing decorator behavior once is sufficient (not per method)

### 5. Implementation Approach
**Decision**: Split into separate steps - Step 2 adds `get_issue()`, Step 3 updates existing methods

**Rationale**:
- Cleaner separation: new feature vs. refactoring existing code
- Better git history and easier rollback if needed
- Step 2: Add `get_issue()` + unit test
- Step 3: Update 6 existing methods to populate assignees

### 6. Integration Test
**Decision**: Add Section 1.5 to `test_complete_issue_workflow` right after issue creation

**Rationale**:
- Natural place to validate `get_issue()` works correctly
- Verifies round-trip: create issue → get issue → verify fields match
- Tests assignees field with real GitHub API
