# Step 1: Add Test Coverage for SDK Message Object Handling

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md, implement Step 1 to add comprehensive test coverage for the SystemMessage AttributeError. The goal is to create tests that reproduce the actual error scenario where Claude SDK objects (not dictionaries) are in raw_messages, causing the .get() method to fail.

Focus on creating tests that fail initially (TDD red phase) and will pass once we implement the fix in subsequent steps.
```

## WHERE
- **Test File**: `tests/cli/commands/test_prompt.py`
- **New Test Class**: Add test methods to existing `TestExecutePrompt` class

## WHAT
- **Function**: `test_verbose_with_sdk_message_objects()` 
- **Function**: `test_raw_with_sdk_message_objects()`
- **Function**: `test_tool_interaction_extraction_sdk_objects()`

## HOW
- **Import**: Add Claude SDK message classes to test imports
- **Mock Strategy**: Create actual SDK message objects instead of dictionaries
- **Test Pattern**: Verify both error reproduction and expected behavior

## ALGORITHM
```python
# Core test logic for SDK object handling
1. Import SystemMessage, AssistantMessage from claude_code_api
2. Create mock response with actual SDK message objects in raw_messages
3. Execute prompt command with verbose/raw verbosity
4. Verify no AttributeError occurs
5. Verify tool interaction data is extracted correctly
```

## DATA
**Test Mock Structure**:
```python
mock_response = {
    "text": "Response text",
    "session_info": {...},
    "result_info": {...},
    "raw_messages": [
        SystemMessage(session_id="test", data={...}),
        AssistantMessage(content=[TextBlock(text="test")], tool_calls=[...])
    ]
}
```

**Expected Results**:
- Tests should initially fail with AttributeError
- After fix implementation, tests should pass
- Tool interaction extraction should work with SDK objects

## Integration Points
- **Existing Tests**: Ensure new tests don't break existing dictionary-based mocks
- **SDK Dependencies**: Import actual Claude SDK classes for realistic testing
- **Error Scenarios**: Test both successful extraction and graceful failure cases

## Validation Criteria
- Test reproduces the exact AttributeError: `'SystemMessage' object has no attribute 'get'`
- Test covers both verbose and raw output formats
- Test verifies tool interaction extraction from SDK objects
- Tests are isolated and don't affect existing test suite
