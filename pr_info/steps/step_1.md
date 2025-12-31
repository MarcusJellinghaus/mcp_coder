# Step 1: Extend `list_issues()` with `since` Parameter

## Objective
Extend the existing `list_issues()` method in `IssueManager` to support incremental fetching using GitHub's `since` parameter.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 1: Extend list_issues() with since parameter.

Requirements:
- Extend existing `list_issues()` method with optional `since: Optional[datetime] = None` parameter
- When `since` is provided, use GitHub API's `since` parameter to fetch only issues updated after that time
- Maintain backward compatibility - existing calls without `since` work unchanged
- Follow existing code patterns in issue_manager.py
- Include proper error handling and logging
- Write comprehensive tests first (TDD approach)

Refer to the summary document for overall context and architecture decisions.
```

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Test File**: `tests/utils/github_operations/test_issue_manager.py`

## WHAT
### Extended Method Signature
```python
def list_issues(
    self, 
    state: str = "open", 
    include_pull_requests: bool = False,
    since: Optional[datetime] = None
) -> List[IssueData]:
```

### Test Functions
```python
def test_list_issues_with_since_parameter()
def test_list_issues_since_filters_pull_requests() 
def test_list_issues_without_since_unchanged()
def test_list_issues_since_pagination()
```

## HOW
### Integration Points
- **Decorator**: Existing `@log_function_call` and `@_handle_github_errors(default_return=[])` unchanged
- **Import**: `from datetime import datetime` (add to existing imports)
- **Position**: Modify existing `list_issues()` method in IssueManager class

### GitHub API Call
```python
# Pass since parameter to PyGithub's get_issues() when provided
if since is not None:
    issues_iterator = repo.get_issues(state=state, since=since)
else:
    issues_iterator = repo.get_issues(state=state)
```

## ALGORITHM
```
1. Get repository using existing _get_repository() method  
2. Build get_issues() call - include since parameter if provided
3. Iterate over issues from GitHub API
4. Filter out pull requests if include_pull_requests=False
5. Convert GitHub issue objects to IssueData dictionaries
6. Return list of IssueData objects
```

## DATA
### Input Parameters
- `state: str = "open"` - Issue state filter ('open', 'closed', 'all') - unchanged
- `include_pull_requests: bool = False` - Whether to include PRs - unchanged
- `since: Optional[datetime] = None` - Only fetch issues updated after this time (new)

### Return Value
- `List[IssueData]` - List of issue dictionaries, unchanged structure

### Error Handling
- Returns empty list `[]` on any GitHub API errors (via existing decorator)
- Uses existing error handling patterns - no changes needed

## Implementation Notes
- **Minimal changes**: Extends existing method, follows existing patterns
- **Backward compatible**: Existing calls without `since` work unchanged
- **Optional parameter**: `since` defaults to `None`, only used when provided
- **Consistent interface**: Same return type and error handling as before