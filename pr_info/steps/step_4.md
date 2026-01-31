# Step 4: Update create_plan.py for Directory Lifecycle

## LLM Prompt

```
Implement Step 4 from pr_info/steps/summary.md:
Update create_plan.py to fail if pr_info/ exists, create directory structure at start,
and remove verify_steps_directory() function.
Follow TDD - write tests first, then implement.
```

## Overview

Modify `create_plan.py` to enforce clean state before planning:
- Fail early if `pr_info/` already exists
- Create the full directory structure at workflow start
- Remove the now-unnecessary `verify_steps_directory()` function

---

## Part A: Write Tests

### WHERE
`tests/workflows/create_plan/test_prerequisites.py`

### WHAT
Add tests for existence check and directory creation.

### Test Cases

```python
class TestPrInfoDirectoryLifecycle:
    """Tests for pr_info/ directory lifecycle in create_plan."""

    def test_fails_if_pr_info_exists(self) -> None:
        """Test workflow fails if pr_info/ directory already exists."""
        # Setup: create pr_info/ directory
        # Call run_create_plan_workflow() or check_pr_info_exists()
        # Assert: returns error code, logs clear error message

    def test_creates_pr_info_directory_structure(self) -> None:
        """Test workflow creates pr_info/, steps/, .conversations/ directories and TASK_TRACKER.md."""
        # Setup: temp dir without pr_info/
        # Call create_pr_info_structure()
        # Assert: all three directories exist
        # Assert: TASK_TRACKER.md exists with template content

    def test_error_message_is_clear(self) -> None:
        """Test error message tells user to clean up manually."""
        # Setup: create pr_info/ directory
        # Call the check function
        # Assert: error message contains "pr_info/ directory already exists"
        # Assert: error message contains "clean up"
```

---

## Part B: Add Existence Check Function

### WHERE
`src/mcp_coder/workflows/create_plan.py`

### WHAT
```python
def check_pr_info_not_exists(project_dir: Path) -> bool:
    """Check that pr_info/ directory does not exist.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        True if pr_info/ does not exist, False if it exists
    """
```

### ALGORITHM
```
1. Build path: project_dir / "pr_info"
2. If exists: log error with cleanup message, return False
3. Return True
```

---

## Part C: Add Directory Creation Function

### WHERE
`src/mcp_coder/workflows/create_plan.py`

### New Import
```python
from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
```

### WHAT
```python
def create_pr_info_structure(project_dir: Path) -> bool:
    """Create pr_info/ directory structure and TASK_TRACKER.md.
    
    Creates:
    - pr_info/
    - pr_info/steps/
    - pr_info/.conversations/
    - pr_info/TASK_TRACKER.md (from template)
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        True if successful, False on error
    """
```

### ALGORITHM
```
1. Build base path: project_dir / "pr_info"
2. Create pr_info/ directory
3. Create pr_info/steps/ directory
4. Create pr_info/.conversations/ directory
5. Write TASK_TRACKER_TEMPLATE to pr_info/TASK_TRACKER.md
6. Log success, return True
7. On exception: log error, return False
```

**Note:** See [Decisions.md](./Decisions.md) (Decisions 3, 4, 5) for .conversations/, template creation, and template content.

---

## Part D: Update Workflow Function

### WHERE
`src/mcp_coder/workflows/create_plan.py` - `run_create_plan_workflow()`

### Current Flow (to modify)
```python
# Step 3: Verify pr_info/steps/ is empty
logger.info("Step 3/7: Verifying pr_info/steps/ is empty...")
if not verify_steps_directory(project_dir):
    logger.error("Steps directory verification failed")
    return 1
```

### New Flow
```python
# Step 3: Check pr_info/ doesn't exist and create structure
logger.info("Step 3/7: Setting up pr_info/ directory structure...")
if not check_pr_info_not_exists(project_dir):
    logger.error("pr_info/ directory already exists. Please clean up before creating a new plan.")
    return 1

if not create_pr_info_structure(project_dir):
    logger.error("Failed to create pr_info/ directory structure")
    return 1
```

---

## Part E: Remove Obsolete Function

### Function to Delete
```python
def verify_steps_directory(project_dir: Path) -> bool:
    """Verify pr_info/steps/ directory is empty or doesn't exist."""
    # ... entire function to be removed
```

### Tests to Remove
- Remove tests for `verify_steps_directory` in `test_prerequisites.py` or relevant test file

---

## Acceptance Criteria

- [ ] `check_pr_info_not_exists()` function added
- [ ] `create_pr_info_structure()` function added
- [ ] `run_create_plan_workflow()` updated to use new functions
- [ ] `verify_steps_directory()` function removed
- [ ] Error message is clear: "pr_info/ directory already exists. Please clean up before creating a new plan."
- [ ] All tests pass
