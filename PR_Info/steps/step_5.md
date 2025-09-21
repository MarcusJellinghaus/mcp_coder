# Step 5: Add Integration Test to Prevent Regression

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and the completed fixes from Steps 1-4, implement Step 5 to add a comprehensive integration test that prevents regression of the SystemMessage AttributeError. This test should simulate the real-world scenario using actual Claude SDK components and verify the complete fix works end-to-end.

All previous tests should now be passing, and this step adds final validation for the complete solution.
```

## WHERE
- **Test File**: `tests/cli/commands/test_prompt.py`
- **New Test**: Add to existing `TestExecutePrompt` class
- **Integration**: Test complete prompt command execution with SDK objects

## WHAT
- **Function**: `test_real_world_sdk_message_integration()`
- **Function**: `test_all_verbosity_levels_with_sdk_objects()`
- **Function**: `test_edge_cases_sdk_message_handling()`

## HOW
- **Real SDK Import**: Import actual Claude SDK message classes
- **End-to-End Test**: Test complete prompt execution flow
- **Multiple Scenarios**: Test various message combinations and edge cases
- **Regression Prevention**: Verify the specific error scenario is permanently fixed

## ALGORITHM
```python
# Integration test for complete SDK object handling
1. Create realistic SDK message objects with various attributes
2. Mock ask_claude_code_api_detailed_sync with SDK objects in raw_messages
3. Execute prompt command with all verbosity levels (just-text, verbose, raw)
4. Verify no AttributeError occurs for any verbosity level
5. Verify output contains expected tool interaction and debugging information
```

## DATA
**Comprehensive Test Mock**:
```python
# Complete SDK message scenario
mock_response = {
    "text": "Integration test response",
    "session_info": {
        "session_id": "integration-test-session",
        "model": "claude-sonnet-4",
        "tools": ["file_reader", "code_executor"],
        "mcp_servers": [{"name": "integration_server", "status": "connected"}]
    },
    "result_info": {
        "duration_ms": 2000,
        "cost_usd": 0.03,
        "usage": {"input_tokens": 15, "output_tokens": 12}
    },
    "raw_messages": [
        SystemMessage(session_id="integration-test", data={"model": "claude-sonnet-4"}),
        AssistantMessage(
            content=[TextBlock(text="Integration response")],
            tool_calls=[{
                "id": "integration_tool_call",
                "name": "file_reader", 
                "parameters": {"path": "/test/file.py"}
            }]
        ),
        ResultMessage(duration_ms=2000, total_cost_usd=0.03)
    ]
}
```

**Test Scenarios**:
- Mixed SDK objects and edge cases
- Empty tool calls and missing attributes
- All verbosity levels with same SDK data
- Error scenarios with malformed SDK objects

## Integration Points
- **Complete Flow**: Test entire prompt command execution path
- **Real SDK Types**: Use actual SystemMessage, AssistantMessage, ResultMessage
- **All Formatters**: Verify just-text, verbose, and raw formatters work
- **Error Prevention**: Specifically test for the original AttributeError scenario

## Validation Criteria
- No AttributeError occurs with any verbosity level when using SDK message objects
- Tool interaction information is properly extracted and displayed
- JSON serialization works correctly in raw output
- All existing tests continue to pass (no regression)
- Integration test covers realistic real-world usage scenarios
- Edge cases (empty messages, missing attributes) are handled gracefully

## Expected Outcomes
- **Complete Fix Validation**: Confirms the original error is permanently resolved
- **Regression Prevention**: Prevents future changes from breaking SDK object handling  
- **Real-World Confidence**: Validates fix works with actual SDK message structures
- **Comprehensive Coverage**: Tests all aspects of the fix across all output formats

## Documentation
- **Test Comments**: Clear documentation of what each test validates
- **Error Scenarios**: Document specific edge cases being tested
- **Maintenance Guide**: Instructions for updating tests if SDK interface changes
- **Coverage Report**: Verify test coverage includes all modified code paths

## Expected Changes
- **Final Integration Test**: `test_complete_sdk_integration_end_to_end()` (~60 lines)
- **Documentation Updates**: ~20 lines of improved docstrings and comments
- **Functionality**: Complete validation of entire solution
- **Confidence**: Production-ready SDK object handling

This final step provides confidence that the complete solution is robust, well-tested, and ready for production use.
