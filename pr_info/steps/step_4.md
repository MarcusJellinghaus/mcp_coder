# Step 4: Extract SDK Utilities

## Objective
Extract SDK message handling utilities from `prompt.py` to `llm/formatting/sdk_serialization.py`. These are pure functions that work with both dictionary and SDK object message formats.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 3 moved providers, all tests passing
- **Current State**: SDK utilities are private functions in `prompt.py`
- **Target State**: SDK utilities are public functions in `llm/formatting/sdk_serialization.py`

## Files to Create

```
src/mcp_coder/llm/formatting/sdk_serialization.py  (NEW)
```

## Files to Modify

```
src/mcp_coder/cli/commands/prompt.py               (Extract functions, update imports)
src/mcp_coder/llm/formatting/__init__.py           (Export public functions)
```

## Implementation

### WHERE
- Extract from: `src/mcp_coder/cli/commands/prompt.py`
- Create: `src/mcp_coder/llm/formatting/sdk_serialization.py`
- Update: `src/mcp_coder/llm/formatting/__init__.py`

### WHAT

**Functions to Extract (5 functions):**

1. `_is_sdk_message(message: Any) -> bool` → `is_sdk_message(message: Any) -> bool`
2. `_get_message_role(message: Any) -> Optional[str]` → `get_message_role(message: Any) -> Optional[str]`
3. `_get_message_tool_calls(message: Any) -> List[Dict[str, Any]]` → `get_message_tool_calls(message: Any) -> List[Dict[str, Any]]`
4. `_serialize_message_for_json(obj: Any) -> Any` → `serialize_message_for_json(obj: Any) -> Any`
5. `_extract_tool_interactions(raw_messages: List[Any]) -> List[str]` → `extract_tool_interactions(raw_messages: List[Any]) -> List[str]`

**Signature Changes:**
- Remove leading underscore (make public)
- Keep all parameters and return types identical
- Keep all docstrings (enhance if needed)

### HOW

**Step 4.1: Create `sdk_serialization.py`**

```python
"""SDK message object serialization and handling utilities.

This module provides utilities for working with Claude SDK message objects
and dictionary message formats, enabling unified handling of both formats.

Dual Message Format Compatibility:
This module handles two different message formats:
1. Dictionary format: {"role": "assistant", "content": "text"}
2. SDK object format: AssistantMessage(content=[...])

The utility functions provide unified access to both formats.
"""

import logging
from typing import Any, Dict, List, Optional

from ..providers.claude.claude_code_api import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    UserMessage,
)

logger = logging.getLogger(__name__)

__all__ = [
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
]


def is_sdk_message(message: Any) -> bool:
    """Check if message is a Claude SDK object vs dictionary.
    
    Args:
        message: Message object to check (can be SDK object, dict, or None)
    
    Returns:
        True if message is a Claude SDK object, False otherwise
    """
    if message is None:
        return False
    return isinstance(
        message, (SystemMessage, AssistantMessage, ResultMessage, UserMessage)
    )


def get_message_role(message: Any) -> Optional[str]:
    """Get role from message (SDK object or dict).
    
    Args:
        message: Message object (SDK object, dictionary, or None)
    
    Returns:
        Role string or None if not available
    """
    if message is None:
        return None
    
    if is_sdk_message(message):
        if hasattr(message, "role"):
            role_value = getattr(message, "role", None)
            if isinstance(role_value, str):
                return role_value
        # Infer role from SDK message type
        if isinstance(message, AssistantMessage):
            return "assistant"
        elif isinstance(message, SystemMessage):
            return "system"
        elif isinstance(message, ResultMessage):
            return "result"
        return None
    else:
        if isinstance(message, dict):
            return message.get("role")
        return None


def get_message_tool_calls(message: Any) -> List[Dict[str, Any]]:
    """Get tool calls from message (SDK object or dict).
    
    Args:
        message: Message object (SDK object or dictionary)
    
    Returns:
        List of tool call dictionaries
    """
    # ... (copy full implementation from prompt.py)
    # Implementation omitted for brevity - copy exactly from prompt.py


def serialize_message_for_json(obj: Any) -> Any:
    """Convert SDK message objects to JSON-serializable format.
    
    Args:
        obj: Object to serialize (SDK message or any other object)
    
    Returns:
        For SDK objects: Dictionary representation
        For other objects: The object unchanged
    """
    # ... (copy full implementation from prompt.py)
    # Implementation omitted for brevity - copy exactly from prompt.py


def extract_tool_interactions(raw_messages: List[Any]) -> List[str]:
    """Extract tool interaction summaries from raw messages.
    
    Args:
        raw_messages: List of message objects (SDK objects or dictionaries)
    
    Returns:
        List of tool interaction summary strings
    """
    # ... (copy full implementation from prompt.py)
    # Implementation omitted for brevity - copy exactly from prompt.py
```

**Step 4.2: Update `llm/formatting/__init__.py`**

```python
"""Response formatting and SDK object serialization utilities."""

from .sdk_serialization import (
    extract_tool_interactions,
    get_message_role,
    get_message_tool_calls,
    is_sdk_message,
    serialize_message_for_json,
)

__all__ = [
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
]
```

**Step 4.3: Update `prompt.py`**

```python
# Remove the 5 private functions (_is_sdk_message, etc.)
# Add import at top of file:
from ...llm.formatting.sdk_serialization import (
    extract_tool_interactions,
    get_message_role,
    get_message_tool_calls,
    is_sdk_message,
    serialize_message_for_json,
)

# Update all function calls:
# _is_sdk_message() → is_sdk_message()
# _get_message_role() → get_message_role()
# _get_message_tool_calls() → get_message_tool_calls()
# _serialize_message_for_json() → serialize_message_for_json()
# _extract_tool_interactions() → extract_tool_interactions()
```

### ALGORITHM
```
1. Create llm/formatting/sdk_serialization.py
2. Copy 5 functions from prompt.py (remove underscores)
3. Add imports for SDK types
4. Update llm/formatting/__init__.py exports
5. Update prompt.py: add import, remove functions
6. Find/replace function calls in prompt.py
7. Run tests to verify behavior unchanged
```

### DATA

**Functions Mapping:**
```python
{
    "_is_sdk_message": "is_sdk_message",
    "_get_message_role": "get_message_role",
    "_get_message_tool_calls": "get_message_tool_calls",
    "_serialize_message_for_json": "serialize_message_for_json",
    "_extract_tool_interactions": "extract_tool_interactions",
}
```

## Testing

### Test Strategy (TDD)

**Test 4.1: Create Unit Tests (copy from existing)**

The tests already exist in `tests/cli/commands/test_prompt_sdk_utilities.py`.
For now, just verify they still pass with the old imports. We'll move these tests in Step 8.

```bash
# Run existing SDK utility tests
pytest tests/cli/commands/test_prompt_sdk_utilities.py -v
```

**Test 4.2: Verify Functions Work in New Location**

```python
# Quick verification test (can be temporary)
def test_sdk_serialization_imports():
    """Verify SDK utilities importable from new location."""
    from mcp_coder.llm.formatting.sdk_serialization import (
        is_sdk_message,
        get_message_role,
        get_message_tool_calls,
        serialize_message_for_json,
        extract_tool_interactions,
    )
    
    # Basic smoke tests
    assert callable(is_sdk_message)
    assert callable(get_message_role)
    assert callable(get_message_tool_calls)
    assert callable(serialize_message_for_json)
    assert callable(extract_tool_interactions)
    
    # Test with None
    assert is_sdk_message(None) is False
    assert get_message_role(None) is None
    assert get_message_tool_calls(None) == []
```

**Test 4.3: Run Prompt Tests**

```bash
# Ensure prompt.py still works with new imports
pytest tests/cli/commands/test_prompt.py -v
```

**Test 4.4: Run Full Test Suite**

```bash
pytest tests/ -v
```

### Expected Results
- SDK utilities work in new location
- `prompt.py` works with imported functions
- All existing tests pass unchanged
- No behavior changes

## Verification Checklist
- [ ] `sdk_serialization.py` created with 5 functions
- [ ] Functions made public (no underscores)
- [ ] All docstrings preserved/enhanced
- [ ] `llm/formatting/__init__.py` exports functions
- [ ] `prompt.py` imports from new location
- [ ] All function calls updated (no underscores)
- [ ] Private functions removed from `prompt.py`
- [ ] SDK utility tests pass
- [ ] Prompt tests pass
- [ ] Full test suite passes
- [ ] Line count of `prompt.py` reduced

## LLM Prompt for Implementation

```
I'm implementing Step 4 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Extract SDK utility functions from prompt.py to llm/formatting/sdk_serialization.py.

Please:
1. Create llm/formatting/sdk_serialization.py with 5 functions:
   - _is_sdk_message → is_sdk_message (remove underscore)
   - _get_message_role → get_message_role
   - _get_message_tool_calls → get_message_tool_calls
   - _serialize_message_for_json → serialize_message_for_json
   - _extract_tool_interactions → extract_tool_interactions

2. Copy complete implementations from prompt.py (no changes to logic)

3. Add necessary imports (SDK types from providers)

4. Update llm/formatting/__init__.py to export these functions

5. Update prompt.py:
   - Add import from llm.formatting.sdk_serialization
   - Remove the 5 private functions
   - Update all function calls (remove underscores)

6. Run tests:
   - pytest tests/cli/commands/test_prompt_sdk_utilities.py -v
   - pytest tests/cli/commands/test_prompt.py -v
   - pytest tests/ -v

This extracts pure functions - no behavior changes allowed.
```

## Next Step
After this step completes successfully, proceed to **Step 5: Extract Formatters**.
