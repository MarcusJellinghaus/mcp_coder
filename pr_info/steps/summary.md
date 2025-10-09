# Issue-Branch Linking via GitHub GraphQL API

## Overview
Implement GitHub's native issue-branch linking feature using GraphQL API to create, query, and unlink branch-issue associations that appear in GitHub's "Development" section.

## Architectural Changes

### New Components
- **IssueBranchManager**: New manager class for branch-issue operations
- **BranchCreationResult**: TypedDict for structured creation results
- **GraphQL Integration**: First use of GitHub GraphQL API in the codebase
- **Branch Name Sanitization**: Utility matching GitHub's exact naming rules

### Design Patterns Applied
- **Inheritance**: Extends `BaseGitHubManager` for consistency
- **Error Handling**: Uses existing `@_handle_github_errors` decorator
- **Logging**: Uses existing `@log_function_call` decorator
- **TypedDict Returns**: Maintains consistency with `IssueManager` patterns
- **TDD Approach**: Tests before implementation for all methods

### Integration Points
- Uses PyGithub's internal GraphQL requester: `_github_client._Github__requester`
- Accesses GitHub Node IDs via `.node_id` property
- Follows same authentication and repository patterns as existing managers

## Files to Create

### Source Files
```
src/mcp_coder/utils/github_operations/issue_branch_manager.py
```
- `IssueBranchManager` class (3 methods)
- `BranchCreationResult` TypedDict
- `generate_branch_name_from_issue()` utility function

### Test Files
```
tests/utils/github_operations/test_issue_branch_manager.py
tests/utils/github_operations/test_issue_branch_manager_integration.py
```
- Unit tests for all methods and edge cases
- Integration test covering complete workflow

## Files to Modify

```
src/mcp_coder/utils/github_operations/__init__.py
```
- Add `IssueBranchManager` and `BranchCreationResult` to exports

## Implementation Approach

### Test-Driven Development
Each step implements tests first, then functionality:
1. **Step 1**: Branch name sanitization (utility + tests)
2. **Step 2**: Query linked branches (tests + implementation)
3. **Step 3**: Create linked branch (tests + implementation)
4. **Step 4**: Delete linked branch (tests + implementation)
5. **Step 5**: Integration test (end-to-end workflow)
6. **Step 6**: Module integration (exports + verification)

### GraphQL Operations
- **Queries**: Use `graphql_query()` for reading linked branches
- **Mutations**: Use `graphql_named_mutation()` for create/delete operations
- **Node IDs**: Extract from PyGithub objects via `.node_id` property
- **Error Handling**: Wrap all GraphQL calls with try-catch and logging

## Key Features

### Branch Name Generation
- Follows GitHub's exact sanitization rules
- Format: `{issue-number}-{sanitized-title}`
- Max length 244 characters (Git branch name limit)
- Preserves issue number, truncates title if needed

### Duplicate Prevention
- Queries existing linked branches before creation
- Returns existing branches in error response
- Prevents redundant API calls and conflicts

### Link Management
- Creates association without creating Git branch (GraphQL only)
- Unlinks without deleting Git branch (removes association only)
- Returns structured data for error handling and UI integration

## Testing Strategy

### Unit Tests
- Branch name sanitization edge cases
- GraphQL response parsing
- Error handling for invalid inputs
- Empty/null value handling

### Integration Tests
- Full workflow with real GitHub API
- Duplicate prevention verification
- Branch visibility in GitHub UI
- Cleanup and state verification

## Success Criteria
- All unit tests pass
- Integration test verifies GitHub UI "Development" section
- Duplicate prevention works correctly
- Error handling covers common failures
- Code follows existing patterns and conventions
