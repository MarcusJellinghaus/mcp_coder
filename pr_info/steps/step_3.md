# Step 3: Branch Management and Directory Verification

## Objective

Implement branch management (get existing or create new linked branch) and verify pr_info/steps/ directory is empty.

## Files to Modify

- `workflows/create_plan.py` - Add branch management and directory verification functions

## Implementation Details

### WHERE
- `workflows/create_plan.py` - Add `manage_branch()` and `verify_steps_directory()` functions

### WHAT

```python
def manage_branch(project_dir: Path, issue_number: int, issue_title: str) -> Optional[str]:
    """Get existing linked branch or create new one.
    
    Returns:
        Branch name if successful, None on error
    """

def verify_steps_directory(project_dir: Path) -> bool:
    """Verify pr_info/steps/ directory is empty or doesn't exist.
    
    Returns:
        True if empty/non-existent, False if contains files
    """
```

### HOW

**Imports:**
```python
from typing import Optional
from mcp_coder.utils import checkout_branch
from mcp_coder.utils.github_operations.issue_branch_manager import IssueBranchManager
```

**manage_branch():**
- Use IssueBranchManager to check for linked branches
- If branches exist, use first one
- If no branches, create new branch on GitHub
- Checkout the branch locally
- Return branch name

**verify_steps_directory():**
- Use pathlib.Path to check directory
- If doesn't exist, return True
- If exists but empty, return True
- If exists and has files, log error and return False

### ALGORITHM

**manage_branch():**
```
1. Create IssueBranchManager instance
2. Get linked branches: linked_branches = manager.get_linked_branches(issue_number)
3. If linked_branches is not empty:
   - branch_name = linked_branches[0]
   - Log "Using existing linked branch: {branch_name}"
4. Else:
   - result = manager.create_remote_branch_for_issue(issue_number)
   - If not result["success"]: log error, return None
   - branch_name = result["branch_name"]
   - Log "Created new branch: {branch_name}"
5. Checkout branch: checkout_branch(project_dir, branch_name)
6. Log "Switched to branch: {branch_name}"
7. Return branch_name
```

**verify_steps_directory():**
```
1. steps_dir = project_dir / "pr_info" / "steps"
2. If not steps_dir.exists(): return True
3. files = list(steps_dir.iterdir())
4. If len(files) == 0: return True
5. Log error: "Directory pr_info/steps/ contains files. Please clean manually."
6. For each file: log "  - {file.name}"
7. Return False
```

### DATA

**manage_branch() returns:**
```python
Optional[str]  # Branch name or None on error
```

**verify_steps_directory() returns:**
```python
bool  # True if clean, False if files exist
```

## Testing

Create `tests/workflows/create_plan/test_branch_management.py`:

```python
def test_manage_branch_existing_branch()
def test_manage_branch_create_new_branch()
def test_manage_branch_create_failure()
def test_manage_branch_checkout_failure()
def test_verify_steps_directory_not_exists()
def test_verify_steps_directory_empty()
def test_verify_steps_directory_has_files()
```

## Acceptance Criteria

- [ ] Function checks for existing linked branches
- [ ] Function creates new branch if none exist
- [ ] Function checks out the branch locally
- [ ] Function returns branch name on success
- [ ] Directory verification detects non-existent directory (OK)
- [ ] Directory verification detects empty directory (OK)
- [ ] Directory verification detects files (Error)
- [ ] Directory verification lists all files found
- [ ] All tests pass with mocked GitHub and git operations

## LLM Prompt for Implementation

```
Please implement Step 3 of the create_plan workflow.

Reference the summary at pr_info/steps/summary.md and previous steps.

Add manage_branch() and verify_steps_directory() functions to workflows/create_plan.py.

Key requirements:
- Use IssueBranchManager.get_linked_branches() to check for existing branches
- Use IssueBranchManager.create_remote_branch_for_issue() to create if needed
- Use checkout_branch() from utils.git_operations to switch branches
- Directory verification must be strict: error if ANY files exist
- Log all operations clearly with branch names

Implement the tests as specified with proper mocking.
```
