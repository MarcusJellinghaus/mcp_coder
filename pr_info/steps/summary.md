# Issue Branch Management Implementation Summary

## Overview
Add functionality to create branches directly from GitHub issues and query linked branches, following GitHub's native branch naming conventions.

## Architectural Changes

### New Components
1. **IssueBranchManager** - New manager class for issue-branch operations
   - Inherits from `BaseGitHubManager`
   - Manages remote branch creation via GitHub API
   - Queries linked branches through GitHub timeline events

2. **Branch Name Generation** - Standalone utility function
   - Implements GitHub's exact sanitization rules
   - Format: `{issue-number}-{sanitized-title}`
   - Max length: 244 characters

3. **BranchCreationResult** - TypedDict for structured return values
   - Contains success status, branch name, errors, and existing branches

### Enhanced Components
1. **IssueManager** - Add missing read method
   - New `get_issue()` method for fetching issue data

## Design Decisions

1. **Remote-Only Operations**: Use PyGithub's `create_git_ref()` - no local git operations
2. **Separate Manager**: Follow existing pattern (IssueManager, LabelsManager, PRManager)
3. **Timeline Events**: Query GitHub issue timeline for linked branch detection
4. **Error Handling**: Re-raise auth errors (401/403), return defaults for others
5. **Base Branch**: Use `repo.default_branch` from PyGithub when not specified

## Files to Create

```
src/mcp_coder/utils/github_operations/
  issue_branch_manager.py          [NEW] - IssueBranchManager class and utilities

tests/utils/github_operations/
  test_issue_branch_manager.py     [NEW] - Unit tests for branch management
```

## Files to Modify

```
src/mcp_coder/utils/github_operations/
  issue_manager.py                 [MODIFY] - Add get_issue() method
  __init__.py                      [MODIFY] - Export new classes

tests/utils/github_operations/
  test_issue_manager.py            [MODIFY] - Add get_issue() tests

docs/architecture/
  ARCHITECTURE.md                  [MODIFY] - Document new manager
```

## Implementation Steps

1. **Step 1**: Add `get_issue()` to IssueManager (TDD)
2. **Step 2**: Create branch name generation utility (TDD)
3. **Step 3**: Create IssueBranchManager with branch creation (TDD)
4. **Step 4**: Add linked branches query functionality (TDD)
5. **Step 5**: Update exports and documentation

## API Surface

```python
# IssueManager enhancement
def get_issue(issue_number: int) -> IssueData

# New utility function
def generate_branch_name_from_issue(
    issue_number: int,
    issue_title: str,
    max_length: int = 244
) -> str

# New manager class
class IssueBranchManager(BaseGitHubManager):
    def create_remote_branch_for_issue(
        issue_number: int,
        branch_name: Optional[str] = None,
        base_branch: Optional[str] = None
    ) -> BranchCreationResult
    
    def get_linked_branches(issue_number: int) -> List[str]

# New TypedDict
class BranchCreationResult(TypedDict):
    success: bool
    branch_name: str
    error: Optional[str]
    existing_branches: List[str]
```

## Testing Strategy

- **Unit Tests**: Mock PyGithub dependencies (mark with `@pytest.mark.github_integration`)
- **Test Coverage**: Name generation, branch creation, linked branches query, error handling
- **TDD Approach**: Write tests first, then implementation for each step

## Integration Points

- Uses existing `BaseGitHubManager` infrastructure
- Leverages PyGithub's Repository API
- Follows existing logging patterns via `log_utils`
- Uses `@_handle_github_errors` decorator
- Integrates with `IssueManager.get_issue()` for issue data
