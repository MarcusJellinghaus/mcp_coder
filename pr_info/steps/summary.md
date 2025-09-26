# Summary: Add Mypy Checking to Implementation Workflow

## Overview
Add mypy type checking after LLM responses in `workflows/implement.py` with automatic fix attempts when issues are found.

## Architectural Changes
- **No new modules or classes** - minimal integration into existing workflow
- **Single insertion point** - add mypy check after LLM response, before formatters
- **Reuse existing infrastructure** - leverage MCP tools, ask_llm(), get_prompt()
- **Simple feedback loop** - max 3 fix attempts, then continue regardless

## Design Principles Applied
- **KISS**: One function, one integration point, minimal configuration
- **TDD**: Test the mypy integration function before implementing workflow integration
- **Clean Code**: Small functions, clear names, existing patterns

## Files Modified
```
pyproject.toml                    - Move mcp-code-checker to main dependencies
src/mcp_coder/prompts/prompts.md  - Add mypy fix prompt
workflows/implement.py            - Add mypy check function + integration
```

## Files Created
```
tests/test_mypy_integration.py    - Test mypy checking functionality
```

## Core Algorithm
```
1. LLM implements task
2. Run mypy check via MCP
3. If issues found:
   - Prompt LLM to fix (max 3 attempts)
   - Save each fix attempt to conversation
4. Continue with formatters/commit regardless
```

## Integration Points
- **After**: LLM implementation response
- **Before**: Code formatters (black, isort)
- **Uses**: Existing MCP `run_mypy_check()`, `ask_llm()`, `get_prompt()`
- **Saves**: Fix attempts to conversation log

## Success Criteria
- Mypy runs automatically after implementation
- Type errors prompt automatic fix attempts
- Workflow continues even if mypy issues remain
- All changes logged to conversation
