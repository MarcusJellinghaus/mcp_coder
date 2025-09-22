# Step 4: Implement CLI Integration for --continue-from-last

## LLM Prompt
```
Implement the CLI integration for --continue-from-last parameter. Add the argument to the parser with mutual exclusivity validation, and integrate with the existing prompt execution logic.

Reference: PR_Info/steps/summary.md - implementing --continue-from-last parameter for mcp-coder prompt command.

This is step 4 of 6: Implementing CLI integration after TDD from step 3.
```

## WHERE
- **File 1**: `src/mcp_coder/cli/main.py` - Add CLI argument
- **File 2**: `src/mcp_coder/cli/commands/prompt.py` - Add integration logic
- **Location**: Modify existing `prompt_parser.add_argument()` calls and `execute_prompt()` function

## WHAT
**Main modifications**:
```python
# In main.py
prompt_parser.add_argument("--continue-from-last", action="store_true")

# In prompt.py  
def execute_prompt(args: argparse.Namespace) -> int:
    # Add logic to handle continue_from_last
```

## HOW
- **Argument Group**: Use argparse mutually exclusive group for `--continue-from` and `--continue-from-last`
- **Integration Point**: Modify existing continue_from logic in `execute_prompt()`
- **Error Handling**: Consistent error patterns with existing code
- **Logging**: Add appropriate debug/info logging

## ALGORITHM
```
1. CREATE mutually exclusive argument group in parser
2. ADD --continue-from-last flag to the group
3. MODIFY execute_prompt() to check continue_from_last flag
4. CALL _find_latest_response_file() if flag is set
5. INTEGRATE with existing _load_previous_chat() logic
```

## DATA
**CLI Argument Structure**:
```python
# In main.py
continue_group = prompt_parser.add_mutually_exclusive_group()
continue_group.add_argument(
    "--continue-from",
    type=str,
    help="Continue from previous stored session file"
)
continue_group.add_argument(
    "--continue-from-last", 
    action="store_true",
    help="Continue from the most recent stored session"
)
```

**Integration Logic**:
```python
# In execute_prompt()
continue_file_path = None
if getattr(args, "continue_from", None):
    continue_file_path = args.continue_from
elif getattr(args, "continue_from_last", False):
    continue_file_path = _find_latest_response_file()
    if continue_file_path is None:
        # Handle no files found error
        
if continue_file_path:
    # Use existing continuation logic
    previous_context = _load_previous_chat(continue_file_path)
    enhanced_prompt = _build_context_prompt(previous_context, args.prompt)
```

**Error Handling**:
- **No files found**: "Error: No previous response files found in .mcp-coder/responses/"
- **Directory missing**: Same error message (handled by utility function)
- **Mutual exclusivity**: Handled automatically by argparse
