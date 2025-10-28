# Step 0: Refactor Shared Components (TDD)

## Reference
**Implementation Plan:** See `pr_info/steps/summary.md` for complete architectural overview.
**Decisions:** See `pr_info/steps/decisions.md` for all architectural decisions.

## Objective
Refactor shared components to support coordinator run without duplicating code:
1. Move `build_label_lookups()` from `validate_labels.py` to `label_config.py`
2. Add `repo_url` parameter support to `BaseGitHubManager`

## WHERE

**Files to Modify:**
1. `workflows/label_config.py` - Add `build_label_lookups()` function
2. `workflows/validate_labels.py` - Update import
3. `src/mcp_coder/utils/github_operations/base_manager.py` - Add `repo_url` support

**Test Files:**
1. `tests/workflows/test_label_config.py` - Test `build_label_lookups()` (if needed)
2. `tests/utils/github_operations/test_base_manager.py` - Test `repo_url` parameter

## WHAT

### Part A: Move `build_label_lookups()` to Shared Module

#### Current Location
`workflows/validate_labels.py` contains:
```python
def build_label_lookups(labels_config: Dict[str, Any]) -> LabelLookups:
    """Build lookup dictionaries from label configuration."""
    # ... implementation ...
```

#### New Location
Move to `workflows/label_config.py` as a shared function.

#### Changes Required
1. Copy function and `LabelLookups` TypedDict to `label_config.py`
2. Update import in `validate_labels.py`:
   ```python
   from workflows.label_config import load_labels_config, build_label_lookups, LabelLookups
   ```

### Part B: Add `repo_url` Support to `BaseGitHubManager`

#### Current Implementation
```python
class BaseGitHubManager:
    def __init__(self, project_dir: Optional[Path] = None) -> None:
        # Requires project_dir, validates it's a git repo
        # Extracts repo URL from git remote
```

#### New Implementation
```python
class BaseGitHubManager:
    def __init__(
        self, 
        project_dir: Optional[Path] = None,
        repo_url: Optional[str] = None
    ) -> None:
        """Initialize BaseGitHubManager with either project_dir or repo_url.
        
        Args:
            project_dir: Path to git repository (traditional usage)
            repo_url: GitHub repository URL (e.g., "https://github.com/user/repo.git")
            
        Raises:
            ValueError: If neither or both parameters provided
        """
        # Validate exactly one parameter provided
        if (project_dir is None) == (repo_url is None):
            raise ValueError("Exactly one of project_dir or repo_url must be provided")
        
        # Get GitHub token (same for both modes)
        github_token = user_config.get_config_value("github", "token")
        if not github_token:
            raise ValueError("GitHub token not found...")
        
        # Initialize based on mode
        if project_dir is not None:
            # Traditional mode - validate git repo
            self._init_with_project_dir(project_dir, github_token)
        else:
            # New mode - use repo_url directly
            self._init_with_repo_url(repo_url, github_token)
```

#### Helper Methods
```python
def _init_with_project_dir(self, project_dir: Path, github_token: str) -> None:
    """Initialize with local git repository (existing behavior)."""
    # Validate project_dir exists, is directory, is git repo
    # Extract repo URL from git remote
    
def _init_with_repo_url(self, repo_url: str, github_token: str) -> None:
    """Initialize with GitHub repository URL (new behavior)."""
    # Parse repo_url to extract owner/repo
    # Set self._repo to None (no local git repo)
    # Store parsed repo info for _get_repository()
```

## HOW

### Integration Points

**Usage in coordinator:**
```python
# coordinator.py
from ...utils.github_operations.issue_manager import IssueManager
from ...utils.github_operations.issue_branch_manager import IssueBranchManager

# Initialize managers with repo_url from config
issue_manager = IssueManager(repo_url=validated_config["repo_url"])
branch_manager = IssueBranchManager(repo_url=validated_config["repo_url"])
```

**Existing usage unchanged:**
```python
# Any existing code continues to work
manager = IssueManager(project_dir=Path.cwd())
```

### Algorithm for `BaseGitHubManager.__init__`

```
1. Validate exactly one of (project_dir, repo_url) is provided
2. Get GitHub token from config
3. Initialize GitHub client
4. IF project_dir provided:
     a. Validate directory exists and is git repo
     b. Extract repo URL from git remote
     c. Store git.Repo object
   ELSE (repo_url provided):
     a. Parse repo_url to extract owner/repo
     b. Set git.Repo to None
     c. Store parsed owner/repo for later use
5. Initialize _repository cache to None
```

### Data Structures

**Parsed repo URL storage:**
```python
# Store in __init__
self._repo_owner = "user"
self._repo_name = "mcp_coder"
self._repo_full_name = "user/mcp_coder"
```

**Modified `_get_repository()` method:**
```python
def _get_repository(self) -> Optional[Repository]:
    if self._repository is not None:
        return self._repository
    
    # IF initialized with project_dir: extract from git remote (existing)
    # ELSE: use stored _repo_full_name (new)
    
    self._repository = self._github_client.get_repo(repo_full_name)
    return self._repository
```

## Implementation Notes

1. **Backward Compatibility:** All existing code using `project_dir` continues to work without changes

2. **Error Handling:** Clear error messages for:
   - Neither parameter provided
   - Both parameters provided
   - Invalid repo_url format

3. **Testing Strategy:**
   - Test both initialization modes
   - Test error cases (neither, both, invalid URL)
   - Verify existing tests still pass

4. **LabelLookups TypedDict:** Move with `build_label_lookups()` to shared module

## LLM Prompt for Implementation

```
Implement Step 0 of the coordinator run feature as described in pr_info/steps/summary.md.

See pr_info/steps/decisions.md for architectural decisions.

Task: Refactor shared components for coordinator run

Requirements:
1. Part A - Move build_label_lookups():
   - Copy function from workflows/validate_labels.py to workflows/label_config.py
   - Include LabelLookups TypedDict
   - Update import in validate_labels.py
   - Ensure all existing tests still pass

2. Part B - Add repo_url support to BaseGitHubManager:
   - Accept either project_dir OR repo_url (exactly one required)
   - Maintain backward compatibility with existing code
   - Parse repo_url to extract owner/repo
   - Update _get_repository() to work with both modes
   - Add comprehensive error handling

3. Write tests:
   - Test BaseGitHubManager with project_dir (existing behavior)
   - Test BaseGitHubManager with repo_url (new behavior)
   - Test error cases (neither, both parameters)
   - Verify build_label_lookups() works in new location

4. Run code quality checks:
   - mcp__code-checker__run_pytest_check (fast unit tests only)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

Follow the exact specifications in step_0.md.
Maintain KISS principle - simple, clean refactoring.
```

## Test Execution

**Run fast unit tests only:**
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## Success Criteria

- ✅ `build_label_lookups()` moved to `label_config.py`
- ✅ `validate_labels.py` imports from shared location
- ✅ All existing tests still pass
- ✅ `BaseGitHubManager` accepts `repo_url` parameter
- ✅ Existing `project_dir` usage unchanged
- ✅ Error handling for invalid parameter combinations
- ✅ New tests for repo_url mode pass
- ✅ Pylint/mypy checks pass
