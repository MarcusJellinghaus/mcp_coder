# Step 2: Core IssueManager Class Structure

## Objective
Create the main IssueManager class inheriting from BaseGitHubManager with additional validation methods.

## WHERE
- **File**: `src/mcp_coder/utils/github_operations/issue_manager.py` (extend existing file)
- **Class**: `IssueManager`

## WHAT
Main class structure with:
```python
class IssueManager(BaseGitHubManager):
    def __init__(self, project_dir: Optional[Path] = None) -> None: ...
    def _validate_issue_number(self, issue_number: int) -> bool: ...
    def _validate_comment_id(self, comment_id: int) -> bool: ...
```

## HOW
- Inherit from BaseGitHubManager for all GitHub client and repository functionality
- Call super().__init__(project_dir) for initialization
- Add issue-specific validation methods following existing patterns
- Import BaseGitHubManager and issue-specific dependencies

## ALGORITHM
```
1. Inherit from BaseGitHubManager class
2. Implement simple __init__ method calling super().__init__(project_dir)
3. Add _validate_issue_number method (same pattern as _validate_pr_number)
4. Add _validate_comment_id method (similar validation pattern)
5. Inherit all repository and GitHub client functionality automatically
```

## DATA
```python
# Inherited attributes from BaseGitHubManager
self.project_dir: Path
self.github_token: str
self._repo: git.Repo
self._github_client: Github
self._repository: Optional[Repository]
```

## LLM Prompt
```
Based on the GitHub Issues API Implementation Summary, implement Step 2: Core IssueManager Class Structure.

Extend the existing issue_manager.py file to add the IssueManager class inheriting from BaseGitHubManager.

Requirements:
- Inherit from BaseGitHubManager class
- Simple __init__ method calling super().__init__(project_dir)
- Add validation methods for issue_number and comment_id following existing validation patterns
- Import BaseGitHubManager from .base_manager
- Use hybrid error handling: raise exceptions for auth/permission errors, return empty dict/list for other errors
- All repository access, GitHub client setup, and configuration handled by base class

Do not implement any issue operations yet - just the class structure and validation methods.
```
