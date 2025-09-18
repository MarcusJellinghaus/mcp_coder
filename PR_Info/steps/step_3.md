# Step 3: Integrate Prompt Command into CLI

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 3: Integrate the prompt command into the main CLI system.

Update the CLI parser and routing to support the new prompt command:
- Add prompt subparser to argument parser
- Add routing logic in main function
- Update command exports
- Update no-command help text

Follow the patterns used for existing commands like help, verify, and commit.
```

## WHERE
- **Files**: 
  - `src/mcp_coder/cli/main.py` (parser and routing)
  - `src/mcp_coder/cli/commands/__init__.py` (exports)

## WHAT
- **Parser Addition**: Add prompt subparser in `create_parser()`
- **Routing Logic**: Add prompt case in `main()` function
- **Export Update**: Add `execute_prompt` to `__init__.py`
- **Help Update**: Include prompt in `handle_no_command()`

## HOW
- **Import**: Add `execute_prompt` to imports in main.py
- **Subparser**: `subparsers.add_parser("prompt", help="Execute prompt via Claude CLI")`
- **Argument**: `prompt_parser.add_argument("prompt", help="The prompt to send to Claude")`
- **Routing**: Add `elif args.command == "prompt":` case

## ALGORITHM
```
1. Add prompt subparser with required prompt argument
2. Import execute_prompt in main.py
3. Add routing case for prompt command
4. Update __init__.py exports
5. Update help text to include prompt command
```

## DATA
- **Parser Config**: Subparser with required `prompt` positional argument
- **Import**: `from .commands import execute_prompt`
- **Routing**: `args.command == "prompt"` → `return execute_prompt(args)`
- **Help Text**: Include "prompt <text>" in command listing
