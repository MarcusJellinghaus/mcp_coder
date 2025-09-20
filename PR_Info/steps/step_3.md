# Step 3: Fix _format_verbose() to Handle Both Message Formats

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and using the utilities created in Step 2, implement Step 3 to fix the _format_verbose() function. Replace the problematic message.get("role") calls with the unified access utilities to handle both dictionary and SDK message objects.

This step should resolve the AttributeError and make the tests from Step 1 start passing for verbose output.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Function**: `_format_verbose()` (lines 112-177)
- **Specific Fix**: Tool interactions extraction section (lines 158-166)

## WHAT
- **Function**: Update `_format_verbose(response_data: Dict[str, Any]) -> str`
- **Target**: Replace manual message parsing with utility functions
- **Scope**: Fix tool interaction extraction and message processing

## HOW
- **Replace**: `message.get("role") == "assistant"` with `_get_message_role(message) == "assistant"`
- **Replace**: `"tool_calls" in message` with `bool(_get_message_tool_calls(message))`
- **Replace**: Manual tool call iteration with `_extract_tool_interactions(raw_messages)`
- **Integration**: Use new utility functions throughout tool interaction section

## ALGORITHM
```python
# Updated tool interaction extraction in _format_verbose()
1. Get raw_messages from response_data
2. Call _extract_tool_interactions(raw_messages) to get formatted list
3. If tool_interactions exist, add them to formatted output
4. If no tool interactions, add "No tool calls made" message
5. Continue with existing performance metrics and session info
```

## DATA
**Before (Problematic Code)**:
```python
tool_interactions = []
for message in raw_messages:
    if message.get("role") == "assistant" and "tool_calls" in message:  # ❌ Fails on SDK objects
        for tool_call in message.get("tool_calls", []):
            tool_name = tool_call.get("name", "unknown_tool")
            tool_params = tool_call.get("parameters", {})
            tool_interactions.append(f"  - {tool_name}: {tool_params}")
```

**After (Fixed Code)**:
```python
tool_interactions = _extract_tool_interactions(raw_messages)  # ✅ Works with both formats
```

**Function Return**: Same string format as before, but now works with SDK objects

## Integration Points
- **Utility Functions**: Use `_extract_tool_interactions()` from Step 2
- **Backward Compatibility**: Maintain exact same output format for existing tests
- **Error Handling**: Graceful fallback if tool extraction fails
- **Performance**: No significant performance impact

## Validation Criteria
- `_format_verbose()` no longer throws AttributeError with SDK message objects
- Tool interaction extraction works with both dictionary and SDK message formats
- Existing tests continue to pass with same output format
- Verbose output includes tool interactions when present
- Tests from Step 1 for verbose format should now pass
- No regression in existing functionality

## Expected Changes
- **Lines Modified**: ~10 lines in `_format_verbose()` function
- **Functionality**: Same output format, expanded input compatibility
- **Error Reduction**: Eliminates AttributeError for SDK objects
- **Test Impact**: Step 1 verbose tests should pass after this change
