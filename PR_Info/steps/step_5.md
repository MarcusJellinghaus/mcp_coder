# Step 5: Implement CLI Integration for --continue

## LLM Prompt
```
Implement the CLI integration for --continue parameter. Add the argument to the parser with mutual exclusivity validation, and integrate with the existing prompt execution logic using the strict validation utility function.

Reference: PR_Info/steps/summary.md and PR_Info/steps/Decisions.md - implementing --continue parameter for mcp-coder prompt command.

This is step 5 of 7: Implementing CLI integration after TDD from step 4.
```

## WHERE
- **File 1**: `src/mcp_coder/cli/main.py` - Add CLI argument
- **File 2**: `src/mcp_coder/cli/commands/prompt.py` - Add integration logic
- **Location**: Modify existing `prompt_parser.add_argument()` calls and `execute_prompt()` function

## WHAT
**Main modifications**:
```python
# In main.py
# Add mutually exclusive group and --continue parameter

# In prompt.py  
def execute_prompt(args: argparse.Namespace) -> int:
    # Add logic to handle continue with error message per Decision #4
```

## HOW
- **Argument Group**: Use argparse mutually exclusive group for `--continue-from` and `--continue`
- **Integration Point**: Modify existing continue_from logic in `execute_prompt()`
- **Error Handling**: Show info message "No previous response files found" per Decision #4
- **User Feedback**: Let utility function handle showing selected file per Decision #6

## ALGORITHM
```
1. CREATE mutually exclusive argument group in parser
2. ADD --continue flag to the group
3. MODIFY execute_prompt() to check continue flag
4. CALL _find_latest_response_file() if flag is set
5. HANDLE None return with specific error message
6. INTEGRATE with existing _load_previous_chat() logic
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
    "--continue", 
    action="store_true",
    help="Continue from the most recent stored session (auto-finds latest response file)"
)
```

**Integration Logic**:
```python
# In execute_prompt()
continue_file_path = None
if getattr(args, "continue_from", None):
    continue_file_path = args.continue_from
elif getattr(args, "continue", False):
    continue_file_path = _find_latest_response_file()
    if continue_file_path is None:
        print("No previous response files found, starting new conversation")  # Decision #10
        # Continue execution with empty context instead of returning
        
if continue_file_path:
    # Use existing continuation logic
    previous_context = _load_previous_chat(continue_file_path)
    enhanced_prompt = _build_context_prompt(previous_context, args.prompt)
```

**Error Handling**:
- **No files found**: "No previous response files found, starting new conversation" (Decision #10)
- **Directory missing**: Same info message, continue execution (handled by utility function)
- **Mutual exclusivity**: Handled automatically by argparse
