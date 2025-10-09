# Design Decisions

## Decision Log

### 1. Assignees Field Scope
**Decision**: Only `get_issue()` needs to populate assignees; all other methods return `assignees=[]`

**Rationale**: 
- Only retrieval operation needs complete assignee data
- Other operations (create, close, label management) don't require returning assignee information
- Reduces implementation complexity by ~60%

### 2. TypedDict Field Definition
**Decision**: Add `assignees: List[str]` (not `Optional[List[str]]`)

**Rationale**:
- Always returning a list (even if empty) is cleaner than nullable field
- No null checks needed in consuming code
- Empty list `[]` is semantically clearer than `None` for "no assignees"
- Consistent with existing `labels` field pattern

### 3. Test Coverage Strategy
**Decision**: Minimal test updates - no test changes for 6 existing methods returning `assignees=[]`

**Rationale**:
- KISS principle: empty list assignment is trivial
- MyPy will catch missing field errors at type-check time
- Only test `get_issue()` which has actual logic for assignees

### 4. Unit Test Scope for get_issue()
**Decision**: Only `test_get_issue_success()` - remove invalid_number and auth_error tests

**Rationale**:
- KISS principle: avoid redundant tests
- Decorator `@_handle_github_errors` already handles both error cases consistently
- Testing decorator behavior once is sufficient (not per method)

### 5. Implementation Approach
**Decision**: Merge Steps 2 & 3 into single implementation step

**Rationale**:
- More efficient: update all IssueData returns while file is open
- Better context: less chance of missing updates
- Single cohesive commit instead of fragmented changes

### 6. Integration Test
**Decision**: Keep simple integration test extension

**Rationale**:
- Verifies real GitHub API behavior for assignees field
- Round-trip validation (create → retrieve → verify)
- Minimal addition to existing test
