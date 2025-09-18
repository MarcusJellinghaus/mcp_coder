# Step 2: Implement Basic Prompt Command Module

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 2: Create the basic prompt command module to make the tests from Step 1 pass.

Implement the execute_prompt function with basic functionality:
- Call Claude API using ask_claude_code_api_detailed_sync function
- Implement just-text output format (default verbosity level)
- NO input validation, NO error handling (let it crash for debugging)
- Print Claude response + basic tool interactions summary

Follow the patterns established in src/mcp_coder/cli/commands/help.py and src/mcp_coder/cli/commands/verify.py.
Implement only the core functionality - verbosity levels come in later steps.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Module**: New command module following existing structure

## WHAT
- **Main Function**: `execute_prompt(args: argparse.Namespace) -> int`
- **Helper Function**: `_format_just_text(response_data: dict) -> str`
- **Imports**: `argparse`, `logging`, `ask_claude_code_api_detailed_sync`

## HOW
- **Integration**: Import from `...llm_providers.claude.claude_code_api`
- **Output Format**: Claude response text + simple tool usage summary
- **No Error Handling**: Let exceptions propagate for debugging visibility
- **Return Codes**: 0=success, let crashes happen for errors

## ALGORITHM
```
1. Extract prompt from args.prompt
2. Call ask_claude_code_api_detailed_sync(prompt)
3. Format output using _format_just_text()
4. Print formatted output to stdout
5. Return 0
```

## DATA
- **Input**: `argparse.Namespace` with `prompt: str` attribute
- **Return**: `int` (exit code, always 0 on success)
- **External Call**: `ask_claude_code_api_detailed_sync(question: str) -> dict`
- **Output**: Claude response + tool summary (e.g., "Used 2 tools: file_read, web_search")
- **Format**: Clean, readable output for default use case
