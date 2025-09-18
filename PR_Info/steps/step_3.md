# Step 3: Add Verbose Verbosity Level Tests

## LLM Prompt
```
Based on the summary in PR_Info/steps/summary.md, implement Step 3: Add tests for the --verbose verbosity level.

Create tests for the verbose output functionality:
- Test verbose output format (detailed tool interactions + metrics)
- Test that verbose shows more information than just-text
- Use the same test patterns established in Step 1

This adds the first verbosity level beyond the default just-text format.
```

## WHERE
- **File**: `tests/cli/commands/test_prompt.py` (extend existing)
- **Test Addition**: Add to existing test module

## WHAT
- **New Test Function**: `test_verbose_output()` 
- **Test Logic**: Mock args with verbose flag, verify detailed output
- **Comparison**: Ensure verbose output contains more detail than just-text

## HOW
- **Mock Setup**: Mock args with `verbose=True` flag
- **Output Verification**: Check for tool interaction details and performance metrics
- **Pattern Matching**: Verify presence of expected verbose-only content
- **Integration**: Extend existing test infrastructure

## ALGORITHM
```
1. Setup mock args with prompt and verbose=True
2. Mock ask_claude_code_api_detailed_sync with rich response data
3. Call execute_prompt function
4. Capture output and verify verbose-specific content:
   - Tool interaction details with parameters
   - Performance metrics (duration, cost)
   - Session information
```

## DATA
- **Input**: `argparse.Namespace` with `prompt` and `verbose=True`
- **Mock Response**: Enhanced Claude API response with tool interactions and metrics
- **Assertions**: 
  - Contains Claude response
  - Contains detailed tool interactions 
  - Contains performance metrics
  - More detailed than just-text output
- **Scope**: Verbose level functionality only
