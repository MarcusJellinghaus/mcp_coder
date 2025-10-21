# Step 3: Register CLI Command in Main CLI System

## Objective

Register the `create-plan` command in the main CLI system by adding a subparser and routing logic. This makes the command accessible via `mcp-coder create-plan`.

## Reference

Review `summary.md` for context and `src/mcp_coder/cli/main.py` to see how other commands (like `implement`) are registered.

## WHERE: File Paths

### Modified Files
- `src/mcp_coder/cli/main.py` - Add subparser and routing

## WHAT: Main Functions

### Modifications to `create_parser()`
Add subparser for `create-plan` command with all required arguments.

### Modifications to `main()`
Add routing logic to call `execute_create_plan()` when command is invoked.

## HOW: Integration Points

### 1. Import Statement
Add import at the top of the file with other command imports:

```python
from .commands.create_plan import execute_create_plan
```

### 2. Subparser Registration
Add in `create_parser()` function, after the `implement` command subparser:

```python
# Create plan command - Generate implementation plan from GitHub issue
create_plan_parser = subparsers.add_parser(
    "create-plan",
    help="Generate implementation plan for a GitHub issue"
)
create_plan_parser.add_argument(
    "issue_number",
    type=int,
    help="GitHub issue number to create plan for"
)
create_plan_parser.add_argument(
    "--project-dir",
    type=str,
    default=None,
    help="Project directory path (default: current directory)",
)
create_plan_parser.add_argument(
    "--llm-method",
    choices=["claude_code_cli", "claude_code_api"],
    default="claude_code_cli",
    help="LLM method to use (default: claude_code_cli)",
)
```

### 3. Command Routing
Add in `main()` function, after the `implement` command routing:

```python
elif args.command == "create-plan":
    return execute_create_plan(args)
```

## ALGORITHM: Integration Logic

**Subparser Addition:**
```python
# In create_parser():
# 1. Create subparser for "create-plan"
# 2. Add issue_number as positional argument (type=int)
# 3. Add --project-dir optional argument
# 4. Add --llm-method optional argument with choices
```

**Routing Logic:**
```python
# In main():
# 1. Check if args.command == "create-plan"
# 2. Call execute_create_plan(args)
# 3. Return exit code from execute_create_plan()
```

## DATA: Argument Structure

### Parsed Arguments (`args` namespace)
```python
args.command: str = "create-plan"
args.issue_number: int              # Required positional
args.project_dir: Optional[str]     # Optional, default=None
args.llm_method: str                # Optional, default="claude_code_cli"
args.log_level: str                 # From parent parser, default="WARNING"
```

## Test Strategy

**Note:** Formal tests will be added in Step 4. For now, verify:
1. Help text displays correctly
2. Command is recognized
3. Arguments are parsed correctly

## Implementation Details

### Complete Changes to `src/mcp_coder/cli/main.py`

#### 1. Add Import (Line ~14, with other command imports)
```python
from .commands.commit import execute_commit_auto, execute_commit_clipboard
from .commands.create_plan import execute_create_plan  # ADD THIS LINE
from .commands.help import execute_help, get_help_text
from .commands.implement import execute_implement
from .commands.prompt import execute_prompt
from .commands.verify import execute_verify
```

#### 2. Add Subparser (In `create_parser()`, after `implement_parser`)
Find the section where `implement_parser` is defined (around line 120), and add after it:

```python
    # Implement command - Step 5
    implement_parser = subparsers.add_parser(
        "implement", help="Execute implementation workflow from task tracker"
    )
    implement_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    implement_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )

    # CREATE-PLAN COMMAND - ADD THIS SECTION
    create_plan_parser = subparsers.add_parser(
        "create-plan",
        help="Generate implementation plan for a GitHub issue"
    )
    create_plan_parser.add_argument(
        "issue_number",
        type=int,
        help="GitHub issue number to create plan for"
    )
    create_plan_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Project directory path (default: current directory)",
    )
    create_plan_parser.add_argument(
        "--llm-method",
        choices=["claude_code_cli", "claude_code_api"],
        default="claude_code_cli",
        help="LLM method to use (default: claude_code_cli)",
    )

    return parser
```

#### 3. Add Routing Logic (In `main()`, after `implement` routing)
Find the section where `implement` command is routed (around line 180), and add after it:

```python
        elif args.command == "implement":
            return execute_implement(args)

        # CREATE-PLAN COMMAND - ADD THIS SECTION
        elif args.command == "create-plan":
            return execute_create_plan(args)

        # Other commands will be implemented in later steps
        logger.error(f"Command '{args.command}' not yet implemented")
```

## Verification Steps

1. **Verify Import:**
   ```bash
   python -c "from src.mcp_coder.cli.main import create_parser"
   ```

2. **Test Help Text:**
   ```bash
   python -m mcp_coder.cli.main create-plan --help
   ```
   
   Expected output:
   ```
   usage: mcp-coder create-plan [-h] [--project-dir PROJECT_DIR]
                                 [--llm-method {claude_code_cli,claude_code_api}]
                                 issue_number

   positional arguments:
     issue_number          GitHub issue number to create plan for

   optional arguments:
     -h, --help            show this help message and exit
     --project-dir PROJECT_DIR
                           Project directory path (default: current directory)
     --llm-method {claude_code_cli,claude_code_api}
                           LLM method to use (default: claude_code_cli)
   ```

3. **Test Command Recognition:**
   ```bash
   python -m mcp_coder.cli.main create-plan 123 --help
   ```
   Should not show "command not yet implemented" error.

4. **Code Quality:**
   ```bash
   mcp__code-checker__run_pylint_check(target_directories=["src/mcp_coder/cli"])
   ```

## Expected Behavior

After this step:
- ✅ `mcp-coder create-plan --help` displays help text
- ✅ `mcp-coder create-plan 123` is recognized as valid command
- ✅ Command routing calls `execute_create_plan()`
- ✅ All arguments are correctly parsed

## Next Steps

Proceed to **Step 4** to create comprehensive tests for the CLI command.

## LLM Prompt for Implementation

```
Please review pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3: Register CLI Command in Main CLI System

Requirements:
1. Add import for execute_create_plan in src/mcp_coder/cli/main.py
2. Add create-plan subparser in create_parser() function
3. Add routing logic in main() function to call execute_create_plan()
4. Follow the exact pattern from the implement command
5. Ensure all arguments are properly defined

After implementation:
1. Verify imports work correctly
2. Test help text: python -m mcp_coder.cli.main create-plan --help
3. Ensure command is recognized
4. Run pylint to check code quality

Do not proceed to the next step yet - wait for confirmation.
```
