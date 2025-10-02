# Step 5: Extract Formatters

## Objective
Extract response formatting functions from `prompt.py` to `llm/formatting/formatters.py`. These functions format LLM responses in different verbosity levels (text, verbose, raw).

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 4 extracted SDK utilities, all tests passing
- **Current State**: Formatters are private functions in `prompt.py`
- **Target State**: Formatters are public functions in `llm/formatting/formatters.py`

## Files to Create

```
src/mcp_coder/llm/formatting/formatters.py  (NEW)
```

## Files to Modify

```
src/mcp_coder/cli/commands/prompt.py        (Extract functions, update imports)
src/mcp_coder/llm/formatting/__init__.py    (Export formatter functions)
```

## Implementation

### WHERE
- Extract from: `src/mcp_coder/cli/commands/prompt.py`
- Create: `src/mcp_coder/llm/formatting/formatters.py`
- Update: `src/mcp_coder/llm/formatting/__init__.py`

### WHAT

**Functions to Extract (3 functions):**

1. `_format_just_text(response_data: Dict[str, Any]) -> str` → `format_text_response(response_data: Dict[str, Any]) -> str`
2. `_format_verbose(response_data: Dict[str, Any]) -> str` → `format_verbose_response(response_data: Dict[str, Any]) -> str`
3. `_format_raw(response_data: Dict[str, Any]) -> str` → `format_raw_response(response_data: Dict[str, Any]) -> str`

**Signature Changes:**
- Remove leading underscore (make public)
- Rename for clarity: `_format_just_text` → `format_text_response`
- Keep all parameters and return types identical
- Keep all docstrings

### HOW

**Step 5.1: Create `formatters.py`**

```python
"""Response formatting functions for different verbosity levels.

This module provides formatters that transform LLM response data into
human-readable output formats (text, verbose, raw).
"""

import json
import logging
from typing import Any, Dict

from .sdk_serialization import extract_tool_interactions, serialize_message_for_json

logger = logging.getLogger(__name__)

__all__ = [
    "format_text_response",
    "format_verbose_response",
    "format_raw_response",
]


def format_text_response(response_data: Dict[str, Any]) -> str:
    """Format response data as simple text output (default verbosity level).
    
    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync
    
    Returns:
        Formatted string with Claude response + tool usage summary
    
    Example:
        >>> data = {"text": "Hello", "session_info": {"tools": ["file_reader"]}}
        >>> output = format_text_response(data)
        >>> print(output)
        Hello
        
        --- Used 1 tools: file_reader ---
    """
    # Extract Claude's response text
    response_text = response_data.get("text", "").strip()
    
    # Extract tools used from session info
    session_info = response_data.get("session_info", {})
    tools = session_info.get("tools", [])
    
    # Create tool usage summary
    if tools:
        tool_summary = f"Used {len(tools)} tools: {', '.join(tools)}"
    else:
        tool_summary = "No tools used"
    
    # Combine response and tool summary
    formatted_parts = []
    if response_text:
        formatted_parts.append(response_text)
    formatted_parts.append(f"\n--- {tool_summary} ---")
    
    return "\n".join(formatted_parts)


def format_verbose_response(response_data: Dict[str, Any]) -> str:
    """Format response data as verbose output with detailed metrics.
    
    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync
    
    Returns:
        Formatted string with response + tool details + metrics + session info
    
    Example:
        >>> data = {
        ...     "text": "Hello",
        ...     "session_info": {"session_id": "abc", "model": "claude-4"},
        ...     "result_info": {"duration_ms": 1000, "cost_usd": 0.01}
        ... }
        >>> output = format_verbose_response(data)
    """
    # ... (copy full implementation from prompt.py)
    # Implementation omitted for brevity - copy exactly from prompt.py


def format_raw_response(response_data: Dict[str, Any]) -> str:
    """Format response data as raw output with complete debug information.
    
    Args:
        response_data: Response dictionary from ask_claude_code_api_detailed_sync
    
    Returns:
        Formatted string with complete debugging information including JSON
    
    Example:
        >>> data = {"text": "Hello", "raw_messages": [], "api_metadata": {}}
        >>> output = format_raw_response(data)
    """
    # Start with everything from verbose format
    verbose_output = format_verbose_response(response_data)
    
    # Extract additional data for raw output
    raw_messages = response_data.get("raw_messages", [])
    api_metadata = response_data.get("api_metadata", {})
    
    # Build additional raw output sections
    formatted_parts = [verbose_output, ""]
    
    # Complete JSON API Response section
    formatted_parts.append("=== Complete JSON API Response ===")
    try:
        formatted_parts.append(
            json.dumps(response_data, indent=2, default=serialize_message_for_json)
        )
    except Exception as e:
        formatted_parts.append(f"JSON serialization failed: {e}")
    formatted_parts.append("")
    
    # ... (copy rest of implementation from prompt.py)
    # Implementation omitted for brevity - copy exactly from prompt.py
```

**Step 5.2: Update `llm/formatting/__init__.py`**

```python
"""Response formatting and SDK object serialization utilities."""

from .formatters import (
    format_raw_response,
    format_text_response,
    format_verbose_response,
)
from .sdk_serialization import (
    extract_tool_interactions,
    get_message_role,
    get_message_tool_calls,
    is_sdk_message,
    serialize_message_for_json,
)

__all__ = [
    # Formatters
    "format_text_response",
    "format_verbose_response",
    "format_raw_response",
    # SDK utilities
    "is_sdk_message",
    "get_message_role",
    "get_message_tool_calls",
    "serialize_message_for_json",
    "extract_tool_interactions",
]
```

**Step 5.3: Update `prompt.py`**

```python
# Remove the 3 private functions (_format_just_text, _format_verbose, _format_raw)
# Add import at top of file:
from ...llm.formatting.formatters import (
    format_raw_response,
    format_text_response,
    format_verbose_response,
)

# Update function calls in execute_prompt():
# _format_just_text(response_data) → format_text_response(response_data)
# _format_verbose(response_data) → format_verbose_response(response_data)
# _format_raw(response_data) → format_raw_response(response_data)
```

### ALGORITHM
```
1. Create llm/formatting/formatters.py
2. Copy 3 formatter functions from prompt.py
3. Import SDK utilities (extract_tool_interactions, etc.)
4. Update function names (remove underscores, rename)
5. Update llm/formatting/__init__.py exports
6. Update prompt.py: add import, remove functions
7. Update function calls in execute_prompt()
8. Run tests to verify output unchanged
```

### DATA

**Functions Mapping:**
```python
{
    "_format_just_text": "format_text_response",
    "_format_verbose": "format_verbose_response",
    "_format_raw": "format_raw_response",
}
```

**Response Data Structure (unchanged):**
```python
{
    "text": str,                    # Main response text
    "session_info": {               # Session metadata
        "session_id": str,
        "model": str,
        "tools": List[str],
        "mcp_servers": List[Dict]
    },
    "result_info": {                # Performance metrics
        "duration_ms": int,
        "cost_usd": float,
        "usage": {"input_tokens": int, "output_tokens": int}
    },
    "raw_messages": List[Any],      # Complete message history
    "api_metadata": Dict[str, Any]  # API response metadata
}
```

## Testing

### Test Strategy (TDD)

**Test 5.1: Unit Tests for Formatters**

Tests already exist in `test_prompt.py` but will be extracted in Step 9.
For now, verify they still pass:

```bash
# Run tests that use formatters
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt::test_verbose_output -v
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt::test_raw_output -v
pytest tests/cli/commands/test_prompt.py::TestExecutePrompt::test_verbose_vs_just_text_difference -v
```

**Test 5.2: Verify Imports**

```python
# Quick verification
def test_formatter_imports():
    """Verify formatters importable from new location."""
    from mcp_coder.llm.formatting.formatters import (
        format_text_response,
        format_verbose_response,
        format_raw_response,
    )
    
    assert callable(format_text_response)
    assert callable(format_verbose_response)
    assert callable(format_raw_response)
```

**Test 5.3: Verify Output Unchanged**

```python
def test_formatter_output_unchanged():
    """Verify formatter output identical to old implementation."""
    from mcp_coder.llm.formatting.formatters import format_text_response
    
    sample_data = {
        "text": "Test response",
        "session_info": {"tools": ["file_reader"]},
        "result_info": {}
    }
    
    output = format_text_response(sample_data)
    assert "Test response" in output
    assert "file_reader" in output
    assert "Used 1 tools" in output
```

**Test 5.4: Run Prompt Tests**

```bash
pytest tests/cli/commands/test_prompt.py -v
```

**Test 5.5: Run Full Test Suite**

```bash
pytest tests/ -v
```

### Expected Results
- Formatters work in new location
- `prompt.py` works with imported formatters
- Output format identical to before
- All existing tests pass
- No behavior changes

## Verification Checklist
- [ ] `formatters.py` created with 3 functions
- [ ] Functions made public and renamed appropriately
- [ ] All docstrings preserved/enhanced
- [ ] Imports SDK utilities correctly
- [ ] `llm/formatting/__init__.py` exports formatters
- [ ] `prompt.py` imports from new location
- [ ] All formatter calls updated
- [ ] Private formatter functions removed from `prompt.py`
- [ ] Formatter tests pass (verbose, raw, etc.)
- [ ] Output format unchanged
- [ ] Full test suite passes
- [ ] Line count of `prompt.py` reduced further

## LLM Prompt for Implementation

```
I'm implementing Step 5 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Extract formatter functions from prompt.py to llm/formatting/formatters.py.

Please:
1. Create llm/formatting/formatters.py with 3 functions:
   - _format_just_text → format_text_response
   - _format_verbose → format_verbose_response
   - _format_raw → format_raw_response

2. Copy complete implementations from prompt.py (no logic changes)

3. Import SDK utilities (extract_tool_interactions, serialize_message_for_json)

4. Update llm/formatting/__init__.py to export formatters

5. Update prompt.py:
   - Add import from llm.formatting.formatters
   - Remove the 3 private formatter functions
   - Update all formatter calls in execute_prompt()

6. Run tests:
   - pytest tests/cli/commands/test_prompt.py -v
   - Verify verbose/raw output tests still pass
   - pytest tests/ -v

This extracts pure formatting logic - output must be identical.
```

## Next Step
After this step completes successfully, proceed to **Step 6: Extract Storage Functions**.
