# Step 6: Implement Raw Verbosity Level

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 6: Add --raw verbosity level functionality to make Step 5 tests pass.

Implement the raw output formatting:
- Add _format_raw() function for complete debug output
- Update execute_prompt() to handle raw verbosity level
- Include everything from verbose plus complete JSON API response structures
- Show full MCP server status and raw message content

Build on the verbose functionality from Step 4, adding the maximum debugging capability.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py` (extend existing)
- **Functions**: Add `_format_raw()`, update verbosity routing

## WHAT
- **New Function**: `_format_raw(response_data: dict) -> str`
- **Enhanced Routing**: Handle three verbosity levels in execute_prompt()
- **Complete Output**: Everything from verbose + raw JSON structures + full MCP status

## HOW
- **Verbosity Routing**: Support just_text, verbose, raw levels
- **Complete Output**: Include full JSON API response, MCP server details, raw messages
- **JSON Formatting**: Pretty-print JSON structures for readability
- **Maximum Debug**: Provide every available piece of information for debugging

## ALGORITHM
```
1. In execute_prompt(): Route to three verbosity levels:
   - Default: _format_just_text()
   - Verbose: _format_verbose() 
   - Raw: _format_raw()
2. _format_raw() includes:
   - Everything from _format_verbose()
   - Complete raw JSON API response structures
   - Full MCP server status and available tools listing
   - Raw message content for maximum debugging capability
```

## DATA
- **Input**: Enhanced `argparse.Namespace` with `raw` attribute
- **Verbosity Levels**: `just_text`, `verbose`, `raw`
- **Raw Output**:
  - All content from verbose level
  - Raw JSON: Pretty-printed complete API response structures
  - MCP Status: Full server information and all available tools
  - Raw Messages: Complete message content for debugging
- **Format**: Structured sections with clear headers for readability
- **Return**: Complete formatted string with maximum debugging information
