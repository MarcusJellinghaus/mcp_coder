# Step 7: Add/Get Comments Operations

## Objective
Implement add and get comments operations: add_comment, get_comments, with unit tests.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class

## WHAT
Add and get comments operations:
```python
@log_function_call
def add_comment(self, issue_number: int, body: str) -> CommentData: ...

@log_function_call
def get_comments(self, issue_number: int) -> List[CommentData]: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow hybrid error handling (raise for auth/permission errors, empty dict/list for others)
- Convert GitHub IssueComment objects to CommentData dictionaries
- Validate input parameters thoroughly

## ALGORITHM
```
1. Validate issue_number and body content
2. Get repository using inherited _get_repository() method
3. Call GitHub API comment methods (create_comment, get_comments)
4. Convert GitHub comment objects to CommentData dictionaries
5. Return structured data or empty dict/list on non-auth errors
```

## DATA
```python
# add_comment returns
CommentData or {} on error

# get_comments returns
List[CommentData] or [] on error  

# CommentData structure
{
    "id": int,
    "body": str,
    "user": Optional[str],
    "created_at": Optional[str], 
    "updated_at": Optional[str],
    "url": str
}
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 7: Add/Get Comments Operations.

Add two methods to the existing IssueManager class: add_comment, get_comments.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Convert GitHub IssueComment objects to CommentData dictionaries
- Include comprehensive input validation for body content
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict/list for other errors

After implementation, add unit tests to tests/utils/test_issue_manager.py:
- Test both methods with mocked GitHub API calls
- Use KISS approach: essential coverage only
- Test success scenarios and basic error handling
- Test input validation for comment body

Focus only on these 2 comment operations and their unit tests.
```
