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

**Complete list of tests requiring updates (11 tests):**

| Test | Mock Changes |
|------|-------------|
| `test_successful_initialization_with_project_dir` | `is_git_repository` → `True`, remove `_repo` assertion |
| `test_initialization_fails_not_git_repository` | `is_git_repository` → `False` |
| `test_initialization_fails_no_github_token` | `is_git_repository` → `True` |
| `test_get_repository_with_project_dir_mode` | Both mocks (see pattern below) |
| `test_get_repository_caching` | Both mocks |
| `test_get_repository_no_origin_remote` | `is_git_repository` → `True`, `get_github_repository_url` → `None` |
| `test_get_repository_invalid_github_url` | `is_git_repository` → `True`, `get_github_repository_url` → GitLab URL |
| `test_get_repository_github_api_error` | Both mocks |
| `test_get_repository_generic_exception` | Both mocks |
| `test_ssh_url_format_parsing` | Both mocks |
| `test_https_url_without_git_extension` | Both mocks |

### Combined Mock Pattern

For tests that call both `__init__` and `_get_repository`, use both mocks:

```python
with (
    patch("...base_manager.git_operations.is_git_repository", return_value=True),
    patch("...base_manager.git_operations.get_github_repository_url", 
          return_value="https://github.com/test-owner/test-repo"),
    patch("...base_manager.user_config.get_config_value", return_value="fake_token"),
    patch("...base_manager.Github") as mock_github_class,
):
    # Test code here
```

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
