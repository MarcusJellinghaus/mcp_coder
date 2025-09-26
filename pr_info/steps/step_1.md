# Step 1: Add Core Tests for prompt_claude Function

## Goal
Implement comprehensive tests for the new `prompt_claude` function before implementing the function itself, following Test-Driven Development principles.

## WHERE
- **File**: `tests/cli/commands/test_prompt.py`
- **Section**: Add new test class `TestPromptClaude` after existing test classes

## WHAT
Add test class and methods to verify:

### Main Test Methods
```python
def test_prompt_claude_basic_success(self) -> None
def test_prompt_claude_with_custom_timeout(self) -> None  
def test_prompt_claude_with_verbosity_levels(self) -> None
def test_prompt_claude_error_handling(self) -> None
```

## HOW
- **Integration**: Add test class to existing test file
- **Imports**: Use existing imports, add new import for `prompt_claude`
- **Mocking**: Reuse existing mock patterns for `ask_claude_code_api_detailed_sync`

## ALGORITHM
```
1. Mock Claude API with predefined response
2. Call prompt_claude with various parameter combinations
3. Verify function returns correct exit codes (0/1)
4. Assert Claude API called with expected parameters
5. Validate output format matches verbosity level
```

## DATA

### Test Input Parameters
```python
# Basic test
prompt_claude("Hello Claude")

# With custom parameters  
prompt_claude("Test prompt", verbosity="verbose", timeout=60)

# Error case
prompt_claude("Test") # with API exception
```

### Expected Return Values
- **Success cases**: `return 0`
- **Error cases**: `return 1`
- **API calls**: Verify `ask_claude_code_api_detailed_sync` called with correct parameters

### Mock Response Structure
```python
mock_response = {
    "text": "Test response text",
    "session_info": {
        "session_id": "test-session-id",
        "model": "claude-sonnet-4", 
        "tools": ["test_tool"]
    },
    "result_info": {
        "duration_ms": 1500,
        "cost_usd": 0.02,
        "usage": {"input_tokens": 10, "output_tokens": 8}
    },
    "raw_messages": []
}
```

## Implementation Notes
- Tests should fail initially (function doesn't exist yet)
- Use `@patch` decorators for mocking Claude API
- Follow existing test patterns in the file
- Include edge cases: empty responses, API errors, invalid parameters

## LLM Prompt for Implementation

```
Please implement Step 1 of the execute_prompt refactoring project (see pr_info/steps/summary.md).

Add comprehensive tests for a new function called prompt_claude() to tests/cli/commands/test_prompt.py.

The function signature should be:
```python
def prompt_claude(
    prompt: str,
    verbosity: str = "just-text", 
    timeout: int = 30,
    store_response: bool = False,
    continue_from: Optional[str] = None,
    continue_latest: bool = False,
    save_conversation_md: Optional[str] = None,
    save_conversation_full_json: Optional[str] = None
) -> int
```

Add a new test class TestPromptClaude with tests for:
1. Basic successful execution with minimal parameters
2. Custom timeout parameter handling
3. Different verbosity levels (just-text, verbose, raw)
4. Error handling when Claude API fails

Follow the existing test patterns in the file, use the same mocking strategies, and ensure tests will fail initially since the function doesn't exist yet.

The function should be imported from: mcp_coder.cli.commands.prompt import prompt_claude
```
