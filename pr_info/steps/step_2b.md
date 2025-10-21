# Step 2b: Refactor Main Function Signature

## Objective

Refactor the `main()` function to `run_create_plan_workflow()` with the new signature that accepts parameters instead of parsing command-line arguments. This implements Decision #2 (return exit codes) and Decision #6 (preserve functionality).

## Reference

Review `decisions.md` Decision #2 and #6 for the rationale behind this change.

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/workflows/create_plan.py` - Refactor main function

## WHAT: Main Changes

### Function Signature Change

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
    
    sys.exit(0)  # or sys.exit(1)
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

    # ... rest of workflow (unchanged) ...
    
    return 0  # or return 1
```

## HOW: Refactoring Steps

### Changes Required

1. **Rename function:** `main` → `run_create_plan_workflow`
2. **Change signature:** Add 4 parameters (issue_number, project_dir, provider, method)
3. **Change return type:** `-> None` → `-> int`
4. **Update docstring:** Add Args and Returns sections
5. **Remove argument parsing:** Delete `args = parse_arguments()` line
6. **Remove project_dir resolution:** Delete `project_dir = resolve_project_dir(args.project_dir)` line
7. **Remove logging setup:** Delete `setup_logging(args.log_level)` line
8. **Add llm_method construction:** `llm_method = f"{provider}_code_{method}"`
9. **Update variable references:** 
   - `args.issue_number` → `issue_number`
   - `args.llm_method` → `llm_method` (after constructing it)
10. **Replace all `sys.exit()`:** 
    - `sys.exit(1)` → `return 1` (6 occurrences in workflow)
    - `sys.exit(0)` → `return 0` (1 occurrence at end)

## ALGORITHM: Refactoring Process

```python
# 1. Change function signature
def main() -> None:
    ↓
def run_create_plan_workflow(issue_number: int, project_dir: Path, provider: str, method: str) -> int:

# 2. Remove CLI-specific code
DELETE: args = parse_arguments()
DELETE: project_dir = resolve_project_dir(args.project_dir)
DELETE: setup_logging(args.log_level)

# 3. Add llm_method construction
ADD: llm_method = f"{provider}_code_{method}"

# 4. Update logging (remove args references)
logger.info(f"Using project directory: {project_dir}")
logger.info(f"GitHub issue number: {issue_number}")
logger.info(f"LLM method: {llm_method}")

# 5. Update all variable references in workflow body
args.issue_number → issue_number
args.llm_method → llm_method

# 6. Replace all sys.exit() calls with return
sys.exit(1) → return 1  # Error cases
sys.exit(0) → return 0  # Success case
```

## DATA: Function Changes

### Input Changes
**Before (from args):**
```python
args.issue_number: int
args.project_dir: str (becomes Path after resolve_project_dir)
args.llm_method: str (e.g., "claude_code_cli")
args.log_level: str
```

**After (function parameters):**
```python
issue_number: int
project_dir: Path (already resolved by CLI)
provider: str (e.g., "claude")
method: str (e.g., "cli")
# Note: llm_method constructed from provider + method
```

### Return Changes
**Before:** `None` (calls `sys.exit()`)
**After:** `int` (returns 0 or 1)

## Implementation Details

### Using edit_file Tool

Use targeted edits to make the changes:

```python
edit_file(
    file_path="src/mcp_coder/workflows/create_plan.py",
    edits=[
        {
            "old_text": "def main() -> None:\n    \"\"\"Main workflow orchestration function - creates implementation plan for GitHub issue.\"\"\"",
            "new_text": """def run_create_plan_workflow(
    issue_number: int,
    project_dir: Path,
    provider: str,
    method: str
) -> int:
    \"\"\"Main workflow orchestration function - creates implementation plan for GitHub issue.
    
    Args:
        issue_number: GitHub issue number to create plan for
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    \"\"\""""
        },
        # ... more edits for removing parse_arguments, etc.
    ]
)
```

## Verification Steps

1. **Function Renamed:**
   ```bash
   grep -n "def run_create_plan_workflow" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: Function found with new signature

2. **No sys.exit() Calls:**
   ```bash
   grep "sys.exit" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results (all replaced with return)

3. **No args References:**
   ```bash
   grep "args\." src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results (all replaced with direct parameters)

4. **Function Signature Check:**
   ```python
   python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow; import inspect; print(inspect.signature(run_create_plan_workflow))"
   ```
   Expected: `(issue_number: int, project_dir: pathlib.Path, provider: str, method: str) -> int`

## Next Steps

Proceed to **Step 2c** to remove CLI parsing code and update sys.exit() calls.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md, pr_info/steps/decisions.md, and pr_info/steps/step_2b.md.

Implement Step 2b: Refactor Main Function Signature

Requirements:
1. Rename function: main() → run_create_plan_workflow()
2. Update signature to accept 4 parameters: issue_number, project_dir, provider, method
3. Update return type: None → int
4. Update docstring with Args and Returns sections
5. Remove: args = parse_arguments() line
6. Remove: project_dir = resolve_project_dir(...) line
7. Remove: setup_logging(...) line
8. Add: llm_method = f"{provider}_code_{method}"
9. Replace all args.issue_number with issue_number
10. Replace all args.llm_method with llm_method
11. Replace all sys.exit(1) with return 1 (should be ~6 occurrences)
12. Replace final sys.exit(0) with return 0

IMPORTANT: Preserve all workflow logic - only change the function interface, not the workflow steps.

After implementation:
1. Verify function signature is correct
2. Verify no sys.exit() calls remain
3. Verify no args. references remain
4. Test import works

Do not proceed to the next step yet - wait for confirmation.
```
