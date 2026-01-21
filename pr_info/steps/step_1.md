# Step 1: Add pre-check for no changes in commit_all_changes()

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #123 - commit_all_changes: return success when no changes to commit

## Overview
Add a test for the "no changes" scenario and implement a pre-check in `commit_all_changes()` that returns success early when there are no changes to commit.

---

## Part A: Test Implementation

### WHERE
`tests/utils/git_operations/test_commits.py`

### WHAT
Add new test method to `TestCommitOperations` class:

```python
def test_commit_all_changes_no_changes_returns_success(
    self, git_repo: tuple[Repo, Path]
) -> None:
```

### HOW
- Add test within existing `TestCommitOperations` class
- Use existing `git_repo` fixture (provides clean repo with no commits)
- No new imports required

### ALGORITHM (Test)
```
1. Get repo and project_dir from git_repo fixture
2. Do NOT create any files (repo is clean)
3. Call commit_all_changes("Test message", project_dir)
4. Assert result["success"] is True
5. Assert result["commit_hash"] is None
6. Assert result["error"] is None
```

### DATA
- Input: Clean git repository with no changes
- Expected output: `{"success": True, "commit_hash": None, "error": None}`

---

## Part B: Implementation

### WHERE
`src/mcp_coder/utils/git_operations/commits.py`

### WHAT
Modify `commit_all_changes()` function to add pre-check:

```python
def commit_all_changes(message: str, project_dir: Path) -> CommitResult:
```

### HOW
1. Add import for `get_full_status` from `.repository`
2. Add pre-check after repository validation, before staging

### ALGORITHM (Implementation)
```
1. (existing) Validate project_dir is git repository
2. NEW: Call get_full_status(project_dir)
3. NEW: Check if staged, modified, and untracked are all empty
4. NEW: If no changes, log INFO "No changes to commit" and return success
5. (existing) Stage all changes
6. (existing) Commit staged files
```

### DATA
- Function signature unchanged: `commit_all_changes(message: str, project_dir: Path) -> CommitResult`
- New return case: `{"success": True, "commit_hash": None, "error": None}` when no changes
- Existing return cases unchanged

### CODE CHANGES

#### Import addition (line ~12):
```python
from .repository import get_staged_changes, is_git_repository, get_full_status
```

#### Pre-check addition (after line ~103, after repository validation):
```python
    # Check if there are any changes to commit
    status = get_full_status(project_dir)
    if not status["staged"] and not status["modified"] and not status["untracked"]:
        logger.info("No changes to commit")
        return {"success": True, "commit_hash": None, "error": None}
```

---

## LLM Prompt

```
You are implementing Issue #123: commit_all_changes returns success when no changes to commit.

Reference: pr_info/steps/summary.md and pr_info/steps/step_1.md

TASK: Implement Step 1 - Add pre-check for no changes in commit_all_changes()

1. FIRST, add a test in tests/utils/git_operations/test_commits.py:
   - Add test_commit_all_changes_no_changes_returns_success() to TestCommitOperations class
   - Test that calling commit_all_changes on a clean repo returns success=True, commit_hash=None

2. THEN, modify src/mcp_coder/utils/git_operations/commits.py:
   - Add get_full_status to the import from .repository
   - In commit_all_changes(), after the is_git_repository check, add a pre-check:
     - Call get_full_status(project_dir)
     - If staged, modified, and untracked are all empty lists
     - Log at INFO level: "No changes to commit"
     - Return {"success": True, "commit_hash": None, "error": None}

3. Run tests to verify: pytest tests/utils/git_operations/test_commits.py -v

Keep changes minimal. Do not modify commit_staged_files() or any other functions.
```

---

## Verification
```bash
# Run the specific test file
pytest tests/utils/git_operations/test_commits.py -v -m git_integration

# Run just the new test
pytest tests/utils/git_operations/test_commits.py::TestCommitOperations::test_commit_all_changes_no_changes_returns_success -v
```
