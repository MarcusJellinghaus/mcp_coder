# Step 2: Implement Graceful Handling for Missing TASK_TRACKER.md (TDD - Green Phase)

## Context
Now that we have a failing test (Red phase), implement the fix to make it pass (Green phase).

Refer to `pr_info/steps/summary.md` for overall architecture and design decisions.

## WHERE: File Locations
- **Source File**: `src/mcp_coder/workflows/create_pr/core.py`
- **Function**: `check_prerequisites()` (lines 252-263)
- **Import Section**: Line 30 (existing task_tracker import)

## WHAT: Function Modification
**Function signature remains unchanged:**
```python
def check_prerequisites(project_dir: Path) -> bool:
```

**Only modify exception handling block**

## HOW: Integration Points

### Import Update (Line 30)
**Before:**
```python
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks
```

**After:**
```python
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    get_incomplete_tasks,
)
```

### Exception Handling Pattern
Follow the existing pattern from `implement` workflow (`src/mcp_coder/workflows/implement/core.py`, line 838):
```python
except TaskTrackerFileNotFoundError:
    logger.info("TASK_TRACKER.md not found - skipping task completeness check")
    # Continue to next check (don't return False)
```

## ALGORITHM: Exception Handling Logic (Pseudocode)
```
1. Try: Call get_incomplete_tasks(pr_info_dir)
2. If incomplete_tasks exist:
   - Log errors
   - Return False (fail prerequisites)
3. Else: Log success
4. Catch TaskTrackerFileNotFoundError specifically:
   - Log INFO message
   - Continue to next prerequisite check (no return)
5. Catch all other Exception:
   - Log ERROR message
   - Return False (fail prerequisites)
```

## DATA: Return Values
- **True**: All prerequisites pass OR task tracker missing (graceful degradation)
- **False**: Any genuine error (dirty git, incomplete tasks, branch issues, unexpected exceptions)

## Implementation Code

### Location: Lines 252-263 (approximate)

**Before:**
```python
# Check for incomplete tasks
try:
    pr_info_dir = str(project_dir / "pr_info")
    incomplete_tasks = get_incomplete_tasks(pr_info_dir)
    if incomplete_tasks:
        logger.error(f"Found {len(incomplete_tasks)} incomplete tasks:")
        for task in incomplete_tasks:
            logger.error(f"  - {task}")
        logger.error("Please complete all tasks before creating PR.")
        return False
    logger.info("✓ No incomplete tasks found")
except Exception as e:
    logger.error(f"Error checking incomplete tasks: {e}")
    return False
```

**After:**
```python
# Check for incomplete tasks
try:
    pr_info_dir = str(project_dir / "pr_info")
    incomplete_tasks = get_incomplete_tasks(pr_info_dir)
    if incomplete_tasks:
        logger.error(f"Found {len(incomplete_tasks)} incomplete tasks:")
        for task in incomplete_tasks:
            logger.error(f"  - {task}")
        logger.error("Please complete all tasks before creating PR.")
        return False
    logger.info("✓ No incomplete tasks found")
except TaskTrackerFileNotFoundError:
    logger.info("TASK_TRACKER.md not found - skipping task completeness check")
    # Continue with other prerequisites - task tracker is optional
except Exception as e:
    logger.error(f"Error checking incomplete tasks: {e}")
    return False
```

## Key Changes Summary
1. ✅ Added `TaskTrackerFileNotFoundError` to imports
2. ✅ Added specific exception handler before general Exception handler
3. ✅ INFO-level logging (not ERROR) for missing file
4. ✅ No return statement in TaskTrackerFileNotFoundError handler (continues to next check)
5. ✅ General Exception handler preserved (still fails on unexpected errors)

## Verification Commands

```bash
# Run the new test (should now pass)
pytest tests/workflows/create_pr/test_prerequisites.py::TestCheckPrerequisites::test_prerequisites_missing_task_tracker -v

# Expected output:
# PASSED

# Run the existing exception test (should still pass)
pytest tests/workflows/create_pr/test_prerequisites.py::TestCheckPrerequisites::test_prerequisites_task_tracker_exception -v

# Expected output:
# PASSED

# Run all prerequisite tests
pytest tests/workflows/create_pr/test_prerequisites.py -v
```

## LLM Prompt for Implementation

```
I need to implement Step 2 of the plan in pr_info/steps/step_2.md.

Please:
1. Read pr_info/steps/summary.md for overall context
2. Read pr_info/steps/step_2.md for detailed requirements
3. Update the import statement in src/mcp_coder/workflows/create_pr/core.py to include TaskTrackerFileNotFoundError
4. Modify the exception handling in check_prerequisites() function (lines 252-263) to:
   - Add a specific handler for TaskTrackerFileNotFoundError that logs INFO and continues
   - Keep the general Exception handler that logs ERROR and returns False
5. Follow the exact implementation code provided in step_2.md
6. Run the tests to verify both the new and existing tests pass (Green phase)

This follows the existing pattern from the implement workflow.
```

## Success Criteria
- ✅ Import statement updated correctly
- ✅ TaskTrackerFileNotFoundError handled with INFO log and continuation
- ✅ General exceptions still handled with ERROR log and return False
- ✅ New test `test_prerequisites_missing_task_tracker` PASSES
- ✅ Existing test `test_prerequisites_task_tracker_exception` still PASSES
- ✅ All other prerequisite tests still pass
- ✅ No syntax errors or import errors

## Expected Test Results
**Status**: ✅ PASS (Green phase - test now passes)

All tests in `test_prerequisites.py` should pass:
- ✅ test_prerequisites_all_pass
- ✅ test_prerequisites_dirty_working_directory
- ✅ test_prerequisites_incomplete_tasks
- ✅ test_prerequisites_same_branch
- ✅ test_prerequisites_no_current_branch
- ✅ test_prerequisites_no_base_branch
- ✅ test_prerequisites_git_exception
- ✅ test_prerequisites_task_tracker_exception (existing - validates general exceptions)
- ✅ test_prerequisites_branch_exception
- ✅ test_prerequisites_missing_task_tracker (NEW - validates missing file)
