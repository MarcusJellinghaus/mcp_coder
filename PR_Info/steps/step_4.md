# Step 4: Implement Verbose Verbosity Level

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 4: Add --verbose verbosity level functionality to make Step 3 tests pass.

Implement the verbose output formatting:
- Add _format_verbose() function for detailed output
- Update execute_prompt() to handle verbosity level argument
- Show detailed tool interactions, performance metrics, and session info
- Maintain the same API call structure from Step 2

Build on the basic functionality from Step 2, adding the verbose formatting capability.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py` (extend existing)
- **Functions**: Add `_format_verbose()`, update `execute_prompt()`

## WHAT
- **New Function**: `_format_verbose(response_data: dict) -> str`
- **Enhanced Logic**: Handle verbosity level selection in execute_prompt()
- **Output Format**: Detailed tool interactions + performance metrics + session info

## HOW
- **Verbosity Handling**: Check args for verbose flag, route to appropriate formatter
- **Detailed Output**: Include tool names, parameters, metrics (duration, cost, tokens)
- **Session Info**: Model name, working directory, basic session details
- **Integration**: Maintain existing just-text as default behavior

## ALGORITHM
```
1. In execute_prompt(): Check args.verbose flag
2. Call appropriate formatter based on verbosity level:
   - Default: _format_just_text()
   - Verbose: _format_verbose()
3. _format_verbose() includes:
   - Claude response text
   - Detailed tool interactions with parameters
   - Performance metrics (duration, cost, token usage)
   - Session information (model, working directory)
```

## DATA
- **Input**: Enhanced `argparse.Namespace` with `verbose` attribute
- **Verbosity Levels**: `just_text` (default), `verbose`
- **Verbose Output**: 
  - Claude response
  - Tool details: "1. fs:read_file - Parameters: {'file_path': 'README.md'}"
  - Metrics: "Duration: 1.2s, Cost: $0.004, Tokens: input=150/output=300"
  - Session: "Model: claude-3-5-sonnet, Directory: /path/to/project"
- **Return**: Formatted string for display
