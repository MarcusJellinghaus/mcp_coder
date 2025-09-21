# Step 3: Fix _format_raw() JSON Serialization & Add Verbosity Tests

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and the fixes from Step 2, implement Step 3 to fix the _format_raw() function for proper JSON serialization of SDK objects. Also add comprehensive integration tests for all verbosity levels.

Step 2 already fixed verbose output, so this step completes the raw output fix and adds thorough testing across all output formats.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Function**: `_format_raw()` (lines 73-110)
- **Test File**: `tests/cli/commands/test_prompt.py`
- **New Test**: `test_all_verbosity_levels_with_sdk_objects()`

## WHAT
- **Function**: Update `_format_raw(response_data: Dict[str, Any]) -> str`
- **Function**: Add `_serialize_message_for_json(obj: Any) -> Any`
- **Test**: Comprehensive integration test for all verbosity levels

## HOW
- **Add**: Custom JSON serialization function `_serialize_message_for_json()`
- **Replace**: Direct `json.dumps()` with SDK-aware serialization
- **Handle**: Convert SDK objects to serializable dictionaries using official structure
- **Test**: Create comprehensive test covering just-text, verbose, and raw output formats

## ALGORITHM
```python
# Custom SDK object serialization for raw output
1. Check if object is SDK message using _is_sdk_message()
2. For SDK objects: convert to dict with relevant attributes based on official structure
3. For other objects: use default JSON serialization
4. Apply custom serializer to both raw_messages and complete response
5. Test all verbosity levels with same SDK data for consistency
```

## DATA
**New Function**:
```python
def _serialize_message_for_json(obj: Any) -> Any:
    """Convert SDK message objects to JSON-serializable format."""
    if _is_sdk_message(obj):
        # Use official SDK structure
        if hasattr(obj, 'subtype'):  # SystemMessage or ResultMessage
            return {"type": type(obj).__name__, "subtype": obj.subtype, ...}
        elif hasattr(obj, 'content'):  # AssistantMessage
            return {"type": type(obj).__name__, "content": obj.content, ...}
    return obj
```

**Updated JSON Serialization**:
```python
# Before
json.dumps(response_data, indent=2, default=str)  # ❌ Fails on SDK objects

# After  
json.dumps(response_data, indent=2, default=_serialize_message_for_json)  # ✅ Works
```

## Integration Points
- **JSON Compatibility**: Ensure output is valid JSON with meaningful structure
- **SDK Structure**: Use official Anthropic SDK structure for serialization
- **Debug Information**: Preserve all debugging information from SDK objects
- **Comprehensive Testing**: Test all three verbosity levels with same SDK data

## Validation Criteria
- `_format_raw()` successfully serializes responses containing SDK message objects
- JSON output is valid and properly formatted using official SDK structure
- All verbosity levels (just-text, verbose, raw) work with SDK objects
- **Integration test covering all verbosity levels should pass**
- No impact on responses with dictionary message objects
- Raw output includes all relevant information from SDK objects

## Expected Changes
- **New Function**: `_serialize_message_for_json()` (~20 lines)
- **Modified Lines**: ~5 lines in `_format_raw()` for JSON serialization
- **New Test**: Comprehensive integration test for all verbosity levels
- **Functionality**: Enhanced JSON serialization + thorough testing
