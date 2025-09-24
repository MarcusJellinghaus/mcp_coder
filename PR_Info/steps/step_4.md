# Step 4: Integration and Module Exports

## Context
Following the summary and previous steps, integrate the task tracker into the existing codebase and provide clean API exports.

## WHERE: File Paths and Module Structure
```
src/mcp_coder/workflow_utils/__init__.py  # Add exports
src/mcp_coder/utils/__init__.py           # Add workflow_utils import  
tests/workflow_utils/test_integration.py  # Add integration tests
```

## WHAT: Main Functions with Signatures
```python
# In workflow_utils/__init__.py
from .task_tracker import get_incomplete_tasks, is_task_done, Task

# In utils/__init__.py  
from .workflow_utils import get_incomplete_tasks, is_task_done
```

## HOW: Integration Points
- Add workflow_utils to main utils module exports
- Follow existing project patterns for module organization
- Add integration tests with real TASK_TRACKER.md files
- Ensure backward compatibility with existing utils

## ALGORITHM: Integration Logic
```python
# 1. Export public API from workflow_utils module
# 2. Add workflow_utils to main utils package
# 3. Create integration tests with actual file structure
# 4. Verify imports work correctly across modules
# 5. Test with real PR_Info/TASK_TRACKER.md files
```

## DATA: Export Structure
```python
# Public API available after integration
from mcp_coder.utils import get_incomplete_tasks, is_task_done
from mcp_coder.workflow_utils import Task

# Integration test results
bool: True  # All imports work correctly
list[str]: ["Real incomplete task names"] # From actual files
```

## LLM Prompt for Implementation
```
Implement Step 4 of the task tracker parser following pr_info/steps/summary.md.

Complete the integration following Steps 1-3:

1. Create proper module exports:
   - Add exports to src/mcp_coder/workflow_utils/__init__.py
   - Update src/mcp_coder/utils/__init__.py to include workflow_utils

2. Write integration tests:
   - Test imports work correctly from different modules
   - Test with real TASK_TRACKER.md file structure  
   - Test end-to-end workflow with actual files

3. Verify integration:
   - Ensure all public functions are properly exported
   - Check backward compatibility with existing utils
   - Test with current project's PR_Info structure

4. Add final documentation and cleanup:
   - Ensure all functions have proper docstrings
   - Clean up any temporary test files
   - Verify code follows project standards

Keep integration simple and follow existing project patterns for module organization.
```
