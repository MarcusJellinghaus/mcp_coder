# Step 5: Comment Management Operations  

## Objective
Implement full CRUD operations for issue comments: add_comment, get_comments, edit_comment, delete_comment.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py`
- **Methods**: Add to existing IssueManager class

## WHAT
Comment management operations:
```python
@log_function_call
def add_comment(self, issue_number: int, body: str) -> CommentData: ...

@log_function_call
def get_comments(self, issue_number: int) -> List[CommentData]: ...

@log_function_call  
def edit_comment(self, comment_id: int, body: str) -> CommentData: ...

@log_function_call
def delete_comment(self, comment_id: int) -> bool: ...
```

## HOW
- Use @log_function_call decorator consistently
- Follow same validation and error handling patterns
- Convert GitHub IssueComment objects to CommentData dictionaries
- Return boolean for delete_comment (success/failure)

## ALGORITHM
```
1. Validate issue_number/comment_id and body content
2. Get repository and issue using existing methods
3. Call GitHub API comment methods (create_comment, get_comments, etc.)
4. Convert GitHub comment objects to CommentData dictionaries
5. Return structured data or empty dict/list/False on error
```

## DATA
```python
# add_comment, edit_comment return
CommentData or {} on error

# get_comments returns
List[CommentData] or [] on error  

# delete_comment returns
bool (True on success, False on error)

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
Based on the GitHub Issues API Implementation Summary, implement Step 5: Comment Management Operations.

Add four methods to the existing IssueManager class: add_comment, get_comments, edit_comment, delete_comment.

Requirements:
- Follow the same patterns as existing methods (error handling, validation, logging)
- Use @log_function_call decorator on all methods
- Convert GitHub IssueComment objects to CommentData dictionaries
- Use _validate_comment_id for comment_id validation
- Return boolean for delete_comment (True/False), structured data for others
- Include comprehensive input validation for body content

Focus only on these 4 comment management operations. This completes the IssueManager implementation.
```
