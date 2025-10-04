# Step 1: Create CLI Utility Module

## Objective
Create the new `cli/utils.py` module with shared parameter conversion utilities and comprehensive tests following TDD principles.

## WHERE
- **New File**: `src/mcp_coder/cli/utils.py`
- **New Test File**: `tests/cli/test_utils.py`

## WHAT
### Main Function to Create
```python
def parse_llm_method_from_args(llm_method: str) -> tuple[str, str]:
    """Parse CLI llm_method into provider, method for internal APIs.
    
    Args:
        llm_method: CLI parameter ('claude_code_cli' or 'claude_code_api')
        
    Returns:
        Tuple of (provider, method) for internal API usage
        
    Raises:
        ValueError: If llm_method is not supported
    """
```

### Test Functions to Create (Unit Tests Only)
```python
def test_parse_llm_method_from_args_api()
def test_parse_llm_method_from_args_cli()
def test_parse_llm_method_from_args_invalid()
def test_parse_llm_method_from_args_empty_string()
def test_parse_llm_method_from_args_none_input()
```

## HOW
### Integration Points
```python
# Import dependency from existing LLM session module
from ..llm.session import parse_llm_method
```

### Test Integration
```python
# Mock the external dependency
@patch("mcp_coder.cli.utils.parse_llm_method")
class TestParseLLMMethodFromArgs:
    # Test cases for parameter conversion
```

## ALGORITHM
```python
# Simple wrapper logic:
1. Validate input parameter is not None/empty
2. Call existing parse_llm_method() function
3. Return the (provider, method) tuple
4. Let parse_llm_method() handle ValueError for invalid inputs
```

## DATA
### Input Parameters
- `llm_method: str` - CLI parameter ("claude_code_cli" or "claude_code_api")

### Return Value
```python
tuple[str, str]
# (provider, method)

# API case:
("claude", "api")

# CLI case:
("claude", "cli")
```

### Test Data Structures
```python
# Test cases for parameter conversion
TEST_CASES = [
    ("claude_code_api", ("claude", "api")),
    ("claude_code_cli", ("claude", "cli")),
]

INVALID_CASES = [
    "invalid_method",
    "openai_api",
    "",
    None,
]
```

## LLM Prompt for Implementation

```
You are implementing Step 1 of the LLM parameter architecture improvement. 

Reference the summary.md for full context. Your task is to:

1. Create `src/mcp_coder/cli/utils.py` with the `parse_llm_method_from_args()` function that provides a shared utility for all CLI commands.

2. Create comprehensive tests in `tests/cli/test_utils.py` that cover:
   - Successful parameter conversion for both API and CLI methods
   - Error handling for invalid input values
   - Edge cases like empty strings and None inputs
   - Verify the function properly delegates to existing parse_llm_method()

The goal is to create a shared utility that eliminates code duplication across CLI commands. Follow TDD - write tests first, then implement the function.

Key requirements:
- Function should be a simple wrapper around existing parse_llm_method()
- Proper error handling and input validation
- Clear documentation for CLI usage
- All tests should mock the underlying parse_llm_method() dependency
- Function should be importable by other CLI command modules
```
