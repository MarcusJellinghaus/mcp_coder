# Step 2: Update Tests to Mock git_operations Instead of git.Repo

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md for context.

Update tests/utils/github_operations/test_base_manager.py to mock git_operations 
functions instead of git.Repo. The test logic remains the same - only the mock 
targets change.

Follow the specifications below exactly.
```

## WHERE

**File to modify:** `tests/utils/github_operations/test_base_manager.py`

## WHAT

### Import Changes

**Remove:**
```python
import git
```

**Keep (no changes):**
```python
from mcp_coder.utils.github_operations.base_manager import (
    BaseGitHubManager,
    _handle_github_errors,
)
```

### Mock Target Changes

All tests that mock `git.Repo` or `git.InvalidGitRepositoryError` need updating.

**Old mock path:**
```python
"mcp_coder.utils.github_operations.base_manager.git.Repo"
```

**New mock path:**
```python
"mcp_coder.utils.github_operations.base_manager.git_operations.is_git_repository"
"mcp_coder.utils.github_operations.base_manager.git_operations.get_github_repository_url"
```

### Test Class: `TestBaseGitHubManagerWithProjectDir`

#### `test_successful_initialization_with_project_dir`

**Change mocks:**
- Remove: `mock_repo = Mock(spec=git.Repo)` and `mock_repo_class`
- Add: Mock `git_operations.is_git_repository` to return `True`
- Remove: Assertion `assert manager._repo == mock_repo`

#### `test_initialization_fails_not_git_repository`

**Change mocks:**
- Remove: `git.Repo` side_effect with `git.InvalidGitRepositoryError`
- Add: Mock `git_operations.is_git_repository` to return `False`

#### `test_get_repository_with_project_dir_mode`

**Change mocks:**
- Remove: `mock_repo.remotes` setup
- Add: Mock `git_operations.get_github_repository_url` to return URL

#### `test_get_repository_no_origin_remote`

**Change mocks:**
- Remove: Mock setup for `mock_repo.remotes` with non-origin remote
- Add: Mock `git_operations.get_github_repository_url` to return `None`

#### `test_get_repository_invalid_github_url`

**Change mocks:**
- Remove: Mock setup for GitLab URL in remotes
- Add: Mock `git_operations.get_github_repository_url` to return GitLab URL

#### Other tests in this class

Apply similar pattern: Replace `git.Repo` mocks with `git_operations` function mocks.

### Test Class: `TestBaseGitHubManagerWithRepoUrl`

**No changes needed** - These tests don't use git.Repo (repo_url mode bypasses local git).

### Test Class: `TestBaseGitHubManagerParameterValidation`

**No changes needed** - These test parameter validation before git operations.

## HOW

### Pattern for Mock Replacement

**Old pattern:**
```python
with patch("...base_manager.git.Repo") as mock_repo_class:
    mock_repo = Mock(spec=git.Repo)
    mock_repo_class.return_value = mock_repo
    # Setup mock_repo.remotes, etc.
```

**New pattern:**
```python
with patch("...base_manager.git_operations.is_git_repository") as mock_is_git:
    mock_is_git.return_value = True  # or False for failure tests
```

**For _get_repository tests:**
```python
with patch("...base_manager.git_operations.get_github_repository_url") as mock_get_url:
    mock_get_url.return_value = "https://github.com/owner/repo"  # or None
```

## ALGORITHM

```
For each test that mocks git.Repo:
1. Remove git.Repo mock and git.InvalidGitRepositoryError
2. Add git_operations.is_git_repository mock with appropriate return value
3. For _get_repository tests, add git_operations.get_github_repository_url mock
4. Remove assertions about manager._repo (attribute no longer exists)
5. Keep all other assertions unchanged
```

## DATA

### Mock Return Values

| Function | Success Value | Failure Value |
|----------|---------------|---------------|
| `is_git_repository()` | `True` | `False` |
| `get_github_repository_url()` | `"https://github.com/owner/repo"` | `None` |

### Assertions to Remove
- `assert manager._repo == mock_repo`
- Any assertion checking `_repo` attribute

### Assertions to Keep
- `assert manager.project_dir == mock_path`
- `assert manager.github_token == "fake_token"`
- `assert manager._repository is None`
- All error message assertions

## Verification

After this step:
- All tests should pass
- No references to `git.Repo` or `git.InvalidGitRepositoryError` in test file
- Run: `pytest tests/utils/github_operations/test_base_manager.py -v`
