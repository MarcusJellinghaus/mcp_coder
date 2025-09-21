# Step 1: Core SDK Detection Test (Mock Test)

## LLM Prompt
```
Based on the summary in pr_info2/steps/summary.md, implement the minimal Step 1 to add a focused test for the _is_sdk_message() function. This test should verify that the isinstance() logic works correctly with SDK objects using a simple mock.

Focus on testing the core logic that prevents the original AttributeError bug.
```

## WHERE
- **Test File**: `tests/cli/commands/test_prompt_sdk_utilities.py`
- **Test Class**: `TestSDKMessageDetection` (existing class, add new method)

## WHAT
- **Function**: `test_sdk_message_detection_basic()`

## HOW
- **Mocking Strategy**: Use `@patch` to mock one SDK class and test isinstance() behavior
- **Import Addition**: `from unittest.mock import patch`
- **Test Pattern**: Mock SDK class, create instance, verify detection vs dictionary/None

## ALGORITHM
```python
# Minimal SDK object detection testing
1. Mock the SystemMessage class 
2. Create mock instance using mocked class
3. Call _is_sdk_message() with mock instance, dictionary, and None
4. Verify isinstance check works correctly for all cases
```

## DATA
**Test Implementation**:
```python
@patch('mcp_coder.cli.commands.prompt.SystemMessage')
def test_sdk_message_detection_basic(self, mock_system_message_class):
    """Test that isinstance() logic works with SDK objects."""
    mock_instance = mock_system_message_class.return_value
    
    # Test our core isinstance() logic
    assert _is_sdk_message(mock_instance) is True
    assert _is_sdk_message({"role": "user"}) is False
    assert _is_sdk_message(None) is False
```

## Integration Points
- **Existing Tests**: Add to existing `TestSDKMessageDetection` class
- **Mock Strategy**: Simple single-class mock to validate isinstance() logic
- **Coverage**: Validates the exact code path that prevents AttributeError

## Validation Criteria
- Test verifies `_is_sdk_message()` returns `True` for mocked SDK objects
- Test verifies `_is_sdk_message()` returns `False` for dictionaries and None
- Test validates the isinstance() logic that was the core of the original bug fix
- Implementation takes ~15 minutes
