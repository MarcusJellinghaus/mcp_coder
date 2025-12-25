# Step 2: Update `get_branch_diff()` with Remote Fallback

## LLM Prompt

```
Implement Step 2 of Issue #204: Update `get_branch_diff()` to fall back to remote ref.

Read the summary at `pr_info/steps/summary.md` for context, then implement this step.

Prerequisite: Step 1 must be completed (remote_branch_exists function).

Follow TDD: write tests first, then modify the function.
```

## Overview

Modify `get_branch_diff()` to use `origin/{base_branch}` when the local branch doesn't exist but the remote ref is available.

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/utils/git_operations/test_diffs.py` | MODIFY - Add test for remote fallback |
| `src/mcp_coder/utils/git_operations/diffs.py` | MODIFY - Add fallback logic |

## WHAT: Modified Function

```python
def get_branch_diff(
    project_dir: Path,
    base_branch: Optional[str] = None,
    exclude_paths: Optional[list[str]] = None,
) -> str:
    """Generate git diff between current branch and base branch.
    
    [existing docstring...]
    
    Note:
        - If base_branch doesn't exist locally but exists on origin,
          falls back to using origin/{base_branch} for comparison.
    """
```

## HOW: Integration Points

### 1. New Import in diffs.py

Add `remote_branch_exists` to existing import:

```python
from .branches import branch_exists, get_current_branch_name, get_parent_branch_name, remote_branch_exists
```

### 2. Modification Location

In `get_branch_diff()`, after the `branch_exists` check:

**Current code:**
```python
# Verify base branch exists
if not branch_exists(project_dir, base_branch):
    logger.error("Base branch '%s' does not exist", base_branch)
    return ""
```

**New code:**
```python
# Verify base branch exists (local or remote)
if not branch_exists(project_dir, base_branch):
    # Try remote ref as fallback
    if remote_branch_exists(project_dir, base_branch):
        logger.debug(
            "Local branch '%s' not found, using remote ref 'origin/%s'",
            base_branch,
            base_branch,
        )
        base_branch = f"origin/{base_branch}"
    else:
        logger.error("Base branch '%s' does not exist locally or on remote", base_branch)
        return ""
```

## ALGORITHM: Modified Logic (6 lines)

```python
# 1. Check if local branch exists (existing)
# 2. If not, check if remote branch exists (NEW)
# 3. If remote exists, update base_branch to "origin/{base_branch}" (NEW)
# 4. Log at DEBUG level when using remote fallback (NEW)
# 5. If neither exists, ERROR log and return "" (existing, updated message)
# 6. Continue with diff using base_branch variable (existing)
```

## DATA: Behavior Changes

| Scenario | Before | After |
|----------|--------|-------|
| Local branch exists | Works | Works (unchanged) |
| Local missing, remote exists | ERROR, return "" | DEBUG log, use remote ref |
| Neither exists | ERROR, return "" | ERROR (updated message), return "" |

## Test Case

### Test: Remote fallback when local branch missing

```python
def test_get_branch_diff_falls_back_to_remote(
    self, git_repo_with_remote: tuple[Repo, Path, Path]
) -> None:
    """Test get_branch_diff falls back to remote ref when local branch missing."""
    repo, project_dir, _ = git_repo_with_remote
    
    # Get initial branch name (main)
    initial_branch = get_current_branch_name(project_dir)
    
    # Push main to remote
    repo.git.push("-u", "origin", initial_branch)
    
    # Create feature branch with changes
    create_branch("feature-branch", project_dir)
    feature_file = project_dir / "feature.py"
    feature_file.write_text("# Feature file")
    commit_all_changes("Add feature file", project_dir)
    
    # Delete local main branch (simulating CI environment)
    repo.git.branch("-D", initial_branch)
    
    # Verify local main doesn't exist
    assert branch_exists(project_dir, initial_branch) is False
    
    # get_branch_diff should still work using origin/main
    diff = get_branch_diff(project_dir, initial_branch)
    
    assert diff != ""
    assert "feature.py" in diff
    assert "# Feature file" in diff
```

## Implementation Order

1. Add test `test_get_branch_diff_falls_back_to_remote` to `test_diffs.py`
2. Add `remote_branch_exists` import to `diffs.py`
3. Modify `get_branch_diff()` with fallback logic
4. Run tests to verify


