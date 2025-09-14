# Step 2: Move CLI Implementation to Dedicated Module

## Objective
Extract the existing CLI-based Claude Code implementation from `claude_client.py` into a dedicated `claude_code_cli.py` module to prepare for the extensible architecture.

## WHERE
- `src/mcp_coder/claude_code_cli.py` (new) - Move existing implementation
- `src/mcp_coder/claude_client.py` (modify) - Keep as compatibility wrapper
- `tests/test_claude_code_cli.py` (new) - Move existing tests

## WHAT
### Main Functions:
```python
# src/mcp_coder/claude_code_cli.py
def _find_claude_executable() -> str
def ask_claude_code_cli(question: str, timeout: int = 30) -> str
```

### Compatibility Layer:
```python
# src/mcp_coder/claude_client.py
def ask_claude(question: str, timeout: int = 30) -> str  # Wrapper to ask_claude_code_cli
```

## HOW
### Integration Points:
- Move all CLI-specific logic to new module
- Import `ask_claude_code_cli` in `claude_client.py`
- Update `__init__.py` exports to maintain backward compatibility

### Imports:
```python
# claude_code_cli.py
from .subprocess_runner import execute_command

# claude_client.py  
from .claude_code_cli import ask_claude_code_cli
```

## ALGORITHM
```pseudocode
1. Copy existing ask_claude() function to claude_code_cli.py
2. Rename ask_claude() to ask_claude_code_cli() in new module
3. Copy _find_claude_executable() helper function
4. Create wrapper ask_claude() that calls ask_claude_code_cli()
5. Update imports and maintain exact same API
6. Move existing tests to test_claude_code_cli.py
```

## DATA
### Input:
- Current `claude_client.py` implementation
- Existing test suite

### Output:
- `claude_code_cli.py` with CLI-specific implementation
- `claude_client.py` as thin compatibility wrapper
- All existing tests passing with new structure

## Testing Strategy
- Copy existing tests to `test_claude_code_cli.py`
- Verify `ask_claude()` still works exactly as before
- Test that all error handling is preserved
- Integration tests should pass without changes

## LLM Prompt for Implementation
```
I need to implement Step 2 of the LLM interface refactoring plan. Please:

1. Read the summary from pr_info/steps/summary.md to understand the target architecture
2. Create src/mcp_coder/claude_code_cli.py by moving the existing implementation from claude_client.py
3. Rename ask_claude() to ask_claude_code_cli() in the new module
4. Keep claude_client.py as a thin wrapper that imports and calls ask_claude_code_cli()
5. Move the existing tests to tests/test_claude_code_cli.py and update them to test the new function names
6. Ensure all existing functionality works exactly the same - this is just a restructuring step

The goal is to separate CLI-specific implementation while maintaining 100% backward compatibility.
```
