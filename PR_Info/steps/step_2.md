# Step 2: Create Message Format Detection and Unified Access Utilities

## LLM Prompt
```
Based on the summary in pr_info/steps/summary.md and Step 1 results, implement Step 2 to create utility functions for detecting message format (dictionary vs SDK object) and providing unified access to message data. These utilities will enable the prompt formatting functions to work with both test mocks and real Claude SDK objects.

The tests from Step 1 should still be failing at this point. These utilities will be used in Steps 3-4 to fix the actual formatting functions.
```

## WHERE
- **File**: `src/mcp_coder/cli/commands/prompt.py`
- **Location**: Add utility functions at module level (before existing functions)

## WHAT
- **Function**: `_is_sdk_message(message: Any) -> bool`
- **Function**: `_get_message_role(message: Any) -> Optional[str]`
- **Function**: `_get_message_tool_calls(message: Any) -> List[Dict[str, Any]]`
- **Function**: `_extract_tool_interactions(raw_messages: List[Any]) -> List[str]`

## HOW
- **Import Addition**: `from typing import Any, List, Optional`
- **SDK Import**: `from ...llm_providers.claude.claude_code_api import SystemMessage, AssistantMessage, ResultMessage`
- **Type Checking**: Use `isinstance()` and `hasattr()` for safe type detection
- **Error Handling**: Graceful fallbacks for unexpected message formats

## ALGORITHM
```python
# Message format detection and unified access
1. Check if message is SDK object using isinstance()
2. For SDK objects: access attributes directly (message.role, message.tool_calls)
3. For dictionaries: use .get() method with defaults
4. Extract tool interactions by iterating messages with unified accessors
5. Return standardized data structures regardless of input format
```

## DATA
**Function Signatures**:
```python
def _is_sdk_message(message: Any) -> bool:
    """Check if message is a Claude SDK object vs dictionary."""

def _get_message_role(message: Any) -> Optional[str]:
    """Get role from message (SDK object or dict)."""

def _get_message_tool_calls(message: Any) -> List[Dict[str, Any]]:
    """Get tool calls from message (SDK object or dict)."""

def _extract_tool_interactions(raw_messages: List[Any]) -> List[str]:
    """Extract tool interaction summaries from raw messages."""
```

**Return Examples**:
- `_is_sdk_message()`: `True` for SDK objects, `False` for dicts
- `_get_message_role()`: `"assistant"`, `"user"`, or `None`
- `_get_message_tool_calls()`: `[{"name": "tool_name", "parameters": {...}}]`
- `_extract_tool_interactions()`: `["tool_name: {...}", "other_tool: {...}"]`

## Integration Points
- **Backward Compatibility**: Functions must work with existing dictionary test mocks
- **Forward Compatibility**: Functions must work with real Claude SDK message objects  
- **Error Resilience**: Handle malformed or unexpected message structures gracefully
- **Type Safety**: Proper type hints and isinstance() checks

## Validation Criteria
- `_is_sdk_message()` correctly identifies SDK objects vs dictionaries
- `_get_message_role()` returns correct role for both message formats
- `_get_message_tool_calls()` extracts tool calls from both formats
- `_extract_tool_interactions()` produces consistent output for both formats
- All functions handle edge cases (None, empty lists, malformed data) gracefully
- Tests from Step 1 still fail (utilities not yet integrated into formatters)
