# Step 2: Update prerequisites.py for Template Creation and Validation

## LLM Prompt

```
Implement Step 2 from pr_info/steps/summary.md:
Update check_prerequisites() in prerequisites.py to create TASK_TRACKER.md from template 
if missing, and validate structure if exists.
Follow TDD - write tests first, then implement.
```

## Overview

Modify `check_prerequisites()` in the implement workflow to validate task tracker:
- Fail if `pr_info/` folder is missing (must run `create_plan` first)
- Validate structure of existing `TASK_TRACKER.md`

**Note:** See [Decisions.md](./Decisions.md) (Decision 1) - no directory creation, only validation.

---

## Part A: Write Tests

### WHERE
`tests/workflows/implement/test_prerequisites.py`

### WHAT
Add tests for template creation and validation behavior.

### Test Cases

```python
class TestCheckPrerequisitesTaskTracker:
    """Tests for task tracker validation in check_prerequisites."""

    def test_fails_when_pr_info_missing(self) -> None:
        """Test returns False when pr_info/ folder is missing."""
        # Setup: git repo without pr_info/ dir
        # Call check_prerequisites()
        # Assert: returns False, logs "folder pr_info not found. Run 'create_plan' first."

    def test_validates_existing_tracker_success(self) -> None:
        """Test validation passes for valid existing tracker."""
        # Setup: git repo with valid TASK_TRACKER.md
        # Call check_prerequisites()
        # Assert: returns True, file unchanged

    def test_validates_existing_tracker_failure(self) -> None:
        """Test validation fails for invalid tracker structure."""
        # Setup: git repo with TASK_TRACKER.md missing ## Pull Request header
        # Call check_prerequisites()
        # Assert: returns False, logs error
```

---

## Part B: Implement Changes

### WHERE
`src/mcp_coder/workflows/implement/prerequisites.py`

### WHAT
Modify `check_prerequisites()` function.

### New Imports
```python
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerSectionNotFoundError,
    validate_task_tracker,
    # existing imports...
)
```

### ALGORITHM
```
1. Check if pr_info/ directory exists
2. If not exists: log error "folder pr_info not found. Run 'create_plan' first.", return False
3. Check if TASK_TRACKER.md exists
4. If not exists: log error, return False
5. Call validate_task_tracker() to validate structure
6. If validation raises exception: log error, return False
7. Continue with existing checks (git repo, etc.)
```

### Modified Function Signature
```python
def check_prerequisites(project_dir: Path) -> bool:
    """Verify dependencies and prerequisites are met.
    
    Now also handles TASK_TRACKER.md lifecycle:
    - Creates from template if missing
    - Validates structure if exists
    
    Args:
        project_dir: Path to the project directory

    Returns:
        True if all prerequisites are met, False otherwise
    """
```

### HOW
Insert task tracker logic after git repo check, before logging "Prerequisites check passed".

---

## Part C: Update Existing Behavior

### Current Behavior (to change)
```python
# Check if task tracker exists
task_tracker_path = project_dir / PR_INFO_DIR / "TASK_TRACKER.md"
if not task_tracker_path.exists():
    logger.error(f"{task_tracker_path} not found")
    return False
```

### New Behavior
```python
# Check pr_info directory exists (created by create_plan workflow)
pr_info_path = project_dir / PR_INFO_DIR
if not pr_info_path.exists():
    logger.error("folder pr_info not found. Run 'create_plan' first.")
    return False

# Check TASK_TRACKER.md exists
task_tracker_path = pr_info_path / "TASK_TRACKER.md"
if not task_tracker_path.exists():
    logger.error(f"{task_tracker_path} not found")
    return False

# Validate existing structure
try:
    validate_task_tracker(str(pr_info_path))
    logger.info("Task tracker structure validated")
except TaskTrackerSectionNotFoundError as e:
    logger.error(f"Invalid task tracker structure: {e}")
    return False
```

---

## Acceptance Criteria

- [ ] `check_prerequisites()` fails with clear error if `pr_info/` folder missing
- [ ] `check_prerequisites()` fails if `TASK_TRACKER.md` missing
- [ ] `check_prerequisites()` validates existing tracker structure
- [ ] Returns `False` with clear error if validation fails
- [ ] All tests pass
