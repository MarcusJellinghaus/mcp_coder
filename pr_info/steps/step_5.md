# Step 5: Add CLI Parser Integration

## LLM Prompt
```
Based on the summary document and this step, integrate the new check-branch-status command into the CLI parser.

Modify `src/mcp_coder/cli/main.py` to add the argument parser and routing for the check-branch-status command. Write tests to verify proper argument parsing and command routing.

Reference the summary document and follow the existing patterns used by other commands like `implement` and `create-pr`.
```

## WHERE
- **File**: `src/mcp_coder/cli/main.py` (modify existing)
- **Test File**: `tests/cli/test_main.py` (extend existing)

## WHAT

### Parser Addition (in create_parser function)
```python
# Add after existing commands
check_branch_status_parser = subparsers.add_parser(
    "check-branch-status", 
    help="Check branch readiness status and optionally apply fixes"
)
```

### Arguments to Add
```python
check_branch_status_parser.add_argument(
    "--project-dir", type=str, default=None,
    help="Project directory path (default: current directory)"
)
check_branch_status_parser.add_argument(
    "--fix", action="store_true",
    help="Attempt to automatically fix issues found"
)
check_branch_status_parser.add_argument(
    "--llm-truncate", action="store_true", 
    help="Truncate output for LLM consumption"
)
# ... standard LLM arguments (method, config, execution-dir)
```

### Routing Addition (in main function)
```python
elif args.command == "check-branch-status":
    from .commands.check_branch_status import execute_check_branch_status
    return execute_check_branch_status(args)
```

### Test Functions
```python
def test_check_branch_status_parser_creation()
def test_check_branch_status_default_args()  
def test_check_branch_status_with_fix_flag()
def test_check_branch_status_routing()
```

## HOW

### Integration Pattern
Follow the exact same pattern as existing commands:
1. Add parser in `create_parser()` after other subparsers
2. Use same argument naming conventions (`--project-dir`, `--llm-method`, etc.)
3. Add routing in `main()` function with lazy import
4. Use same error handling pattern as other commands

### Standard Arguments to Include
```python
# Follow implement.py pattern exactly:
--project-dir           # Project directory path
--llm-method           # claude_code_cli or claude_code_api  
--mcp-config           # Path to MCP configuration file
--execution-dir        # Working directory for Claude subprocess
```

### Algorithm (Parser Integration)
```
1. Add subparser after existing commands in create_parser()
2. Add all required arguments with proper defaults
3. Add help text consistent with other commands
4. Add routing case in main() with lazy import
5. Follow existing error handling patterns
```

## DATA

### Argument Defaults
```python
# Match existing command patterns:
project_dir: None           # Use current directory
llm_method: "claude_code_cli"  # Default to CLI
mcp_config: None           # Auto-discover
execution_dir: None        # Use current directory
fix: False                 # Read-only by default
llm_truncate: False        # Full output by default
```

### Help Text
```python
main_help = "Check branch readiness status and optionally apply fixes"

--fix_help = "Attempt to automatically fix issues found (CI failures, formatting, etc.)"
--llm_truncate_help = "Truncate output for LLM consumption (~200 lines)"
```

### Expected Usage Patterns
```bash
# Read-only analysis
mcp-coder check-branch-status

# With auto-fixes  
mcp-coder check-branch-status --fix

# LLM mode (used by slash command)
mcp-coder check-branch-status --fix --llm-truncate

# Custom project directory
mcp-coder check-branch-status --project-dir /path/to/project
```

## Implementation Notes
- **Consistency**: Use exact same argument patterns as `implement` command
- **Help Integration**: Command appears in main help with appropriate description
- **Error Handling**: Lazy import in routing prevents import errors if dependencies missing
- **Testing**: Test both successful parsing and routing to verify integration
- **Documentation**: Help text clearly explains read-only vs fix modes