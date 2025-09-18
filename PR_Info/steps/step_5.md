# Step 5: Add Raw Verbosity Level Tests

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 5: Add tests for the --raw verbosity level.

Create tests for the raw output functionality:
- Test raw output format (everything including full JSON structures)
- Test that raw shows more information than verbose
- Verify presence of complete API response structures
- Use the same test patterns established in previous steps

This adds the most detailed verbosity level for maximum debugging capability.
```

## WHERE
- **File**: `tests/cli/commands/test_prompt.py` (extend existing)
- **Test Addition**: Add to existing test module

## WHAT
- **New Test Function**: `test_raw_output()`
- **Test Logic**: Mock args with raw flag, verify complete debug output
- **JSON Verification**: Check for presence of raw JSON API response structures

## HOW
- **Mock Setup**: Mock args with `verbosity="raw"`  
- **Output Verification**: Check for raw JSON, complete MCP server status, full message content
- **Content Checking**: Verify presence of JSON structures and complete debugging info
- **Comparison**: Ensure raw contains everything from verbose plus JSON data

## ALGORITHM
```
1. Setup mock args with prompt and verbosity="raw"
2. Mock ask_claude_code_api_detailed_sync with complete response data
3. Call execute_prompt function
4. Capture output and verify raw-specific content:
   - Everything from verbose output
   - Complete raw JSON API response structures
   - Full MCP server status and available tools
   - Raw message content for maximum debugging
```

## DATA
- **Input**: `argparse.Namespace` with `prompt` and `verbosity="raw"`
- **Mock Response**: Complete Claude API response with full JSON structures
- **Assertions**:
  - Contains all verbose output elements
  - Contains raw JSON structures (check for JSON-like patterns)
  - Contains complete MCP server information
  - Contains raw message content
- **Scope**: Raw verbosity level functionality only
