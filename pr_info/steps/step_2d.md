# Step 2d: Clean Up Imports and Verify Quality

## Objective

Remove unused imports (particularly `argparse` and `sys` if no longer used), verify the module works correctly, and run quality checks to ensure the refactored code meets standards.

## Reference

Review `decisions.md` Decision #6 for emphasis on preserving functionality.

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/workflows/create_plan.py` - Clean up imports, verify quality

## WHAT: Import Changes

### Imports to Review and Remove (if unused)

**1. argparse Import**
```python
import argparse  # REMOVE - no longer used (parse_arguments deleted)
```

**2. sys Import**
```python
import sys  # REMOVE - only if no other usage besides sys.exit() (which was removed)
```

**Note:** Check if `sys` is used elsewhere in the file before removing. If it's only used for `sys.exit()` (which we replaced with `return`), then remove it.

### Expected Imports After Cleanup

The file should retain imports needed for workflow logic:
```python
import logging
from pathlib import Path
from typing import Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.prompt_manager import PromptManager
from mcp_coder.utils.commit_operations import commit_changes
from mcp_coder.utils.git_operations.core import get_git_root
from mcp_coder.utils.github_operations.issue_manager import IssueManager
from mcp_coder.utils.github_operations.github_utils import get_github_token
# ... other necessary imports
```

## HOW: Cleanup and Verification Process

### Step 1: Remove Unused Imports

```python
edit_file(
    file_path="src/mcp_coder/workflows/create_plan.py",
    edits=[
        {
            "old_text": "import argparse\n",
            "new_text": ""
        }
    ]
)

# Only remove sys if not used elsewhere
# Check first: grep "sys\." src/mcp_coder/workflows/create_plan.py
# If only sys.exit() was used (now removed), then:
edit_file(
    file_path="src/mcp_coder/workflows/create_plan.py",
    edits=[
        {
            "old_text": "import sys\n",
            "new_text": ""
        }
    ]
)
```

### Step 2: Verify Module Functionality

**Test import:**
```python
python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow"
```

**Test function signature:**
```python
python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow; import inspect; print(inspect.signature(run_create_plan_workflow))"
```

Expected: `(issue_number: int, project_dir: pathlib.Path, provider: str, method: str) -> int`

### Step 3: Run Quality Checks

**3a. Pylint Check:**
```bash
mcp__code-checker__run_pylint_check(
    categories=["error", "fatal"],
    target_directories=["src/mcp_coder/workflows"]
)
```

Expected: No errors

**3b. Mypy Check:**
```bash
mcp__code-checker__run_mypy_check(
    strict=True,
    target_directories=["src/mcp_coder/workflows"]
)
```

Expected: No type errors

**Note:** Pytest will be run in Step 5 after test imports are updated.

## ALGORITHM: Verification Process

```python
# 1. Check for unused imports
unused = []
if not uses_argparse():
    unused.append("argparse")
if not uses_sys():
    unused.append("sys")

# 2. Remove unused imports
for import_name in unused:
    remove_import(import_name)

# 3. Verify import works
try:
    from mcp_coder.workflows.create_plan import run_create_plan_workflow
    verify_signature(run_create_plan_workflow)
except ImportError as e:
    report_error(e)
    return False

# 4. Run quality checks
pylint_result = run_pylint()
mypy_result = run_mypy()

return pylint_result.success and mypy_result.success
```

## DATA: Expected State After Step 2d

### File State
- **Location:** `src/mcp_coder/workflows/create_plan.py`
- **Size:** ~443 lines (after deletions in 2c)
- **Main Function:** `run_create_plan_workflow(issue_number, project_dir, provider, method) -> int`
- **Imports:** Clean - only necessary imports remain
- **CLI Code:** All removed (parse_arguments, if __name__, sys.exit)

### Module Exports
```python
# These functions should be importable:
from mcp_coder.workflows.create_plan import (
    run_create_plan_workflow,  # Main function (renamed from main)
    check_prerequisites,
    manage_branch,
    verify_steps_directory,
    run_planning_prompts,
    validate_output_files,
    resolve_project_dir,  # Kept for backward compatibility
)
```

## Verification Steps

1. **Unused Imports Removed:**
   ```bash
   grep "^import argparse" src/mcp_coder/workflows/create_plan.py
   grep "^import sys" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results (both removed)

2. **Module Imports Successfully:**
   ```python
   python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow, check_prerequisites, manage_branch"
   ```
   Expected: Success

3. **Function Signature Correct:**
   ```python
   python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow; import inspect; print(inspect.signature(run_create_plan_workflow))"
   ```
   Expected: `(issue_number: int, project_dir: pathlib.Path, provider: str, method: str) -> int`

4. **Pylint Clean:**
   ```bash
   mcp__code-checker__run_pylint_check(
       categories=["error", "fatal"],
       target_directories=["src/mcp_coder/workflows"]
   )
   ```
   Expected: No errors or fatal issues

5. **Mypy Clean:**
   ```bash
   mcp__code-checker__run_mypy_check(
       strict=True,
       target_directories=["src/mcp_coder/workflows"]
   )
   ```
   Expected: No type errors

## Troubleshooting

### If Imports Fail
- Check that all necessary imports are present
- Verify module path is correct
- Check for circular import issues

### If Pylint/Mypy Fails
- Review error messages carefully
- Fix type hints if needed
- Address any code quality issues
- Re-run checks until clean

## Next Steps

Proceed to **Step 3** to register the CLI command in the main CLI system.

## Success Criteria for Step 2 (All Sub-steps Complete)

- ✅ File copied to new location (Step 2a)
- ✅ Function refactored with new signature (Step 2b)
- ✅ CLI parsing code removed (Step 2c)
- ✅ Imports cleaned up (Step 2d)
- ✅ Module imports successfully
- ✅ Pylint passes (no errors)
- ✅ Mypy passes (no type errors)
- ✅ Functionality preserved (workflow logic unchanged)

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md, pr_info/steps/decisions.md, and pr_info/steps/step_2d.md.

Implement Step 2d: Clean Up Imports and Verify Quality

Requirements:
1. Remove unused imports:
   - Remove: import argparse (no longer used)
   - Check if sys is used elsewhere besides sys.exit() - if not, remove it
2. Verify module imports successfully
3. Verify function signature is correct
4. Run pylint check on src/mcp_coder/workflows/
5. Run mypy check on src/mcp_coder/workflows/
6. Fix any issues found until both checks pass

After implementation:
1. Confirm argparse import removed
2. Confirm sys import removed (if applicable)
3. Verify: python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow"
4. Verify function signature matches expected
5. Confirm pylint passes with no errors
6. Confirm mypy passes with no type errors

This completes Step 2 (all sub-steps). All workflow functionality should be preserved.

Do not proceed to the next step yet - wait for confirmation that Step 2 is complete.
```
