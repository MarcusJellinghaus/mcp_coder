# Step 1: Add `remote_branch_exists()` Function

## LLM Prompt

```
Implement Step 1 of Issue #204: Add the `remote_branch_exists()` function.

Read the summary at `pr_info/steps/summary.md` for context, then implement this step.

Follow TDD: write tests first, then implement the function.
```

## Overview

Add a new function `remote_branch_exists()` to check if a branch exists on the remote origin.

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/utils/git_operations/conftest.py` | MODIFY - Add fixture |
| `tests/utils/git_operations/test_branches.py` | MODIFY - Add tests |
| `src/mcp_coder/utils/git_operations/branches.py` | MODIFY - Add function |
| `src/mcp_coder/utils/git_operations/__init__.py` | MODIFY - Export function |

## WHAT: Function Signature

```python
def remote_branch_exists(project_dir: Path, branch_name: str) -> bool:
    """Check if a git branch exists on the remote origin.

    Args:
        project_dir: Path to the project directory containing git repository
        branch_name: Name of the branch to check (without 'origin/' prefix)

    Returns:
        True if branch exists on origin remote, False otherwise
    """
```

## HOW: Integration Points

### 1. Test Fixture (conftest.py)

Add fixture that creates a repo with a bare remote:

```python
@pytest.fixture
def git_repo_with_remote(tmp_path: Path) -> tuple[Repo, Path, Path]:
    """Create git repository with a bare remote origin.
    
    Returns:
        tuple[Repo, Path, Path]: (repo, project_dir, bare_remote_dir)
    """
```

### 2. Imports in branches.py

No new imports needed - already has `Repo`, `GitCommandError`, etc.

### 3. Export in __init__.py

Add to imports and `__all__` list:
```python
from .branches import remote_branch_exists
```

## ALGORITHM: Core Logic (5 lines)

```python
# 1. Validate: is_git_repository, branch_name not empty
# 2. Open repo with _safe_repo_context
# 3. Check if "origin" in repo.remotes, return False if not
# 4. Get remote refs: [ref.name for ref in repo.remotes.origin.refs]
# 5. Return f"origin/{branch_name}" in remote_refs
```

## DATA: Return Values

| Scenario | Return |
|----------|--------|
| Branch exists on origin | `True` |
| Branch doesn't exist on origin | `False` |
| No origin remote | `False` |
| Invalid repository | `False` |
| Empty branch name | `False` |

## Test Cases

### Test 1: Remote branch exists
```python
def test_remote_branch_exists_returns_true(self, git_repo_with_remote):
    """Test remote_branch_exists returns True for existing remote branch."""
    repo, project_dir, _ = git_repo_with_remote
    # Push current branch to remote
    repo.git.push("-u", "origin", "main")
    assert remote_branch_exists(project_dir, "main") is True
```

### Test 2: Remote branch doesn't exist
```python
def test_remote_branch_exists_returns_false_for_nonexistent(self, git_repo_with_remote):
    """Test remote_branch_exists returns False for non-existing remote branch."""
    _, project_dir, _ = git_repo_with_remote
    assert remote_branch_exists(project_dir, "nonexistent-branch") is False
```

### Test 3: No origin remote
```python
def test_remote_branch_exists_returns_false_no_origin(self, git_repo_with_commit):
    """Test remote_branch_exists returns False when no origin remote."""
    _, project_dir = git_repo_with_commit
    assert remote_branch_exists(project_dir, "main") is False
```

### Test 4: Invalid inputs
```python
def test_remote_branch_exists_invalid_inputs(self, tmp_path):
    """Test remote_branch_exists returns False for invalid inputs."""
    assert remote_branch_exists(tmp_path, "main") is False  # Not a repo
```

## Implementation Order

1. Add `git_repo_with_remote` fixture to `conftest.py`
2. Add test class `TestRemoteBranchExists` to `test_branches.py`
3. Implement `remote_branch_exists()` in `branches.py`
4. Add export to `__init__.py`
5. Run tests to verify
