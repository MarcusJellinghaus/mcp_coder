# Step 8: Update Module Exports and Documentation

## Context
Update module-level exports and documentation to make new functions easily discoverable. See `pr_info/steps/summary.md` for architectural overview.

## Objective
Ensure all new functions are properly exported and documented at the package level for easy importing and IDE autocomplete.

## Changes Required

### WHERE: File Modifications

1. **File**: `src/mcp_coder/__init__.py`
2. **File**: `src/mcp_coder/llm_types.py` (verify exports)
3. **File**: `src/mcp_coder/llm_serialization.py` (verify exports)

### WHAT: Export Updates

#### Add to `__init__.py`
```python
from .llm_interface import (
    ask_llm,
    prompt_llm,  # NEW
    serialize_llm_response,  # NEW
    deserialize_llm_response,  # NEW
)
from .llm_types import LLMResponseDict, LLM_RESPONSE_VERSION  # NEW

__all__ = [
    # ... existing exports ...
    "ask_llm",
    "prompt_llm",  # NEW
    "serialize_llm_response",  # NEW
    "deserialize_llm_response",  # NEW
    "LLMResponseDict",  # NEW
    "LLM_RESPONSE_VERSION",  # NEW
]
```

### HOW: Import Patterns

```python
# Simple usage
from mcp_coder import ask_llm

# Session management
from mcp_coder import prompt_llm, serialize_llm_response

# Type hints
from mcp_coder import LLMResponseDict

# Everything
from mcp_coder import (
    ask_llm,
    prompt_llm,
    serialize_llm_response,
    deserialize_llm_response,
    LLMResponseDict,
    LLM_RESPONSE_VERSION,
)
```

### ALGORITHM: None Required
This step only updates exports.

### DATA: No Runtime Data
Only affects import structure.

## Implementation

### File 1: `src/mcp_coder/__init__.py`

**Modifications**:

```python
"""MCP Coder - AI-powered code generation and modification tool."""

# ... existing imports ...

# Add new imports
from .llm_interface import (
    ask_llm,
    prompt_llm,
    serialize_llm_response,
    deserialize_llm_response,
)
from .llm_types import LLMResponseDict, LLM_RESPONSE_VERSION

# Update __all__ to include new exports
__all__ = [
    # ... existing exports ...
    # LLM Interface
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
    # LLM Types
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]
```

### File 2: Verify `src/mcp_coder/llm_types.py`

**Check exports**:
```python
__all__ = [
    "LLMResponseDict",
    "LLM_RESPONSE_VERSION",
]
```

### File 3: Verify `src/mcp_coder/llm_serialization.py`

**Check exports**:
```python
__all__ = [
    "serialize_llm_response",
    "deserialize_llm_response",
]
```

### File 4: Verify `src/mcp_coder/llm_interface.py`

**Check exports**:
```python
__all__ = [
    "ask_llm",
    "prompt_llm",
    "serialize_llm_response",
    "deserialize_llm_response",
]
```

## Testing

### WHERE: Test File Creation/Modification
**New File**: `tests/test_module_exports.py`

### Test Cases

```python
"""Tests for module-level exports."""

import pytest


def test_ask_llm_exported_from_main_module():
    """Test that ask_llm can be imported from main module."""
    from mcp_coder import ask_llm
    assert callable(ask_llm)


def test_prompt_llm_exported_from_main_module():
    """Test that prompt_llm can be imported from main module."""
    from mcp_coder import prompt_llm
    assert callable(prompt_llm)


def test_serialization_functions_exported():
    """Test that serialization functions are exported."""
    from mcp_coder import serialize_llm_response, deserialize_llm_response
    assert callable(serialize_llm_response)
    assert callable(deserialize_llm_response)


def test_llm_types_exported():
    """Test that LLM types are exported."""
    from mcp_coder import LLMResponseDict, LLM_RESPONSE_VERSION
    assert LLMResponseDict is not None
    assert isinstance(LLM_RESPONSE_VERSION, str)


def test_all_contains_new_exports():
    """Test that __all__ includes new exports."""
    import mcp_coder
    
    required_exports = [
        "ask_llm",
        "prompt_llm",
        "serialize_llm_response",
        "deserialize_llm_response",
        "LLMResponseDict",
        "LLM_RESPONSE_VERSION",
    ]
    
    for export in required_exports:
        assert export in mcp_coder.__all__, f"{export} not in __all__"


def test_llm_interface_all_is_correct():
    """Test that llm_interface module exports correct items."""
    from mcp_coder import llm_interface
    
    expected = [
        "ask_llm",
        "prompt_llm",
        "serialize_llm_response",
        "deserialize_llm_response",
    ]
    
    assert set(llm_interface.__all__) == set(expected)


def test_llm_types_all_is_correct():
    """Test that llm_types module exports correct items."""
    from mcp_coder import llm_types
    
    expected = [
        "LLMResponseDict",
        "LLM_RESPONSE_VERSION",
    ]
    
    assert set(llm_types.__all__) == set(expected)


def test_llm_serialization_all_is_correct():
    """Test that llm_serialization module exports correct items."""
    from mcp_coder import llm_serialization
    
    expected = [
        "serialize_llm_response",
        "deserialize_llm_response",
    ]
    
    assert set(llm_serialization.__all__) == set(expected)


def test_import_all_from_mcp_coder():
    """Test that star import works correctly."""
    # Note: This is mainly for documentation, not recommended in practice
    import mcp_coder
    
    # Check that new functions are accessible
    assert hasattr(mcp_coder, "prompt_llm")
    assert hasattr(mcp_coder, "serialize_llm_response")
    assert hasattr(mcp_coder, "LLMResponseDict")


def test_no_import_errors():
    """Test that importing mcp_coder doesn't raise errors."""
    try:
        import mcp_coder
        from mcp_coder import (
            ask_llm,
            prompt_llm,
            serialize_llm_response,
            deserialize_llm_response,
            LLMResponseDict,
            LLM_RESPONSE_VERSION,
        )
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
```

## Documentation Updates

### File: `README.md` or module docstrings

**Add usage examples** (if applicable):

```markdown
## Session Management

### Simple Usage
```python
from mcp_coder import ask_llm

response = ask_llm("What is Python?")
print(response)
```

### Session-Aware Usage
```python
from mcp_coder import prompt_llm, serialize_llm_response

# Start conversation
result = prompt_llm("My favorite color is blue")
print(result["text"])
session_id = result["session_id"]

# Continue conversation
result2 = prompt_llm("What's my favorite color?", session_id=session_id)
print(result2["text"])  # "Your favorite color is blue"

# Save for analysis
serialize_llm_response(result2, f"logs/{session_id}.json")
```

### Type Hints
```python
from mcp_coder import prompt_llm, LLMResponseDict

def process_response(response: LLMResponseDict) -> str:
    return response["text"]

result = prompt_llm("Analyze this code")
processed = process_response(result)
```
```

## Validation Checklist

- [ ] `__init__.py` updated with new imports
- [ ] All new functions in `__all__` list
- [ ] Types exported from main module
- [ ] Verify exports in submodules (llm_types, llm_serialization, llm_interface)
- [ ] Tests created for module exports
- [ ] All import tests pass
- [ ] No import errors when loading module
- [ ] IDE autocomplete shows new functions
- [ ] Documentation examples added (if applicable)

## LLM Prompt

```
I am implementing Step 8 of the LLM Session Management implementation plan.

Please review:
- pr_info/steps/summary.md for architectural context
- pr_info/steps/step_7.md for the functions to be exported

For Step 8, I need to update module exports:

Requirements from pr_info/steps/step_8.md:
1. Modify src/mcp_coder/__init__.py to:
   - Import new functions: prompt_llm, serialize_llm_response, deserialize_llm_response
   - Import types: LLMResponseDict, LLM_RESPONSE_VERSION
   - Add all to __all__ list
2. Verify __all__ in submodules:
   - src/mcp_coder/llm_types.py
   - src/mcp_coder/llm_serialization.py
   - src/mcp_coder/llm_interface.py
3. Create tests/test_module_exports.py with comprehensive import tests
4. Ensure no import errors

This makes new functions discoverable via:
- from mcp_coder import prompt_llm
- IDE autocomplete
- Help system

Please implement with all tests passing.
```

## Dependencies
- **Requires**: Steps 1-7 complete (all functions implemented)

## Success Criteria
1. ✅ All new functions imported in `__init__.py`
2. ✅ All exports in `__all__` list
3. ✅ Submodule `__all__` lists verified
4. ✅ Import tests pass
5. ✅ No circular import issues
6. ✅ IDE autocomplete works
7. ✅ `from mcp_coder import *` includes new functions
8. ✅ Type hints accessible from main module
