# Step 3: Create IssueBranchManager with Branch Creation

## LLM Prompt
```
Read pr_info/steps/summary.md and this step file. Implement IssueBranchManager class and create_remote_branch_for_issue() method following TDD approach:
1. First write unit tests
2. Then implement the class following BaseGitHubManager pattern
Use PyGithub's create_git_ref() for remote branch creation.
```

## WHERE
- **Test File**: `tests/utils/github_operations/test_issue_branch_manager.py` (extend)
- **Implementation File**: `src/mcp_coder/utils/github_operations/issue_branch_manager.py` (extend)

## WHAT

### Test Classes and Functions
```python
class TestIssueBranchManagerInit:
    def test_initialization_requires_project_dir(self) -> None
    def test_initialization_requires_git_repository(tmp_path: Path) -> None
    def test_initialization_requires_github_token(tmp_path: Path) -> None

class TestCreateRemoteBranchForIssue:
    def test_create_branch_with_auto_generated_name(mock_github, tmp_path) -> None
    def test_create_branch_with_custom_name(mock_github, tmp_path) -> None
    def test_create_branch_with_custom_base_branch(mock_github, tmp_path) -> None
    def test_create_branch_fails_when_branch_exists(mock_github, tmp_path) -> None
    def test_create_branch_invalid_issue_number(tmp_path) -> None
    def test_create_branch_issue_not_found(mock_github, tmp_path) -> None
    def test_create_branch_auth_error_raises(mock_github, tmp_path) -> None
    def test_create_branch_with_existing_linked_branches(mock_github, tmp_path) -> None
```

### Implementation Classes
```python
class BranchCreationResult(TypedDict):
    success: bool
    branch_name: str
    error: Optional[str]
    existing_branches: List[str]

class IssueBranchManager(BaseGitHubManager):
    def create_remote_branch_for_issue(
        self,
        issue_number: int,
        branch_name: Optional[str] = None,
        base_branch: Optional[str] = None
    ) -> BranchCreationResult
```

## HOW

### Integration Points
1. **Inheritance**: Extends `BaseGitHubManager`
2. **Decorators**: 
   - `@log_function_call`
   - `@_handle_github_errors(default_return={...})`
3. **Dependencies**:
   - Import `IssueManager` for `get_issue()`
   - Import `generate_branch_name_from_issue()`
   - Use `self._get_repository()` from base class
4. **PyGithub API**:
   - `repo.default_branch` - Get default branch name
   - `repo.get_branch(name).commit.sha` - Get base SHA
   - `repo.create_git_ref(f"refs/heads/{name}", sha)` - Create branch
   - `repo.get_git_refs()` - Check existing branches

## ALGORITHM

### Test Algorithm (test_create_branch_with_auto_generated_name)
```
1. Setup: Git repo, mock GitHub API
2. Mock: Issue data, repository branches, default branch
3. Execute: manager.create_remote_branch_for_issue(123)
4. Assert: success=True, branch_name matches pattern "123-*"
5. Assert: create_git_ref called with correct ref and SHA
```

### Implementation Algorithm
```
1. Validate issue_number (return error result if invalid)
2. Get repository (return error result if fails)
3. Get issue data via IssueManager.get_issue()
4. Check existing linked branches (return if found)
5. Generate/validate branch_name
6. Get base_branch (default to repo.default_branch)
7. Get base SHA from base_branch
8. Check if branch exists remotely (return error if exists)
9. Create branch: repo.create_git_ref(f"refs/heads/{branch_name}", sha)
10. Return success result with branch_name
```

## DATA

### BranchCreationResult TypedDict
```python
{
    "success": bool,              # True if created successfully
    "branch_name": str,           # Name of created/attempted branch
    "error": Optional[str],       # Error message if failed
    "existing_branches": List[str] # Linked branches found (if any)
}
```

### Success Case
```python
{
    "success": True,
    "branch_name": "123-fix-login-bug",
    "error": None,
    "existing_branches": []
}
```

### Error Cases
```python
# Branch already exists
{
    "success": False,
    "branch_name": "123-fix-login-bug",
    "error": "Branch already exists",
    "existing_branches": []
}

# Linked branches found
{
    "success": False,
    "branch_name": "",
    "error": "Issue already has linked branches",
    "existing_branches": ["feature/fix-123", "123-alternative"]
}

# Invalid issue number
{
    "success": False,
    "branch_name": "",
    "error": "Invalid issue number",
    "existing_branches": []
}
```

## Implementation Pattern

```python
@log_function_call
@_handle_github_errors(
    default_return=BranchCreationResult(
        success=False,
        branch_name="",
        error="GitHub API error",
        existing_branches=[]
    )
)
def create_remote_branch_for_issue(
    self,
    issue_number: int,
    branch_name: Optional[str] = None,
    base_branch: Optional[str] = None
) -> BranchCreationResult:
    """Create a branch on GitHub for an issue.
    
    Args:
        issue_number: Issue number to create branch for
        branch_name: Custom branch name (auto-generated if None)
        base_branch: Base branch name (repo default if None)
        
    Returns:
        BranchCreationResult with operation status
        
    Raises:
        GithubException: For authentication or permission errors
    """
    # 1. Validate issue_number
    # 2. Get repository
    # 3. Check for existing linked branches
    # 4. Generate/validate branch name
    # 5. Get base branch SHA
    # 6. Check if branch already exists
    # 7. Create branch via PyGithub
    # 8. Return success result
```

## Key Implementation Details

### Getting Issue Data
```python
# Use IssueManager to fetch issue details
issue_manager = IssueManager(self.project_dir)
issue_data = issue_manager.get_issue(issue_number)
if issue_data["number"] == 0:  # Failed to fetch
    return error_result
```

### Generating Branch Name
```python
if branch_name is None:
    branch_name = generate_branch_name_from_issue(
        issue_number, 
        issue_data["title"]
    )
```

### Getting Base Branch SHA
```python
if base_branch is None:
    base_branch = repo.default_branch
    
base_branch_ref = repo.get_branch(base_branch)
base_sha = base_branch_ref.commit.sha
```

### Checking Branch Exists
```python
# Check if branch exists in remote refs
try:
    repo.get_git_ref(f"heads/{branch_name}")
    # Branch exists - return error
except GithubException as e:
    if e.status == 404:
        # Branch doesn't exist - can proceed
        pass
    else:
        raise
```

### Creating Branch
```python
repo.create_git_ref(
    ref=f"refs/heads/{branch_name}",
    sha=base_sha
)
```
