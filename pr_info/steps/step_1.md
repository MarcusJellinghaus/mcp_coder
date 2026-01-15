# Step 1: Add `rebase_onto_branch()` Function with Tests

## Overview

Add the core rebase function to `git_operations/branches.py` with comprehensive unit tests. This function handles the low-level git rebase operation including conflict detection and automatic abort.

## LLM Prompt

```
Implement Step 1 of the auto-rebase feature as described in pr_info/steps/summary.md.

Add the `rebase_onto_branch()` function to the git_operations module with tests.
Follow TDD: write tests first, then implement the function.
```

---

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/utils/git_operations/test_branches.py` | ADD test class `TestRebaseOntoBranch` |
| `src/mcp_coder/utils/git_operations/branches.py` | ADD function `rebase_onto_branch()` |
| `src/mcp_coder/utils/git_operations/__init__.py` | ADD export `rebase_onto_branch` |

---

## WHAT: Function Signature

```python
def rebase_onto_branch(project_dir: Path, target_branch: str) -> bool:
    """Attempt to rebase current branch onto origin/<target_branch>.
    
    Fetches from origin, then attempts rebase. If conflicts are detected,
    automatically aborts the rebase. All outcomes are logged internally.
    
    Args:
        project_dir: Path to the project directory containing git repository
        target_branch: Name of the branch to rebase onto (without 'origin/' prefix)
    
    Returns:
        True if rebase succeeded or branch is already up-to-date.
        False if rebase was skipped (conflicts, errors, etc.)
    
    Note:
        This function never raises exceptions - all errors are logged and
        result in False return value. Safe to call without try/except.
    """
```

---

## HOW: Integration Points

**Imports needed in branches.py:**
```python
from .remotes import fetch_remote  # Already available via relative import
```

**Export in __init__.py:**
```python
from .branches import (
    # ... existing exports ...
    rebase_onto_branch,
)

__all__ = [
    # ... existing exports ...
    "rebase_onto_branch",
]
```

---

## ALGORITHM: Core Logic (Pseudocode)

```python
def rebase_onto_branch(project_dir, target_branch):
    # 1. Validate inputs (is_git_repository, non-empty branch name)
    # 2. Fetch from origin (call fetch_remote)
    # 3. Try: repo.git.rebase(f"origin/{target_branch}")
    # 4. Catch GitCommandError:
    #    - Check if rebase in progress (.git/rebase-merge or .git/rebase-apply)
    #    - If yes: abort with repo.git.rebase("--abort"), return False
    #    - If "up to date" in message: log info, return True
    #    - Else: log warning, return False
    # 5. Success: log info, return True
```

---

## DATA: Return Values

| Scenario | Return | Log Level | Log Message |
|----------|--------|-----------|-------------|
| Rebase successful | `True` | INFO | "Successfully rebased onto origin/{branch}" |
| Already up-to-date | `True` | INFO | "Already up-to-date with origin/{branch}" |
| Conflicts detected | `False` | WARNING | "Skipping rebase: merge conflicts detected" |
| Fetch failed | `False` | WARNING | "Skipping rebase: failed to fetch from origin" |
| Invalid repository | `False` | DEBUG | "Not a git repository: {path}" |
| Other error | `False` | WARNING | "Skipping rebase: {error}" |

---

## TEST CASES

### Test Class: `TestRebaseOntoBranch`

```python
@pytest.mark.git_integration
class TestRebaseOntoBranch:
    """Tests for rebase_onto_branch function."""

    def test_rebase_onto_branch_success(self, git_repo_with_remote):
        """Test successful rebase when behind remote."""
        # Setup: create commits on remote that local doesn't have
        # Call rebase_onto_branch
        # Verify: returns True, local has remote commits

    def test_rebase_onto_branch_already_up_to_date(self, git_repo_with_remote):
        """Test rebase when already up-to-date."""
        # Setup: local and remote are in sync
        # Call rebase_onto_branch
        # Verify: returns True

    def test_rebase_onto_branch_conflict_aborts(self, git_repo_with_remote):
        """Test rebase aborts cleanly on conflict."""
        # Setup: create conflicting changes on local and remote
        # Call rebase_onto_branch
        # Verify: returns False, no rebase in progress, original state preserved

    def test_rebase_onto_branch_not_git_repo(self, tmp_path):
        """Test returns False for non-git directory."""
        # Verify: returns False

    def test_rebase_onto_branch_no_remote(self, git_repo_with_commit):
        """Test returns False when no origin remote."""
        # Verify: returns False (fetch fails)

    def test_rebase_onto_branch_invalid_target_branch(self, git_repo_with_remote):
        """Test returns False for non-existent target branch."""
        # Verify: returns False
```

---

## IMPLEMENTATION NOTES

1. **Conflict Detection**: After `GitCommandError`, check for `.git/rebase-merge` or `.git/rebase-apply` directories to confirm rebase is in progress before aborting.

2. **Up-to-date Detection**: GitPython's rebase may succeed with no changes, or may return a message containing "up to date". Handle both cases.

3. **Logging Pattern**: Follow existing patterns in `branches.py` - use `logger.debug()` for routine operations, `logger.info()` for success, `logger.warning()` for skip scenarios.

4. **No Exceptions**: Wrap entire function body in try/except to ensure no exceptions propagate to caller.
