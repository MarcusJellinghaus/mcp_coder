# Step 3: Create High-Level LLM Interface

## Objective
Create the top-level `ask_llm()` function and Claude-specific routing logic to establish the extensible architecture foundation.

## WHERE
- `src/mcp_coder/llm_interface.py` (new) - High-level interface
- `src/mcp_coder/claude_code_interface.py` (new) - Claude-specific routing
- `src/mcp_coder/__init__.py` (modify) - Add new exports
- `tests/test_llm_interface.py` (new) - Test new interface

## WHAT
### Main Functions:
```python
# src/mcp_coder/llm_interface.py
def ask_llm(question: str, provider: str = "claude", method: str = "cli", timeout: int = 30) -> str

# src/mcp_coder/claude_code_interface.py  
def ask_claude_code(question: str, method: str = "cli", timeout: int = 30) -> str
```

## HOW
### Integration Points:
- `ask_llm()` routes to provider-specific functions
- `ask_claude_code()` routes between CLI and API methods
- Import existing `ask_claude_code_cli` function
- Prepare for future `ask_claude_code_api` function

### Imports:
```python
# llm_interface.py
from .claude_code_interface import ask_claude_code

# claude_code_interface.py
from .claude_code_cli import ask_claude_code_cli
```

## ALGORITHM
```pseudocode
1. ask_llm() validates provider parameter
2. Routes to ask_claude_code() for "claude" provider  
3. ask_claude_code() validates method parameter
4. Routes to ask_claude_code_cli() for "cli" method
5. Returns result with consistent error handling
6. Raises ValueError for unsupported providers/methods
```

## DATA
### Input:
- `question: str` - The question to ask the LLM
- `provider: str` - LLM provider ("claude" for now)
- `method: str` - Implementation method ("cli" for now, "api" coming soon)
- `timeout: int` - Timeout in seconds

### Output:
- `str` - LLM response
- Raises `ValueError` for invalid parameters
- Preserves existing exception types from CLI implementation

## Testing Strategy
- Test `ask_llm()` with valid parameters routes correctly
- Test invalid provider/method parameters raise ValueError
- Test that existing CLI functionality works through new interface
- Mock underlying functions to test routing logic

## LLM Prompt for Implementation
```
I need to implement Step 3 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand the target architecture
2. Create src/mcp_coder/llm_interface.py with ask_llm() function that routes to provider-specific implementations
3. Create src/mcp_coder/claude_code_interface.py with ask_claude_code() that routes between different Claude Code methods
4. For now, only support provider="claude" and method="cli", but design for extensibility
5. Add comprehensive tests in tests/test_llm_interface.py
6. Update src/mcp_coder/__init__.py to export the new ask_llm function

Focus on clean routing logic and parameter validation. This establishes the foundation for the extensible architecture.
```
