# Step 4: Update `create_pr/core.py` to Use `detect_base_branch()`

## LLM Prompt
```
Implement Step 4 of Issue #388: Update create_pr/core.py to use detect_base_branch().

Reference: pr_info/steps/summary.md for full context.

This step replaces get_parent_branch_name() calls with detect_base_branch() 
and adds proper None handling with clear error messages.
```

## Overview

Replace all `get_parent_branch_name()` calls with `detect_base_branch()` in `create_pr/core.py` and handle `None` return values with appropriate error messages.

---

## WHERE: Files to Modify

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/create_pr/core.py` | Replace function calls |
| `tests/workflows/create_pr/test_prerequisites.py` | Update mocks |
| `tests/workflows/create_pr/test_workflow.py` | Update mocks |

---

## WHAT: Changes to `create_pr/core.py`

### Update Imports

```python
# BEFORE
from mcp_coder.utils import (
    commit_all_changes,
    get_branch_diff,
    get_current_branch_name,
    get_parent_branch_name,  # DELETE
    git_push,
    is_working_directory_clean,
)

# AFTER
from mcp_coder.utils import (
    commit_all_changes,
    get_branch_diff,
    get_current_branch_name,
    git_push,
    is_working_directory_clean,
)
from mcp_coder.workflow_utils.base_branch import detect_base_branch  # ADD
```

### Update `check_prerequisites()`

```python
# BEFORE (around line 175-185)
# Check current branch
try:
    current_branch = get_current_branch_name(project_dir)
    if current_branch is None:
        logger.error("Could not determine current branch (possibly detached HEAD)")
        return False

    parent_branch = get_parent_branch_name(project_dir)
    if parent_branch is None:
        logger.error("Could not determine parent branch")
        return False
    ...

# AFTER
# Check current branch
try:
    current_branch = get_current_branch_name(project_dir)
    if current_branch is None:
        logger.error("Could not determine current branch (possibly detached HEAD)")
        return False

    parent_branch = detect_base_branch(project_dir, current_branch=current_branch)
    if parent_branch is None:
        logger.error(
            "Could not detect base branch for PR creation.\n"
            "Tip: Add '### Base Branch' section to your GitHub issue with the target branch name."
        )
        return False
    ...
```

### Update `create_pull_request()`

```python
# BEFORE (around line 220-230)
def create_pull_request(project_dir: Path, title: str, body: str) -> bool:
    ...
    try:
        # Get current and parent branches
        current_branch = get_current_branch_name(project_dir)
        if current_branch is None:
            logger.error("Could not determine current branch")
            return False

        parent_branch = get_parent_branch_name(project_dir)
        if parent_branch is None:
            logger.error("Could not determine parent branch")
            return False
        ...

# AFTER
def create_pull_request(project_dir: Path, title: str, body: str) -> bool:
    ...
    try:
        # Get current and base branches
        current_branch = get_current_branch_name(project_dir)
        if current_branch is None:
            logger.error("Could not determine current branch")
            return False

        base_branch = detect_base_branch(project_dir, current_branch=current_branch)
        if base_branch is None:
            logger.error(
                "Could not detect base branch for PR creation.\n"
                "Tip: Add '### Base Branch' section to your GitHub issue."
            )
            return False
        
        # Create PR using PullRequestManager
        pr_manager = PullRequestManager(project_dir)
        pr_result = pr_manager.create_pull_request(
            title=title,
            head_branch=current_branch,
            base_branch=base_branch,  # Was: parent_branch
            body=body,
        )
        ...
```

### Update `generate_pr_summary()` 

The `generate_pr_summary()` function calls `get_branch_diff()`. Since we changed `get_branch_diff()` to require explicit `base_branch`, we need to pass it:

```python
# BEFORE (around line 130)
def generate_pr_summary(...) -> Tuple[str, str]:
    ...
    # Get branch diff
    logger.info("Getting branch diff...")
    diff_content = get_branch_diff(project_dir, exclude_paths=["pr_info/steps/"])
    ...

# AFTER
def generate_pr_summary(...) -> Tuple[str, str]:
    ...
    # Get base branch for diff
    current_branch = get_current_branch_name(project_dir)
    base_branch = detect_base_branch(project_dir, current_branch=current_branch)
    if base_branch is None:
        logger.error("Could not detect base branch for PR summary generation")
        return "Pull Request", "Could not generate summary - base branch unknown"
    
    # Get branch diff
    logger.info("Getting branch diff...")
    diff_content = get_branch_diff(
        project_dir, 
        base_branch=base_branch,  # ADD explicit base_branch
        exclude_paths=["pr_info/steps/"]
    )
    ...
```

---

## HOW: Variable Naming Convention

Change variable names from `parent_branch` to `base_branch` for clarity:
- `parent_branch` → `base_branch` (more accurate terminology)

---

## ALGORITHM: N/A

No new algorithms - just function call replacement.

---

## DATA: N/A

No data structure changes.

---

## TEST: Update Mocks

### File: `tests/workflows/create_pr/test_prerequisites.py`

Update mocks to use `detect_base_branch` instead of `get_parent_branch_name`:

```python
# BEFORE
@patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
def test_check_prerequisites_no_parent_branch(self, mock_parent, ...):
    mock_parent.return_value = None
    ...

# AFTER
@patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
def test_check_prerequisites_no_base_branch(self, mock_base, ...):
    mock_base.return_value = None
    ...
```

### File: `tests/workflows/create_pr/test_workflow.py`

Similar mock updates for workflow tests.

---

## ACCEPTANCE CRITERIA

- [ ] `get_parent_branch_name` import removed from `core.py`
- [ ] `detect_base_branch` imported from `workflow_utils.base_branch`
- [ ] `check_prerequisites()` uses `detect_base_branch()` with `None` handling
- [ ] `create_pull_request()` uses `detect_base_branch()` with `None` handling  
- [ ] `generate_pr_summary()` passes explicit `base_branch` to `get_branch_diff()`
- [ ] Error messages include helpful tip about `### Base Branch` section
- [ ] Variable names changed from `parent_branch` to `base_branch`
- [ ] All test mocks updated
- [ ] PR is created against correct base branch (not always main)
