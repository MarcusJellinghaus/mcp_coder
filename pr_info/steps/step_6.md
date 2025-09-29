# Step 6: Create BaseGitHubManager Class

## Context
Extract shared functionality from `LabelsManager` and `PullRequestManager` into a common base class to eliminate code duplication and improve maintainability.

## WHERE

### New File
```
src/mcp_coder/utils/github_operations/base_manager.py
```

### Files to Modify
```
src/mcp_coder/utils/github_operations/__init__.py
```

## WHAT

### Base Class and Shared Methods

```python
class BaseGitHubManager:
    def __init__(self, project_dir: Optional[Path] = None) -> None:
    def _get_repository(self) -> Optional[Repository]:
    def _validate_project_dir(self, project_dir: Optional[Path]) -> Path:
    def _get_github_token(self) -> str:
    def _initialize_git_repo(self, project_dir: Path) -> git.Repo:
    def _initialize_github_client(self, token: str) -> Github:
    
    # Properties
    @property
    def repository_name(self) -> str:
    @property  
    def repository_url(self) -> str:
```

### Shared Attributes
```python
self.project_dir: Path
self.github_token: str
self._repo: git.Repo
self._github_client: Github
self._repository: Optional[Repository]
```

## HOW

### Integration Points
- Extract common initialization logic from both existing managers
- Use same imports as existing classes: `git`, `Github`, `Repository`, `user_config`
- Add proper error handling with logging
- Follow existing validation patterns exactly

### Module Exports
Update `__init__.py` to export `BaseGitHubManager` alongside existing classes.

## ALGORITHM

### Initialization Logic
```
1. Validate project_dir (exists, is directory)
2. Validate git repository (use git.Repo)
3. Get GitHub token (config or environment)
4. Initialize GitHub client with token
5. Cache repository URL and project attributes
```

## DATA

### Instance Attributes
```python
self.project_dir: Path                    # Validated project directory
self.github_token: str                    # GitHub authentication token  
self._repo: git.Repo                      # Git repository object
self._github_client: Github               # PyGithub client instance
self._repository: Optional[Repository]    # Cached GitHub repository object
```

### Properties Return Values
- `repository_name`: `str` (format: "owner/repo")
- `repository_url`: `str` (format: "https://github.com/owner/repo")

## LLM Prompt

```
Create BaseGitHubManager class to eliminate code duplication between LabelsManager and PullRequestManager.

Context: Read pr_info/steps/summary.md and pr_info/steps/decisions.md for overview.
Reference: Both src/mcp_coder/utils/github_operations/labels_manager.py and pr_manager.py

Tasks:
1. Create base_manager.py with BaseGitHubManager class
2. Extract common initialization logic from both managers:
   - Project directory validation
   - Git repository validation  
   - GitHub token retrieval from config
   - GitHub client initialization
   - Repository URL parsing and caching
3. Add shared helper methods:
   - _get_repository() for lazy Repository object loading
   - _validate_project_dir() for directory validation
   - _get_github_token() for token retrieval
   - _initialize_git_repo() for git setup
   - _initialize_github_client() for GitHub client
4. Add properties: repository_name, repository_url
5. Use proper logging with logger = logging.getLogger(__name__)
6. Update __init__.py to export BaseGitHubManager

Implementation notes:
- Follow exact same validation logic as existing classes
- Use same error messages and exception types
- Maintain all existing behavior - pure refactor
- Add comprehensive docstrings for the base class

Run: pytest tests/utils/test_github_operations.py::TestLabelsManagerUnit -v
Expected: All tests PASS (no behavioral changes from refactoring)
```

## Notes

- Pure refactor - no functional changes
- Both existing managers will inherit from this base in next step
- Maintain exact same error handling and validation logic
- Add comprehensive docstrings explaining the shared functionality
