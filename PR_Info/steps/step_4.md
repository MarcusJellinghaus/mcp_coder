# Step 4: Fix _format_raw() to Properly Serialize SDK Objects

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and the fixes from Step 3, implement Step 4 to fix the _format_raw() function. The raw output format needs to properly serialize Claude SDK message objects to JSON, which requires custom serialization since SDK objects aren't directly JSON-serializable.

This step should make the tests from Step 1 pass for raw output format and complete the fix for the original error.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Function**: `_format_raw()` (lines 73-110)
- **Specific Fix**: JSON serialization sections (lines 88-103)

## WHAT
- **Function**: Update `_format_raw(response_data: Dict[str, Any]) -> str`
- **Target**: Fix JSON serialization of SDK message objects
- **Scope**: Raw messages JSON section and complete API response JSON section

## HOW
- **Add**: Custom serialization function `_serialize_message_for_json()`
- **Replace**: Direct `json.dumps()` with SDK-aware serialization
- **Handle**: Convert SDK objects to serializable dictionaries
- **Maintain**: Existing JSON structure and formatting

## ALGORITHM
```python
# Custom SDK object serialization for raw output
1. Check if object is SDK message using _is_sdk_message()
2. For SDK objects: convert to dict with relevant attributes
3. For other objects: use default JSON serialization
4. Apply custom serializer to both raw_messages and complete response
5. Maintain existing JSON formatting (indent=2, default=str)
```

## DATA
**New Function**:
```python
def _serialize_message_for_json(obj: Any) -> Any:
    """Convert SDK message objects to JSON-serializable format."""
    if _is_sdk_message(obj):
        return {
            "type": type(obj).__name__,
            "role": _get_message_role(obj),
            "tool_calls": _get_message_tool_calls(obj),
            # Add other relevant attributes
        }
    return obj
```

**Updated JSON Serialization**:
```python
# Before
json.dumps(response_data, indent=2, default=str)  # ❌ Fails on SDK objects

# After  
json.dumps(response_data, indent=2, default=_serialize_message_for_json)  # ✅ Works
```

**Output Structure**: Same JSON format but with properly serialized SDK objects

## Integration Points
- **Utility Functions**: Use message detection and access utilities from Step 2
- **JSON Compatibility**: Ensure output is valid JSON with meaningful structure
- **Debug Information**: Preserve all debugging information from SDK objects
- **Existing Format**: Maintain compatibility with current raw output expectations

## Validation Criteria
- `_format_raw()` successfully serializes responses containing SDK message objects
- JSON output is valid and properly formatted
- Raw output includes all relevant information from SDK objects
- SDK object attributes are properly represented in JSON format
- Tests from Step 1 for raw format should now pass
- No impact on responses with dictionary message objects

## Expected Changes
- **New Function**: `_serialize_message_for_json()` (~15 lines)
- **Modified Lines**: ~5 lines in `_format_raw()` for JSON serialization
- **Functionality**: Enhanced JSON serialization capability
- **Compatibility**: Full backward compatibility with existing raw output format
- **Error Resolution**: Eliminates JSON serialization errors for SDK objects

## Technical Details
- **SDK Object Handling**: Convert SystemMessage, AssistantMessage, ResultMessage to dicts
- **Attribute Preservation**: Include session_id, role, content, tool_calls, etc.
- **Type Information**: Include object type name for debugging clarity
- **Fallback Strategy**: Graceful handling of unknown object types
