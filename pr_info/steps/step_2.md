# Step 2: Migrate and Refactor Workflow Module

## Objective

Move the workflow module from `workflows/create_plan.py` to `src/mcp_coder/workflows/create_plan.py` and refactor the main entry point to return exit codes instead of calling `sys.exit()`.

## Reference

Review `summary.md` for architectural context. This step relocates existing code with minimal changes.

## WHERE: File Paths

### New Files
- `src/mcp_coder/workflows/create_plan.py` - Relocated workflow module

### Modified Files
- None (relocation only)

### Files to Reference
- `workflows/create_plan.py` - Source file (will be deleted in Step 7)

## WHAT: Main Functions

### `run_create_plan_workflow(issue_number: int, project_dir: Path, provider: str, method: str) -> int`
**Location:** `src/mcp_coder/workflows/create_plan.py`

**Signature:**
```python
def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    method: str
) -> int:
    """Main workflow orchestration function - creates implementation plan for GitHub issue.
    
    Args:
        issue_number: GitHub issue number to create plan for
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

### Other Functions (Preserved)
All existing functions remain unchanged:
- `check_prerequisites(project_dir: Path, issue_number: int) -> tuple[bool, IssueData]`
- `manage_branch(project_dir: Path, issue_number: int, issue_title: str) -> Optional[str]`
- `verify_steps_directory(project_dir: Path) -> bool`
- `run_planning_prompts(project_dir: Path, issue_data: IssueData, llm_method: str) -> bool`
- `format_initial_prompt(prompt_template: str, issue_data: IssueData) -> str`
- `validate_output_files(project_dir: Path) -> bool`
- `_load_prompt_or_exit(header: str) -> str`
- `resolve_project_dir(project_dir_arg: Optional[str]) -> Path` (kept for backward compatibility)

## HOW: Integration Points

### Key Changes

1. **Remove CLI Argument Parsing**
   - Delete `parse_arguments()` function (moved to CLI layer)
   - Remove `if __name__ == "__main__":` block

2. **Refactor Main Function**
   - Rename: `main()` → `run_create_plan_workflow()`
   - Change signature to accept parameters instead of parsing args
   - Return exit code instead of calling `sys.exit()`

3. **Update LLM Method Handling**
   - Accept `provider` and `method` as parameters
   - Combine into `llm_method` string for `run_planning_prompts()` call

### Module Structure (Unchanged)
```python
# Imports (same as original)
import logging
from pathlib import Path
from typing import Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
# ... rest of imports

# Logger
logger = logging.getLogger(__name__)

# Helper functions (unchanged)
# - check_prerequisites()
# - manage_branch()
# - verify_steps_directory()
# - _load_prompt_or_exit()
# - format_initial_prompt()
# - run_planning_prompts()
# - validate_output_files()
# - resolve_project_dir()

# Main workflow function (refactored)
def run_create_plan_workflow(issue_number, project_dir, provider, method) -> int:
    # Workflow orchestration logic
    pass
```

## ALGORITHM: Core Logic Changes

**Original `main()` function:**
```python
def main() -> None:
    args = parse_arguments()                    # Parse CLI args
    project_dir = resolve_project_dir(...)     # Resolve path
    setup_logging(args.log_level)              # Setup logging
    
    # ... workflow steps ...
    
    sys.exit(0)  # Exit with code
```

**Refactored `run_create_plan_workflow()`:**
```python
def run_create_plan_workflow(issue_number, project_dir, provider, method) -> int:
    # Note: logging already setup by CLI layer
    # Note: project_dir already resolved and validated by CLI layer
    
    # Combine provider + method for legacy function calls
    llm_method = f"{provider}_{method}"  # e.g., "claude_code_cli"
    
    # Run workflow steps (same as before)
    # ... check prerequisites ...
    # ... manage branch ...
    # ... run prompts ...
    # ... validate ...
    # ... commit ...
    # ... push ...
    
    return 0  # Return exit code instead of sys.exit()
```

**Detailed refactoring:**
```python
# 1. Remove early sys.exit() calls, use return instead
if not success:
    logger.error("Prerequisites validation failed")
    return 1  # Changed from: sys.exit(1)

# 2. Keep logging setup location (CLI handles it)
# DELETE: setup_logging(args.log_level)

# 3. Combine provider + method for run_planning_prompts()
llm_method = f"{provider}_code_{method}"  # e.g., "claude_code_cli"
if not run_planning_prompts(project_dir, issue_data, llm_method):
    logger.error("Planning prompts execution failed")
    return 1

# 4. Return success instead of sys.exit(0)
logger.info("Create plan workflow completed successfully!")
return 0  # Changed from: sys.exit(0)
```

## DATA: Return Values

### Function Return
- **Type:** `int`
- **Values:**
  - `0` - Success (plan created, committed, pushed)
  - `1` - Error (prerequisites failed, branch failed, prompts failed, validation failed)

### Input Parameters
```python
issue_number: int              # GitHub issue number
project_dir: Path              # Validated absolute path to project
provider: str                  # LLM provider ('claude')
method: str                    # LLM method ('cli' or 'api')
```

### Internal Data Structures (Unchanged)
- `IssueData` - TypedDict with issue information
- Git operation results - Dicts with `{'success': bool, ...}`

## Test Strategy

**Note:** Tests will be updated in Step 5. For now, ensure the module can be imported without errors.

## Implementation Details

### Step-by-Step Migration

1. **Copy the file:**
   ```bash
   cp workflows/create_plan.py src/mcp_coder/workflows/create_plan.py
   ```

2. **Delete `parse_arguments()` function**
   - Remove entire function (~40 lines)

3. **Delete `if __name__ == "__main__":` block**
   - Remove 2 lines at end of file

4. **Refactor `main()` → `run_create_plan_workflow()`**
   
   **Before:**
   ```python
   def main() -> None:
       """Main workflow orchestration function - creates implementation plan for GitHub issue."""
       # Parse command line arguments
       args = parse_arguments()
       project_dir = resolve_project_dir(args.project_dir)
       
       # Setup logging early
       setup_logging(args.log_level)
       
       logger.info("Starting create plan workflow...")
       logger.info(f"Using project directory: {project_dir}")
       logger.info(f"GitHub issue number: {args.issue_number}")
       logger.info(f"LLM method: {args.llm_method}")
   
       # ... rest of workflow ...
       
       logger.info("Create plan workflow completed successfully!")
       sys.exit(0)
   ```
   
   **After:**
   ```python
   def run_create_plan_workflow(
       issue_number: int,
       project_dir: Path,
       provider: str,
       method: str
   ) -> int:
       """Main workflow orchestration function - creates implementation plan for GitHub issue.
       
       Args:
           issue_number: GitHub issue number to create plan for
           project_dir: Path to the project directory
           provider: LLM provider (e.g., 'claude')
           method: LLM method (e.g., 'cli' or 'api')
       
       Returns:
           int: Exit code (0 for success, 1 for error)
       """
       # Note: Logging already setup by CLI layer
       # Note: project_dir already resolved and validated by CLI layer
       
       # Combine provider and method for legacy function compatibility
       llm_method = f"{provider}_code_{method}"  # e.g., "claude_code_cli"
       
       logger.info(f"Starting create plan workflow for project: {project_dir}")
       logger.info(f"GitHub issue number: {issue_number}")
       logger.info(f"LLM method: {llm_method}")
   
       # ... rest of workflow (same as before) ...
       
       logger.info("Create plan workflow completed successfully!")
       return 0
   ```

5. **Replace all `sys.exit(1)` with `return 1`**
   - Search for: `sys.exit(1)`
   - Replace with: `return 1`
   - Should be 6 replacements in the workflow steps

6. **Replace final `sys.exit(0)` with `return 0`**
   - At end of function
   - 1 replacement

7. **Update variable references**
   - Change `args.issue_number` → `issue_number`
   - Change `args.llm_method` → `llm_method`

8. **Remove unused imports**
   - Delete: `import argparse` (no longer needed)
   - Delete: `import sys` (only if no longer used elsewhere)
   - Keep: All other imports unchanged

## Verification Steps

1. **File Created:**
   ```bash
   ls -la src/mcp_coder/workflows/create_plan.py
   ```

2. **Import Check:**
   ```python
   python -c "from src.mcp_coder.workflows.create_plan import run_create_plan_workflow"
   ```

3. **Function Signature Check:**
   ```python
   python -c "from src.mcp_coder.workflows.create_plan import run_create_plan_workflow; import inspect; print(inspect.signature(run_create_plan_workflow))"
   ```

4. **Code Quality:**
   ```bash
   mcp__code-checker__run_pylint_check(target_directories=["src/mcp_coder/workflows"])
   ```

## Next Steps

Proceed to **Step 3** to register the CLI command in the main CLI system.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2: Migrate and Refactor Workflow Module

Requirements:
1. Copy workflows/create_plan.py to src/mcp_coder/workflows/create_plan.py
2. Delete the parse_arguments() function
3. Delete the if __name__ == "__main__": block
4. Refactor main() to run_create_plan_workflow() with the new signature
5. Replace all sys.exit(1) calls with return 1
6. Replace sys.exit(0) with return 0
7. Update variable references (args.* to direct parameters)
8. Remove unused imports (argparse)
9. Combine provider + method into llm_method string for legacy function calls

After implementation:
1. Verify the module can be imported
2. Check the function signature
3. Run pylint to ensure code quality
4. Ensure all workflow logic is preserved

Do not delete the original workflows/create_plan.py yet - that will happen in Step 7.
Do not proceed to the next step yet - wait for confirmation.
```
