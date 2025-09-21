# Step 2: Add SDK Object Tool Extraction Tests

## LLM Prompt
```
Based on the summary in pr_info2/steps/summary.md and Step 1 results, implement Step 2 to add comprehensive tests for the _get_message_tool_calls() function with SDK objects. The current tests only cover dictionary messages, but we need to test the SDK object code path that processes content blocks with tool information.

Focus on testing the logic that extracts tool calls from SDK AssistantMessage content.
```

## WHERE
- **Test File**: `tests/cli/commands/test_prompt_sdk_utilities.py`
- **Test Class**: `TestToolCallExtraction` (existing class, add new methods)

## WHAT
- **Function**: `test_sdk_assistant_message_tool_extraction()`
- **Function**: `test_sdk_assistant_message_no_tools()`
- **Function**: `test_sdk_assistant_message_malformed_content()`

## HOW
- **Mock Strategy**: Create mock AssistantMessage with mock content blocks
- **Content Simulation**: Mock tool blocks with `name` and `input`/`parameters` attributes
- **Error Testing**: Test malformed content that triggers exception handling

## ALGORITHM
```python
# SDK object tool extraction testing
1. Create mock tool block with name and input/parameters attributes
2. Create mock AssistantMessage with content containing tool block
3. Call _get_message_tool_calls() with mock AssistantMessage
4. Verify extracted tool calls match expected structure
5. Test both 'input' and 'parameters' attribute variations
```

## DATA
**Mock Structure**:
```python
class MockToolBlock:
    def __init__(self, name, tool_input):
        self.name = name
        self.input = tool_input  # or self.parameters

class MockAssistantMessage:
    def __init__(self, content):
        self.content = content
```

**Expected Results**:
- Tool calls extracted as `[{"name": "tool_name", "parameters": {...}}]`
- Both `input` and `parameters` attributes handled correctly
- Empty list returned for AssistantMessage without tools
- Exception handling tested for malformed content

## Integration Points
- **Existing Tests**: Add to existing `TestToolCallExtraction` class
- **Mock Integration**: Use controlled mocks that mimic SDK structure
- **Error Coverage**: Test exception paths in production code

## Validation Criteria
- Test verifies tool extraction from mock AssistantMessage with tool blocks
- Test handles both `input` and `parameters` attribute names
- Test returns empty list for AssistantMessage without tool content
- Test gracefully handles malformed content (non-iterable, missing attributes)
- Tests verify the specific code path that processes SDK objects
