# Step 2: Core IssueManager Class Structure

## Objective
Create the main IssueManager class with initialization and validation methods, following the exact same patterns as PullRequestManager.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py` (extend existing file)
- **Class**: `IssueManager`

## WHAT
Main class structure with:
```python
class IssueManager:
    def __init__(self, project_dir: Optional[Path] = None) -> None: ...
    def _validate_issue_number(self, issue_number: int) -> bool: ...
    def _validate_comment_id(self, comment_id: int) -> bool: ...
    def _parse_and_get_repo(self) -> Optional[Repository]: ...
```

## HOW
- Copy initialization logic exactly from PullRequestManager
- Reuse the same validation patterns and error messages
- Use same Repository caching approach
- Import same dependencies (Github, GithubException, etc.)

## ALGORITHM
```
1. Copy __init__ method from PullRequestManager (identical logic)
2. Add _validate_issue_number method (same as _validate_pr_number)
3. Add _validate_comment_id method (similar validation pattern) 
4. Copy _parse_and_get_repo method (identical implementation)
5. Add same property methods (repository_name, default_branch)
```

## DATA
```python
# Class attributes (same as PullRequestManager)
self.project_dir: Path
self.repository_url: str  
self.github_token: str
self._github_client: Github
self._repository: Optional[Repository]
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 2: Core IssueManager Class Structure.

Extend the existing issue_manager.py file to add the IssueManager class following the EXACT same patterns as PullRequestManager in pr_manager.py.

Requirements:
- Copy the __init__ method logic exactly (same validations, same error messages)
- Copy _parse_and_get_repo method exactly  
- Add validation methods for issue_number and comment_id following pr_number pattern
- Copy the repository_name and default_branch properties exactly
- Use same imports and exception handling patterns
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict/list for other errors

Do not implement any issue operations yet - just the class structure and validation.
```
