# Step 1: Create CLI Command Handler Structure

## Objective

Create the CLI command handler for `create-plan` that integrates with the main CLI system. This thin handler will parse arguments and delegate to the workflow module.

## Reference

Review `summary.md` for architectural context and `src/mcp_coder/cli/commands/implement.py` for the established pattern.

## WHERE: File Paths

### New Files
- `src/mcp_coder/cli/commands/create_plan.py` - CLI command handler

### Modified Files
- None (isolated change)

## WHAT: Main Functions

### `execute_create_plan(args: argparse.Namespace) -> int`
**Location:** `src/mcp_coder/cli/commands/create_plan.py`

**Signature:**
```python
def execute_create_plan(args: argparse.Namespace) -> int:
    """Execute the create-plan workflow command.

    Args:
        args: Parsed command line arguments with:
            - issue_number: GitHub issue number (int)
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude_code_cli' or 'claude_code_api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
```

## HOW: Integration Points

### Imports Required
```python
import argparse
import logging
import sys
from pathlib import Path

from ...workflows.create_plan import run_create_plan_workflow  # Will create in step 2
from ...workflows.utils import resolve_project_dir
from ..utils import parse_llm_method_from_args

logger = logging.getLogger(__name__)
```

### Module Structure
Follow the exact pattern from `implement.py`:
1. Import dependencies
2. Define logger
3. Implement `execute_create_plan()` function
4. Handle exceptions gracefully

## ALGORITHM: Core Logic

**Pseudocode for `execute_create_plan()`:**
```python
try:
    # 1. Resolve and validate project directory
    project_dir = resolve_project_dir(args.project_dir)
    
    # 2. Parse LLM method into provider and method
    provider, method = parse_llm_method_from_args(args.llm_method)
    
    # 3. Run workflow with issue number, project_dir, provider, method
    return run_create_plan_workflow(args.issue_number, project_dir, provider, method)
    
except KeyboardInterrupt:
    # Handle user cancellation gracefully
    
except Exception as e:
    # Log error and return error code
```

## DATA: Return Values

### Function Return
- **Type:** `int`
- **Values:**
  - `0` - Success (workflow completed)
  - `1` - Error (validation failed, workflow error, or user cancellation)

### Arguments Structure
```python
args.issue_number: int              # Required positional argument
args.project_dir: Optional[str]     # Optional --project-dir flag
args.llm_method: str                # Optional --llm-method flag (default: "claude_code_cli")
```

## Test Strategy

**Note:** Tests will be added in Step 4 after the workflow module exists. For now, create the handler structure only.

## Implementation Details

### Complete File Content

Create `src/mcp_coder/cli/commands/create_plan.py`:

```python
"""Create plan command implementation.

This module provides the CLI command interface for the create-plan workflow,
which generates implementation plans for GitHub issues.
"""

import argparse
import logging
import sys
from pathlib import Path

from ...workflows.utils import resolve_project_dir
from ..utils import parse_llm_method_from_args

logger = logging.getLogger(__name__)


def execute_create_plan(args: argparse.Namespace) -> int:
    """Execute the create-plan workflow command.

    Args:
        args: Parsed command line arguments with:
            - issue_number: GitHub issue number (int)
            - project_dir: Optional project directory path
            - llm_method: LLM method to use ('claude_code_cli' or 'claude_code_api')

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting create-plan command execution")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Parse LLM method using shared utility
        provider, method = parse_llm_method_from_args(args.llm_method)

        # Import here to avoid circular dependency during module load
        from ...workflows.create_plan import run_create_plan_workflow

        # Run the create-plan workflow
        return run_create_plan_workflow(args.issue_number, project_dir, provider, method)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1

    except Exception as e:
        print(f"Error during workflow execution: {e}", file=sys.stderr)
        logger.error(f"Unexpected error in create-plan command: {e}", exc_info=True)
        return 1
```

## Verification Steps

1. **File Created:**
   ```bash
   # Verify file exists
   ls -la src/mcp_coder/cli/commands/create_plan.py
   ```

2. **Import Check:**
   ```python
   # Verify no syntax errors
   python -c "from src.mcp_coder.cli.commands.create_plan import execute_create_plan"
   ```

3. **Code Quality:**
   ```bash
   # Run pylint on new file
   mcp__code-checker__run_pylint_check(target_directories=["src/mcp_coder/cli/commands"])
   ```

## Next Steps

Proceed to **Step 2** to create the workflow module that this CLI handler will invoke.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: Create CLI Command Handler Structure

Requirements:
1. Create the file src/mcp_coder/cli/commands/create_plan.py with the exact content specified in the step
2. Follow the pattern from src/mcp_coder/cli/commands/implement.py
3. Ensure all imports are correct and follow the module structure
4. Use lazy import for run_create_plan_workflow to avoid circular dependencies
5. Include proper docstrings and type hints

After implementation:
1. Verify the file was created correctly
2. Check that there are no syntax errors
3. Run pylint to ensure code quality

Do not proceed to the next step yet - wait for confirmation.
```
