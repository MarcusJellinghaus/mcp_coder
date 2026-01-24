# Step 1: Implement Rebase Detection Utility

## LLM Prompt
```
Based on the summary document and this step, implement rebase detection functionality in the git operations module. 

Add a `needs_rebase()` function to `src/mcp_coder/utils/git_operations/branches.py` that detects if the current branch needs rebasing onto its parent branch using `git merge-base`. Follow the existing code patterns in the file and write comprehensive tests first.

Reference the summary document for data structures and integration requirements.
```

## WHERE
- **File**: `src/mcp_coder/utils/git_operations/branches.py`
- **Test File**: `tests/utils/git_operations/test_branches.py`

## WHAT

### New Function
```python
def needs_rebase(project_dir: Path, target_branch: Optional[str] = None) -> Tuple[bool, str]:
    """Detect if current branch needs rebasing onto target branch.
    
    Args:
        project_dir: Path to git repository
        target_branch: Branch to check against (defaults to auto-detect)
    
    Returns:
        (needs_rebase, reason)
    """
```

### Test Functions
```python
def test_needs_rebase_up_to_date()
def test_needs_rebase_behind()
def test_needs_rebase_invalid_repo()
def test_needs_rebase_no_remote()
```

## HOW

### Integration Points
- Import existing utilities: `is_git_repository`, `fetch_remote`, `_safe_repo_context`
- Use existing logger from module
- Follow existing error handling patterns in the file

### Algorithm
```
1. Validate git repo and fetch from remote
2. Get current branch and determine target (auto-detect if needed)  
3. Run `git merge-base --is-ancestor origin/target HEAD`
4. If ancestor: UP_TO_DATE, if not: NEEDS_REBASE with commit count
```

## DATA

### Return Structure
```python
# Return tuple meaning:
# (needs_rebase: bool, reason: str)

# Examples:
(False, "up-to-date")           # No rebase needed
(True, "3 commits behind")      # Rebase needed
(False, "error: <reason>")      # Error occurred
```

### Target Branch Detection Priority
1. Function parameter if provided
2. GitHub PR base branch (if open PR exists)
3. Default branch (main/master) via `get_default_branch_name()`

## Implementation Notes
- **Error Handling**: Return `(False, "error: <reason>")` on failures
- **Logging**: Use debug level for normal operations, warning for issues
- **Git Commands**: Use GitPython's `repo.git` interface for merge-base operations
- **Graceful Degradation**: Handle missing remotes, network issues, invalid branches