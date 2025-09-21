# Step 2: Real SDK Objects Integration Test

## LLM Prompt
```
Based on the summary in pr_info2/steps/summary.md and completed Step 1, implement the minimal Step 2 to add an integration test that validates our utility functions work with actual SDK objects when available. This test should skip gracefully if the SDK is not installed.

Focus on real-world validation without external dependencies.
```

## WHERE
- **Test File**: `tests/cli/commands/test_prompt_sdk_utilities.py`
- **Test Class**: `TestSDKMessageDetection` (existing class, add new method)

## WHAT
- **Function**: `test_real_sdk_objects_if_available()`

## HOW
- **Integration Strategy**: Import and test with real SDK objects
- **Graceful Skipping**: Use try/except with pytest.skip() for missing SDK
- **Test Scope**: Validate basic utility functions with real objects

## ALGORITHM
```python
# Real SDK object integration testing
1. Try to import real SDK classes from our codebase
2. Create real SDK objects with minimal data
3. Test _is_sdk_message(), _get_message_role(), _get_message_tool_calls()
4. Skip test gracefully if SDK import fails
```

## DATA
**Test Implementation**:
```python
@pytest.mark.integration
def test_real_sdk_objects_if_available(self):
    """Test with real SDK objects when SDK is available."""
    try:
        from mcp_coder.llm_providers.claude.claude_code_api import SystemMessage, AssistantMessage
        
        # Test with real SDK objects
        system_msg = SystemMessage(subtype="test", data={})
        assert _is_sdk_message(system_msg) is True
        assert _get_message_role(system_msg) == "system"
        
        # Test graceful handling
        assert _get_message_tool_calls(system_msg) == []
        
    except ImportError:
        pytest.skip("SDK not available for integration testing")
```

## Integration Points
- **Real Objects**: Uses actual SDK classes from the codebase
- **Graceful Degradation**: Skips if SDK not available
- **Validation**: Tests the actual utility functions with real objects

## Validation Criteria
- Test validates `_is_sdk_message()` works with real SDK objects
- Test validates `_get_message_role()` extracts correct role from real objects
- Test validates `_get_message_tool_calls()` handles real objects gracefully
- Test skips when SDK unavailable (no false failures)
- Implementation takes ~15 minutes
- Provides confidence that fix works in real-world scenarios
