# Step 2c: Remove CLI Parsing Code

## Objective

Remove all CLI-specific code that is no longer needed in the workflow module: the `parse_arguments()` function and the `if __name__ == "__main__":` block. This completes the separation of CLI concerns from workflow logic.

## Reference

Review `decisions.md` Decision #5 for rationale on moving CLI parsing to the CLI layer.

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/workflows/create_plan.py` - Remove CLI parsing code

## WHAT: Code to Remove

### 1. parse_arguments() Function

**Location:** Near the top of the file (after imports, before helper functions)

**Complete function to DELETE:**
```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - issue_number: GitHub issue number (int)
            - project_dir: Optional project directory path
            - llm_method: LLM method to use
            - log_level: Logging level
    """
    parser = argparse.ArgumentParser(
        description="Create implementation plan from GitHub issue"
    )
    parser.add_argument(
        "issue_number",
        type=int,
        help="GitHub issue number to create plan for"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()
```

**Size:** Approximately 40 lines

### 2. Main Execution Block

**Location:** End of file

**Complete block to DELETE:**
```python
if __name__ == "__main__":
    main()
```

**Size:** 2 lines

## HOW: Deletion Process

### Using edit_file Tool

Use targeted deletions to remove the code:

```python
edit_file(
    file_path="src/mcp_coder/workflows/create_plan.py",
    edits=[
        {
            "old_text": """def parse_arguments() -> argparse.Namespace:
    \"\"\"Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - issue_number: GitHub issue number (int)
            - project_dir: Optional project directory path
            - llm_method: LLM method to use
            - log_level: Logging level
    \"\"\"
    parser = argparse.ArgumentParser(
        description="Create implementation plan from GitHub issue"
    )
    parser.add_argument(
        "issue_number",
        type=int,
        help="GitHub issue number to create plan for"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()


""",
            "new_text": ""
        },
        {
            "old_text": """

if __name__ == "__main__":
    main()""",
            "new_text": ""
        }
    ]
)
```

## ALGORITHM: Verification Process

```python
# 1. Locate parse_arguments function
find_function_start = "def parse_arguments()"
find_function_end = "return parser.parse_args()"

# 2. Delete entire function (including docstring)
DELETE_LINES: from function start to function end + blank lines

# 3. Locate main execution block
find_main_block = "if __name__ == \"__main__\":"

# 4. Delete main execution block
DELETE_LINES: if __name__ block (2 lines)

# 5. Verify no parse_arguments references remain
search_file("parse_arguments") → should find 0 results
```

## DATA: Expected File Changes

**Lines Removed:** ~42 lines total
- `parse_arguments()` function: ~40 lines
- `if __name__ == "__main__":` block: ~2 lines

**File Size Change:**
- Before: ~485 lines
- After: ~443 lines

## Verification Steps

1. **Function Removed:**
   ```bash
   grep -n "def parse_arguments" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results

2. **No parse_arguments Calls:**
   ```bash
   grep "parse_arguments" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results

3. **Main Block Removed:**
   ```bash
   grep -n "if __name__" src/mcp_coder/workflows/create_plan.py
   ```
   Expected: No results

4. **File Still Imports:**
   ```python
   python -c "from mcp_coder.workflows.create_plan import run_create_plan_workflow"
   ```
   Expected: Success (may still have import errors - will fix in step 2d)

## Next Steps

Proceed to **Step 2d** to update imports and run quality checks.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md, pr_info/steps/decisions.md, and pr_info/steps/step_2c.md.

Implement Step 2c: Remove CLI Parsing Code

Requirements:
1. Delete the entire parse_arguments() function (~40 lines)
   - Includes function definition, docstring, and all argument parsing code
2. Delete the if __name__ == "__main__": block at the end of the file (~2 lines)
3. Ensure no references to parse_arguments remain in the file

IMPORTANT: Only delete these two sections - do not modify any other code.

After implementation:
1. Verify parse_arguments function is gone
2. Verify if __name__ block is gone
3. Verify file still imports (may have import issues - will fix in step 2d)
4. Check that ~42 lines were removed

Do not proceed to the next step yet - wait for confirmation.
```
