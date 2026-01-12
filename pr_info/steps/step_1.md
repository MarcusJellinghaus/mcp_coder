# Step 1: Update base_manager.py to Use git_operations Abstraction

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Refactor src/mcp_coder/utils/github_operations/base_manager.py to remove direct 
GitPython imports and use the git_operations abstraction layer instead.

Follow the specifications below exactly. Preserve existing error messages for 
API compatibility.
```

## WHERE

**File to modify:** `src/mcp_coder/utils/github_operations/base_manager.py`

## WHAT

### Import Changes

**Remove:**
```python
import git
```

**Add:**
```python
from mcp_coder.utils import git_operations
```

### Attribute Removal

**Remove from class:**
- `self._repo: Optional[git.Repo] = None` (line 115)
- All assignments: `self._repo = repo` and `self._repo = None`
- Update class docstring: Remove `_repo` from Attributes section

### Method: `_init_with_project_dir()`

**Current signature:** `def _init_with_project_dir(self, project_dir: Path) -> None`

**Replace lines 145-153:**
```python
# OLD:
try:
    repo = git.Repo(project_dir)
except git.InvalidGitRepositoryError as exc:
    raise ValueError(
        f"Directory is not a git repository: {project_dir}"
    ) from exc
self._repo = repo
```

**With:**
```python
# NEW:
if not git_operations.is_git_repository(project_dir):
    raise ValueError(f"Directory is not a git repository: {project_dir}")
```

### Method: `_get_repository()`

**Current signature:** `def _get_repository(self) -> Optional[Repository]`

**Replace the project_dir mode block (lines 198-211):**
```python
# OLD:
elif self._repo is not None:
    # project_dir mode - extract from git remote
    remote_url = None
    for remote in self._repo.remotes:
        if remote.name == "origin":
            remote_url = remote.url
            break
    if not remote_url:
        logger.warning("No 'origin' remote found in git repository")
        return None
    parsed = parse_github_url(remote_url)
    if parsed is None:
        logger.warning("Could not parse GitHub URL: %s", remote_url)
        return None
    owner, repo_name = parsed
    repo_full_name = f"{owner}/{repo_name}"
```

**With:**
```python
# NEW:
elif self.project_dir is not None:
    # project_dir mode - use git_operations abstraction
    github_url = git_operations.get_github_repository_url(self.project_dir)
    if not github_url:
        logger.warning("Could not get GitHub URL from repository")
        return None
    parsed = parse_github_url(github_url)
    if parsed is None:
        logger.warning("Could not parse GitHub URL: %s", github_url)
        return None
    owner, repo_name = parsed
    repo_full_name = f"{owner}/{repo_name}"
```

## HOW

### Integration Points
- Import `git_operations` module (namespace import for clarity)
- Use `git_operations.is_git_repository()` from `repository.py`
- Use `git_operations.get_github_repository_url()` from `remotes.py`

## ALGORITHM

```
_init_with_project_dir:
1. Validate directory exists and is directory (existing code)
2. Call git_operations.is_git_repository(project_dir)
3. If False, raise ValueError with same error message
4. Set self.project_dir = project_dir

_get_repository (project_dir mode):
1. Call git_operations.get_github_repository_url(project_dir)
2. If None, log warning and return None
3. Parse URL with parse_github_url()
4. Continue with existing logic to get repo from GitHub API
```

## DATA

### Return Values (unchanged)
- `_init_with_project_dir()`: None (raises ValueError on failure)
- `_get_repository()`: Optional[Repository]

### Error Messages (must preserve exactly)
- `"Directory is not a git repository: {project_dir}"`

### Warning Messages (slightly updated for clarity)
- `"Could not get GitHub URL from repository"` (combines two previous warnings)
- `"Could not parse GitHub URL: %s"` (unchanged)

## Verification

After this step:
- Code should compile without import errors
- Tests will fail (expected - they mock git.Repo which no longer exists)
- Step 2 will fix the tests
