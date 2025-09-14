# Step 4: Implement Basic Python SDK Client

## Objective
Create a basic Python SDK implementation that provides the same functionality as the CLI version, establishing the "api" method option.

## WHERE
- `src/mcp_coder/claude_code_api.py` (new) - Python SDK implementation
- `src/mcp_coder/claude_code_interface.py` (modify) - Add API routing
- `tests/test_claude_code_api.py` (new) - Test SDK implementation
- `tests/test_claude_code_integration.py` (modify) - Add API integration tests

## WHAT
### Main Functions:
```python
# src/mcp_coder/claude_code_api.py
def ask_claude_code_api(question: str, timeout: int = 30) -> str
def _create_claude_client() -> Any  # Helper to create SDK client
```

### Updated Routing:
```python
# claude_code_interface.py (modified)
def ask_claude_code(question: str, method: str = "cli", timeout: int = 30) -> str
    # Now supports method="api" in addition to method="cli"
```

## HOW
### Integration Points:
- Import `claude_code_sdk` package
- Use `query()` function from SDK with basic configuration
- Handle async/await pattern by using `anyio.run()` or similar
- Integrate with existing error handling patterns

### Imports:
```python
# claude_code_api.py
import anyio
from claude_code_sdk import query, ClaudeCodeOptions

# claude_code_interface.py (add)
from .claude_code_api import ask_claude_code_api
```

## ALGORITHM
```pseudocode
1. Create ClaudeCodeOptions with basic configuration
2. Call query() function with question and options
3. Iterate through async response messages
4. Extract text content from response
5. Return concatenated response as string
6. Handle errors and convert to consistent exception types
```

## DATA
### Input:
- `question: str` - The question to ask Claude
- `timeout: int` - Timeout in seconds (map to SDK options)

### Output:
- `str` - Claude's response text
- Raises same exception types as CLI version for consistency
- `ClaudeCodeOptions` object for SDK configuration

### SDK Response Format:
- AsyncIterator[Message] from query()
- Extract text content from message objects

## Testing Strategy
- Test basic question/answer functionality
- Test timeout handling
- Test error scenarios (API key missing, network issues)
- Compare responses with CLI version for consistency
- Mock SDK calls for unit tests
- Add integration test marked with `@pytest.mark.integration`

## LLM Prompt for Implementation
```
I need to implement Step 4 of the LLM interface refactoring plan. Please:

⚠️ **PREREQUISITES**: Ensure that claude-code-sdk dependency has been installed (from Step 1) before proceeding.

1. Read the summary from pr_info/steps/summary.md to understand the overall architecture
2. Verify that `import claude_code_sdk` works - if not, STOP and request dependency installation
3. Create src/mcp_coder/claude_code_api.py with ask_claude_code_api() function using the claude-code-sdk
4. Use the SDK's query() function with basic ClaudeCodeOptions configuration
5. Handle the async nature of the SDK by using anyio.run() or similar synchronous wrapper
6. Update claude_code_interface.py to support method="api" and route to the new function
7. Create comprehensive tests including error handling and integration tests
8. Keep the implementation simple - just match the basic functionality of the CLI version

**IMPORTANT**: If claude_code_sdk import fails, stop immediately and alert that dependencies need to be installed first.
```
