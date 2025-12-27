# Step 1: Add Incremental GitHub API Fetching

## Objective
Add `list_issues_since()` method to `IssueManager` to support incremental fetching using GitHub's `since` parameter.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, implement Step 1: Add incremental GitHub API fetching to IssueManager.

Requirements:
- Add `list_issues_since()` method to support incremental fetching
- Use GitHub API's `since` parameter with `state="all"` 
- Follow existing code patterns in issue_manager.py
- Include proper error handling and logging
- Write comprehensive tests first (TDD approach)

Refer to the summary document for overall context and architecture decisions.
```

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Test File**: `tests/utils/github_operations/test_issue_manager.py`

## WHAT
### New Method
```python
def list_issues_since(self, since: datetime, state: str = "all", include_pull_requests: bool = False) -> List[IssueData]:
```

### Test Functions
```python
def test_list_issues_since_valid_datetime()
def test_list_issues_since_filters_pull_requests() 
def test_list_issues_since_error_handling()
def test_list_issues_since_pagination()
```

## HOW
### Integration Points
- **Decorator**: `@log_function_call` and `@_handle_github_errors(default_return=[])`
- **Import**: `from datetime import datetime` (if not already present)
- **Position**: After existing `list_issues()` method in IssueManager class

### GitHub API Call
```python
# Uses PyGithub's get_issues() with since parameter
for issue in repo.get_issues(state=state, since=since):
```

## ALGORITHM
```
1. Validate since parameter is datetime object
2. Get repository using existing _get_repository() method  
3. Call repo.get_issues(state=state, since=since) for incremental fetch
4. Filter out pull requests if include_pull_requests=False
5. Convert GitHub issue objects to IssueData dictionaries
6. Return list of IssueData objects
```

## DATA
### Input Parameters
- `since: datetime` - Only fetch issues updated after this time
- `state: str = "all"` - Issue state filter ('open', 'closed', 'all')  
- `include_pull_requests: bool = False` - Whether to include PRs

### Return Value
- `List[IssueData]` - List of issue dictionaries with same structure as `list_issues()`

### Error Handling
- Returns empty list `[]` on any GitHub API errors (via decorator)
- Logs validation errors for invalid datetime parameter
- Uses existing error handling patterns from current `list_issues()` method

## Implementation Notes
- **Minimal changes**: Follows existing patterns exactly, just adds `since` parameter
- **Backwards compatible**: Doesn't modify existing `list_issues()` method
- **State parameter**: Uses `"all"` by default to detect closed/deleted issues for cache cleanup
- **Consistent interface**: Same return type and error handling as existing method