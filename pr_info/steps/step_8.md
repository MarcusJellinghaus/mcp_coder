# Step 8: Edit/Delete Comments Operations

## Objective
Implement edit and delete comments operations: edit_comment, delete_comment, with unit tests and final integration test enhancement.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class
- **Integration Test**: Final enhancement to existing test in `tests/utils/test_issue_manager_integration.py`

## WHAT
Edit and delete comments operations:
```python
@log_function_call  
def edit_comment(self, comment_id: int, body: str) -> CommentData: ...

@log_function_call
def delete_comment(self, comment_id: int) -> bool: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow hybrid error handling (raise for auth/permission errors, empty dict/False for others)
- Use _validate_comment_id for comment_id validation
- Return boolean for delete_comment (success/failure)

## ALGORITHM
```
1. Validate comment_id and body content (for edit)
2. Get repository using inherited _get_repository()
3. Call GitHub API comment methods (edit_comment, delete_comment)
4. Convert GitHub comment objects to CommentData dictionaries (for edit)
5. Return structured data, boolean, or empty dict/False on non-auth errors
```

## DATA
```python
# edit_comment returns
CommentData or {} on error

# delete_comment returns
bool (True on success, False on error)
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 8: Edit/Delete Comments Operations.

Add two methods to the existing IssueManager class: edit_comment, delete_comment.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Use _validate_comment_id for comment_id validation
- Return boolean for delete_comment (True/False), CommentData for edit_comment
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict/False for other errors

After implementation, add unit tests to tests/utils/test_issue_manager.py:
- Test both methods with mocked GitHub API calls
- Use KISS approach: essential coverage only
- Test success scenarios and basic error handling

Then enhance the existing integration test in tests/utils/test_issue_manager_integration.py:
- Complete the integration test flow: create_issue → add_labels → remove_labels → add_comment → edit_comment → delete_comment → close_issue
- Test the full issue lifecycle with real GitHub API
- Ensure integration test fails clearly with exceptions on permission issues

This completes the IssueManager implementation with full issue lifecycle testing.
```
