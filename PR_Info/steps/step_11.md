# Step 11: CLI Integration for All Parameters

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 11: Integrate all prompt command parameters into the CLI system.

Update the CLI parser and routing to support all new parameters:
- Add prompt subparser with all verbosity and storage parameters
- Add routing logic in main function for the complete prompt command
- Update command exports to include execute_prompt
- Ensure all parameters (--verbose, --raw, --store-response, --continue-from) are properly handled

Follow the patterns used for existing commands like help, verify, and commit, but include all the enhanced functionality.
```

## WHERE
- **Files**:
  - `src/mcp_coder/cli/main.py` (parser and routing)
  - `src/mcp_coder/cli/commands/__init__.py` (exports)

## WHAT
- **Parser Enhancement**: Add comprehensive prompt subparser with all parameters
- **Routing Logic**: Add prompt case in main() function with full parameter support
- **Export Update**: Add `execute_prompt` to command exports
- **Parameter Integration**: Support verbosity levels and storage options

## HOW
- **Complete Subparser**: Add prompt subparser with all flags and options
- **Parameter Definitions**:
  - `prompt` (positional): The prompt text
  - `--verbosity`: Choose output level (just-text, verbose, raw) with just-text default
  - `--store-response`: Store session data
  - `--continue-from`: Continue from previous session file

## ALGORITHM
```
1. Add comprehensive prompt subparser in create_parser():
   - Positional prompt argument
   - --verbosity option with choices (just-text, verbose, raw) and just-text default
   - --store-response flag for session storage
   - --continue-from option for session continuation
2. Import execute_prompt in main.py
3. Add routing case for prompt command in main()
4. Update __init__.py exports to include execute_prompt
```

## DATA
- **Parser Configuration**:
  ```python
  prompt_parser = subparsers.add_parser("prompt", 
      help="Execute prompt via Claude API with debug output")
  prompt_parser.add_argument("prompt", 
      help="The prompt to send to Claude")
  prompt_parser.add_argument("--verbosity", 
      choices=["just-text", "verbose", "raw"], default="just-text",
      help="Output verbosity level (default: just-text)")
  prompt_parser.add_argument("--store-response", action="store_true",
      help="Store complete session data for continuation")
  prompt_parser.add_argument("--continue-from", type=str,
      help="Continue from previous stored session file")
  ```
- **Routing**: `args.command == "prompt"` → `return execute_prompt(args)`
- **Import**: `from .commands import execute_prompt`
