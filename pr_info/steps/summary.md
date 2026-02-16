# Implementation Summary: Branch Resolution with PR Fallback

## Issue Reference
**Issue #219**: No linked branch found for issues with draft PRs

## Problem Statement
The coordinator command fails to find branches for issues when a draft PR has been created from the linked branch. GitHub removes the `linkedBranches` connection from issues when a PR is created, transferring the linkage to the PR instead.

**Current Behavior:**
- Queries only `linkedBranches` GraphQL field
- Returns empty list when PR exists → workflow skipped silently
- Affects implement and create-pr workflows

**Root Cause:**
GitHub API behavior: Issue → Branch linked → Draft PR created → linkedBranches empty → Link now in PR timeline

---

## Architectural Design

### Design Philosophy: KISS Principle
Instead of creating a separate module with complex result types, we **extend the existing `IssueBranchManager`** with a single fallback method.

### Key Design Decisions

1. **Single Responsibility Extension**
   - Add one new method to existing `IssueBranchManager` class
   - Method encapsulates two-step fallback logic
   - Reuses existing error handling patterns (`@_handle_github_errors` decorator)

2. **Simple Return Type**
   - Returns `Optional[str]` (branch name or None)
   - No complex enum/TypedDict structures
   - Logging provides debugging context internally

3. **Two-Step Resolution Strategy**
   ```
   Step 1: Query linkedBranches (fast, primary source)
   Step 2: Query issue timeline for draft/open PRs (fallback)
   ```

4. **Error Handling**
   - Multiple PRs found → Return None, log warning with PR numbers
   - No PRs found → Return None
   - API errors → Handled by decorator, return None

---

## Architecture Changes

### Modified Components

#### 1. `IssueBranchManager` (`src/mcp_coder/utils/github_operations/issues/branch_manager.py`)
**New Method:**
```python
def get_branch_with_pr_fallback(
    self, 
    issue_number: int,
    repo_owner: str,
    repo_name: str
) -> Optional[str]:
```

**Behavior:**
- Tries `get_linked_branches()` first (existing method)
- On empty result, queries GitHub GraphQL timeline API
- Filters for `CROSS_REFERENCED_EVENT` with PR type
- Returns `headRefName` if exactly one draft/open PR found
- Returns None if multiple PRs or no PRs found
- Logs resolution source and any issues internally

#### 2. Coordinator Workflow (`src/mcp_coder/cli/commands/coordinator/core.py`)
**Modified Function:** `dispatch_workflow()` (lines 388-400)

**Changes:**
- Import `parse_github_url` from `github_utils`
- Extract repo owner/name from `repo_config["repo_url"]`
- Replace `get_linked_branches()` call with `get_branch_with_pr_fallback()`
- Update error logging to be more comprehensive

---

## Files Created/Modified

### Modified Files
1. **`src/mcp_coder/utils/github_operations/issues/branch_manager.py`**
   - Add `get_branch_with_pr_fallback()` method (~80 lines)
   - GraphQL query for PR timeline
   - Filtering and resolution logic

2. **`src/mcp_coder/cli/commands/coordinator/core.py`**
   - Update `dispatch_workflow()` function (lines 388-400)
   - Add import for `parse_github_url`
   - Replace branch resolution logic (~15 lines changed)

### Created Files
3. **`tests/utils/github_operations/issues/test_branch_resolution.py`** (NEW)
   - Unit tests for new `get_branch_with_pr_fallback()` method
   - Test scenarios: linkedBranches success, PR fallback, multiple PRs, errors
   - ~280 lines (hybrid approach with parametrization for similar tests)

---

## Implementation Steps Overview

### Step 1: Test Suite Foundation
- Create test file structure
- Write failing tests for all scenarios
- Mock `IssueBranchManager` and GraphQL responses
- Covers: linkedBranches path, PR fallback, edge cases

### Step 2: Core Method Implementation
- Implement `get_branch_with_pr_fallback()` in `branch_manager.py`
- GraphQL timeline query logic
- PR filtering (draft/open state)
- Make tests pass

### Step 3: Coordinator Integration
- Update `dispatch_workflow()` in coordinator
- Parse repo URL for owner/name
- Replace branch resolution call
- Update error logging

### Step 4: Code Quality Verification
- Run pylint, pytest, mypy
- Fix any issues
- Ensure all tests pass
- Verify no regressions

---

## Acceptance Criteria

- [x] `get_branch_with_pr_fallback()` method added to `IssueBranchManager`
- [x] Method queries linkedBranches first (primary path)
- [x] Method queries issue timeline for draft/open PRs as fallback
- [x] Multiple PRs case: returns None, logs warning with PR numbers
- [x] Coordinator updated to use new method
- [x] Comprehensive error logging (factual, no suggestions)
- [x] Coordinator continues processing after errors (non-blocking)
- [x] Unit tests pass with mocked managers
- [x] All code quality checks pass (pylint, pytest, mypy)
- [x] Closed issues remain filtered out (no changes needed - already handled)

---

## Technical Notes

### GraphQL Timeline Query
Query issue's `timelineItems` for `CROSS_REFERENCED_EVENT`:

```graphql
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      timelineItems(itemTypes: [CROSS_REFERENCED_EVENT], first: 100) {
        nodes {
          __typename
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                number
                state
                isDraft
                headRefName
              }
            }
          }
        }
      }
    }
  }
}
```

**Filtering Logic:**
- Only consider PRs with `state == "OPEN"` (includes both draft and non-draft)
- Single PR found → return `headRefName`
- Multiple PRs found → return None, log PR numbers
- No PRs found → return None

**Note:** Timeline query limited to first 100 cross-references (sufficient for typical usage).

### Error Handling Strategy
- Use existing `@_handle_github_errors(default_return=None)` decorator
- Log warnings internally for debugging
- Coordinator logs comprehensive error and continues processing
- Non-blocking: other issues processed even if one fails

---

## Testing Strategy

### Test Coverage
1. **Primary Path**: linkedBranches returns branch → immediate success
2. **Fallback Success (parametrized)**: linkedBranches empty, single draft/open PR found
3. **Multiple PRs**: linkedBranches empty, multiple PRs → None + warning
4. **Not Found**: linkedBranches empty, no PRs → None
5. **API Errors**: GraphQL errors handled by decorator → None
6. **Invalid Input**: Invalid issue numbers → None

**Test Structure**: Hybrid approach with parametrization reduces duplication (~280 lines)

### Test Patterns
- Mock `IssueBranchManager` with fixtures
- Mock GraphQL responses (query and mutation patterns)
- Follow existing test structure from `test_issue_branch_manager.py`
- Use `pytest.fixture` for manager setup
- Assert on return values and log messages

---

## Dependencies

### Internal
- `IssueBranchManager.get_linked_branches()` (existing method)
- `@_handle_github_errors` decorator (existing)
- `parse_github_url()` from `github_utils` (existing)
- PyGithub GraphQL API

### External
- GitHub GraphQL API (timeline queries)
- PyGithub library

---

## Rollback Plan
If issues arise:
1. Revert coordinator changes (restore old `get_linked_branches()` call)
2. Remove new method from `IssueBranchManager`
3. Delete test file

Low risk: Changes are additive, no existing functionality modified.

---

## Estimated Complexity
- **Low-Medium**: Single method addition, straightforward GraphQL query
- **Lines Changed**: ~100 new, ~15 modified
- **Test Lines**: ~300-400 new
- **Files Modified**: 2 existing, 1 new test file
