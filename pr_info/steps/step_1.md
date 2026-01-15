# Step 1: Add `rebase_onto_branch()` Function and `force_with_lease` Parameter with Tests

## Overview

Add the core rebase function to `git_operations/branches.py` and extend `git_push()` in `remotes.py` with `force_with_lease` support. This step handles all low-level git operations including conflict detection, automatic abort, and safe force push capability.

## LLM Prompt

```
Implement Step 1 of the auto-rebase feature as described in pr_info/steps/summary.md.

1. Add `force_with_lease` parameter to `git_push()` in remotes.py with tests.
2. Add the `rebase_onto_branch()` function to branches.py with tests.
Follow TDD: write tests first, then implement the functions.
```

---

## WHERE: File Locations

| File | Action |
|------|--------|
| `tests/utils/git_operations/test_remotes.py` | ADD test class `TestGitPushForceWithLease` |
| `src/mcp_coder/utils/git_operations/remotes.py` | MODIFY `git_push()` to add `force_with_lease` parameter |
| `tests/utils/git_operations/test_branches.py` | ADD test class `TestRebaseOntoBranch` |
| `src/mcp_coder/utils/git_operations/branches.py` | ADD function `rebase_onto_branch()` |
| `src/mcp_coder/utils/git_operations/__init__.py` | ADD export `rebase_onto_branch` |

---

## WHAT: Function Signatures

### Modified: `git_push()` in remotes.py

```python
def git_push(project_dir: Path, force_with_lease: bool = False) -> dict[str, Any]:
    """
    Push current branch to origin remote.

    Args:
        project_dir: Path to the project directory containing git repository
        force_with_lease: If True, use --force-with-lease for safe force push (default: False)

    Returns:
        Dictionary containing:
        - success: True if push succeeded, False otherwise
        - error: Error message if failed, None if successful
    """
```

### New: `rebase_onto_branch()` in branches.py

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

### Test Class: `TestGitPushForceWithLease`

```python
@pytest.mark.git_integration
class TestGitPushForceWithLease:
    """Tests for git_push with force_with_lease parameter."""

    def test_git_push_default_no_force(self, git_repo_with_remote):
        """Test default push without force flag."""
        # Setup: push normally
        # Verify: regular push succeeds

    def test_git_push_force_with_lease_after_rebase(self, git_repo_with_remote):
        """Test force push with lease succeeds after rebase."""
        # Setup: create diverged history (local rebased, remote has old commits)
        # Call git_push with force_with_lease=True
        # Verify: returns success=True

    def test_git_push_force_with_lease_fails_on_unexpected_remote(self, git_repo_with_remote):
        """Test force with lease fails if remote has unexpected commits."""
        # Setup: someone else pushed to remote after our last fetch
        # Call git_push with force_with_lease=True
        # Verify: returns success=False (safe failure)
```

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
