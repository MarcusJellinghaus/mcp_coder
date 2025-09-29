# Step 3: Core Issue Operations

## Objective
Implement basic issue CRUD operations: get_issue, get_issues, create_issue, close_issue, reopen_issue.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class

## WHAT
Core issue operations:
```python
@log_function_call
def get_issue(self, issue_number: int) -> IssueData: ...

@log_function_call  
def get_issues(self, state: str = "open", labels: Optional[List[str]] = None) -> List[IssueData]: ...

@log_function_call
def create_issue(self, title: str, body: str = "", labels: Optional[List[str]] = None) -> IssueData: ...

@log_function_call
def close_issue(self, issue_number: int) -> IssueData: ...

@log_function_call
def reopen_issue(self, issue_number: int) -> IssueData: ...
```

## HOW
- Use @log_function_call decorator (same as PullRequestManager)
- Follow exact same error handling pattern (try/except with empty dict returns)
- Use same validation approach as pr_manager methods
- Convert GitHub Issue objects to IssueData dictionaries

## ALGORITHM
```
1. Validate inputs (issue_number, title, state, labels)
2. Get repository using _parse_and_get_repo()
3. Call appropriate GitHub API method (get_issue, get_issues, create_issue, etc.)
4. Convert GitHub objects to IssueData dictionary format
5. Return structured data or empty dict on error
```

## DATA
```python
# get_issue returns
IssueData or {} on error

# get_issues returns  
List[IssueData] or [] on error

# create_issue, close_issue, reopen_issue return
IssueData or {} on error
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 3: Core Issue Operations.

Add five methods to the existing IssueManager class: get_issue, get_issues, create_issue, close_issue, reopen_issue.

Requirements:
- Follow the EXACT same patterns as PullRequestManager methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Convert GitHub Issue objects to IssueData dictionaries 
- Return empty dict/list on any error (never raise exceptions)
- Use comprehensive input validation following existing patterns
- Include detailed docstrings following pr_manager.py style

Focus only on these 5 core issue operations. Do not implement labels or comments yet.
```
