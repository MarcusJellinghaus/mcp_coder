# Step 2: Implement Prompt Command Module

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 2: Create the prompt command module to make the tests from Step 1 pass.

Implement the execute_prompt function that:
- Validates input prompts (non-empty, non-whitespace)
- Calls Claude CLI using existing ask_claude_code_cli function
- Handles errors gracefully with proper exit codes
- Prints Claude's response to console

Follow the patterns established in src/mcp_coder/cli/commands/help.py and src/mcp_coder/cli/commands/verify.py.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Module**: New command module following existing structure

## WHAT
- **Main Function**: `execute_prompt(args: argparse.Namespace) -> int`
- **Helper Function**: `_validate_prompt(prompt: str) -> None` (raises ValueError)
- **Imports**: `argparse`, `logging`, `ask_claude_code_cli`

## HOW
- **Integration**: Import `ask_claude_code_cli` from `...llm_providers.claude.claude_code_cli`
- **Logging**: Use module logger with standard log messages
- **Error Handling**: Try/catch with specific exception handling
- **Return Codes**: 0=success, 1=user error, 2=system error

## ALGORITHM
```
1. Extract prompt from args.prompt
2. Validate prompt is not empty/whitespace
3. Call ask_claude_code_cli(prompt)
4. Print response to console
5. Return appropriate exit code
```

## DATA
- **Input**: `argparse.Namespace` with `prompt: str` attribute
- **Return**: `int` (exit code)
- **External Call**: `ask_claude_code_cli(question: str) -> str`
- **Output**: Claude's response printed to stdout
- **Exceptions**: `ValueError`, `FileNotFoundError`, `subprocess.CalledProcessError`
