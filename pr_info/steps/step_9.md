# Step 9: Extract Formatting Tests

## Objective
Extract formatting and SDK utility tests from `test_prompt.py` to dedicated test files that mirror the code structure.

## Context
- **Reference**: See `pr_info/steps/summary.md` for architectural overview
- **Previous Step**: Step 8 moved core tests, all tests passing
- **Current State**: Formatting tests buried in 800+ line `test_prompt.py`
- **Target State**: Formatting tests in `tests/llm/formatting/` matching code structure

## Files to Create

```
tests/llm/formatting/test_formatters.py         (NEW - extract from test_prompt.py)
```

## Files to Move

```
tests/cli/commands/test_prompt_sdk_utilities.py → tests/llm/formatting/test_sdk_serialization.py
```

## Files to Modify

```
tests/cli/commands/test_prompt.py               (Remove extracted tests)
tests/llm/formatting/test_sdk_serialization.py  (Update imports)
```

## Implementation

### WHERE
- Extract from: `tests/cli/commands/test_prompt.py`
- Move: `test_prompt_sdk_utilities.py` → `test_sdk_serialization.py`
- Create: `tests/llm/formatting/test_formatters.py`

### WHAT

**Tests to Extract to `test_formatters.py` (~300 lines):**
1. `test_verbose_output()` - Test verbose formatting
2. `test_raw_output()` - Test raw formatting
3. `test_verbose_vs_just_text_difference()` - Compare format outputs
4. `test_raw_vs_verbose_difference()` - Compare format outputs

**File to Move:**
- `test_prompt_sdk_utilities.py` → `test_sdk_serialization.py`
- Update all imports (remove underscores from function names)

### HOW

**Step 9.1: Move SDK Utilities Tests**

```bash
# Move file
git mv tests/cli/commands/test_prompt_sdk_utilities.py \
       tests/llm/formatting/test_sdk_serialization.py
```

**Step 9.2: Update Imports in `test_sdk_serialization.py`**

```python
# In tests/llm/formatting/test_sdk_serialization.py

# OLD imports
from mcp_coder.cli.commands.prompt import (
    _extract_tool_interactions,
    _get_message_role,
    _get_message_tool_calls,
    _is_sdk_message,
    _serialize_message_for_json,
)

# NEW imports
from mcp_coder.llm.formatting.sdk_serialization import (
    extract_tool_interactions,
    get_message_role,
    get_message_tool_calls,
    is_sdk_message,
    serialize_message_for_json,
)

# Update all function calls to remove underscores
# _is_sdk_message() → is_sdk_message()
# _get_message_role() → get_message_role()
# etc.
```

**Step 9.3: Create `test_formatters.py`**

Extract these test methods from `test_prompt.py`:

```python
"""Tests for response formatting functions."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from mcp_coder.llm.formatting.formatters import (
    format_text_response,
    format_verbose_response,
    format_raw_response,
)


class TestFormatTextResponse:
    """Tests for format_text_response function."""
    
    def test_basic_text_formatting(self):
        """Test basic text response formatting."""
        response_data = {
            "text": "Here's how to create a file.",
            "session_info": {"tools": ["file_writer"]},
            "result_info": {}
        }
        
        output = format_text_response(response_data)
        
        assert "Here's how to create a file." in output
        assert "file_writer" in output
        assert "Used 1 tools" in output


class TestFormatVerboseResponse:
    """Tests for format_verbose_response function."""
    
    # Extract test_verbose_output() from test_prompt.py
    # Adapt to test the function directly, not via CLI
    
    def test_verbose_formatting_with_metrics(self):
        """Test verbose output includes performance metrics."""
        response_data = {
            "text": "Response text",
            "session_info": {
                "session_id": "test-session-123",
                "model": "claude-sonnet-4",
                "tools": ["file_reader"],
            },
            "result_info": {
                "duration_ms": 2000,
                "cost_usd": 0.04,
                "usage": {"input_tokens": 20, "output_tokens": 15}
            },
            "raw_messages": []
        }
        
        output = format_verbose_response(response_data)
        
        # Verify all verbose sections present
        assert "Response text" in output
        assert "test-session-123" in output
        assert "claude-sonnet-4" in output
        assert "2000" in output or "2.0" in output  # Duration
        assert "0.04" in output  # Cost
        assert "20" in output  # Input tokens
        assert "15" in output  # Output tokens


class TestFormatRawResponse:
    """Tests for format_raw_response function."""
    
    # Extract test_raw_output() from test_prompt.py
    # Adapt to test the function directly
    
    def test_raw_formatting_includes_json(self):
        """Test raw output includes complete JSON structures."""
        response_data = {
            "text": "Response text",
            "session_info": {"session_id": "raw-123"},
            "result_info": {"duration_ms": 1000},
            "raw_messages": [],
            "api_metadata": {"request_id": "req-123"}
        }
        
        output = format_raw_response(response_data)
        
        # Verify raw-specific content
        assert "req-123" in output  # API metadata
        assert "{" in output  # JSON structures
        assert "}" in output


class TestFormatterComparison:
    """Tests comparing different formatter outputs."""
    
    # Extract test_verbose_vs_just_text_difference() from test_prompt.py
    # Extract test_raw_vs_verbose_difference() from test_prompt.py
    
    def test_verbose_contains_more_than_text(self):
        """Test that verbose output contains more detail than text output."""
        response_data = {
            "text": "Test response",
            "session_info": {"session_id": "compare-123", "tools": []},
            "result_info": {"duration_ms": 1000, "cost_usd": 0.01},
            "raw_messages": []
        }
        
        text_output = format_text_response(response_data)
        verbose_output = format_verbose_response(response_data)
        
        # Verbose should be longer
        assert len(verbose_output) > len(text_output)
        
        # Verbose should contain session ID, text shouldn't
        assert "compare-123" in verbose_output
        assert "compare-123" not in text_output
    
    def test_raw_contains_more_than_verbose(self):
        """Test that raw output contains more detail than verbose output."""
        response_data = {
            "text": "Test response",
            "session_info": {"session_id": "compare-456"},
            "result_info": {"duration_ms": 2000},
            "raw_messages": [],
            "api_metadata": {"request_id": "unique-req-789"}
        }
        
        verbose_output = format_verbose_response(response_data)
        raw_output = format_raw_response(response_data)
        
        # Raw should be longer
        assert len(raw_output) > len(verbose_output)
        
        # Raw should contain request ID, verbose shouldn't
        assert "unique-req-789" in raw_output
        assert "unique-req-789" not in verbose_output
```

**Step 9.4: Remove Tests from `test_prompt.py`**

Remove these test methods:
- `test_verbose_output()`
- `test_raw_output()`
- `test_verbose_vs_just_text_difference()`
- `test_raw_vs_verbose_difference()`

### ALGORITHM
```
1. Move test_prompt_sdk_utilities.py → test_sdk_serialization.py
2. Update imports in test_sdk_serialization.py (remove underscores)
3. Create test_formatters.py
4. Extract 4 test methods from test_prompt.py
5. Adapt tests to call formatter functions directly
6. Remove extracted tests from test_prompt.py
7. Run formatting tests
8. Run prompt tests (verify removal didn't break anything)
9. Run full test suite
```

### DATA

**Test Files Mapping:**
```python
{
    "test_prompt_sdk_utilities.py": "llm/formatting/test_sdk_serialization.py",
    "test_prompt.py (partial)": "llm/formatting/test_formatters.py",
}
```

**Function Name Updates (in test_sdk_serialization.py):**
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

**Test 9.1: Run SDK Serialization Tests**

```bash
# After move and import updates
pytest tests/llm/formatting/test_sdk_serialization.py -v
```

**Test 9.2: Run Formatter Tests**

```bash
# New formatter tests
pytest tests/llm/formatting/test_formatters.py -v
```

**Test 9.3: Run Prompt Tests**

```bash
# Verify test_prompt.py still works after removal
pytest tests/cli/commands/test_prompt.py -v
```

**Test 9.4: Run All Formatting Tests**

```bash
pytest tests/llm/formatting/ -v
```

**Test 9.5: Run Full Test Suite**

```bash
pytest tests/ -v
```

### Expected Results
- SDK serialization tests pass in new location
- Formatter tests pass independently
- `test_prompt.py` still passes (reduced size)
- All formatting tests organized under `tests/llm/formatting/`
- Test structure mirrors code structure

## Verification Checklist
- [ ] `test_prompt_sdk_utilities.py` moved to `test_sdk_serialization.py`
- [ ] Imports updated in `test_sdk_serialization.py` (no underscores)
- [ ] `test_formatters.py` created with 4 extracted tests
- [ ] Tests adapted to call functions directly (not via CLI)
- [ ] Extracted tests removed from `test_prompt.py`
- [ ] SDK serialization tests pass
- [ ] Formatter tests pass
- [ ] Prompt tests pass
- [ ] All formatting tests pass
- [ ] Full test suite passes
- [ ] `test_prompt.py` line count reduced

## LLM Prompt for Implementation

```
I'm implementing Step 9 of the LLM module refactoring as described in pr_info/steps/summary.md.

Task: Extract formatting tests from test_prompt.py and move SDK utility tests.

Please:
1. Move test_prompt_sdk_utilities.py → tests/llm/formatting/test_sdk_serialization.py

2. Update imports in test_sdk_serialization.py:
   - from mcp_coder.cli.commands.prompt import _func
   - from mcp_coder.llm.formatting.sdk_serialization import func
   - Remove all underscores from function names

3. Create tests/llm/formatting/test_formatters.py
   - Extract these tests from test_prompt.py:
     * test_verbose_output
     * test_raw_output
     * test_verbose_vs_just_text_difference
     * test_raw_vs_verbose_difference
   - Adapt to test formatter functions directly
   - Import from mcp_coder.llm.formatting.formatters

4. Remove extracted tests from test_prompt.py

5. Run tests:
   - pytest tests/llm/formatting/ -v
   - pytest tests/cli/commands/test_prompt.py -v
   - pytest tests/ -v

This extracts and reorganizes tests - no test logic changes.
```

## Next Step
After this step completes successfully, proceed to **Step 10: Extract Storage/Session Tests**.
