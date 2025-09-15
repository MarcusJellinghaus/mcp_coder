# Refactor for Extensible LLM Interface

## Overview
Refactor the current `ask_claude()` function to create an extensible architecture that supports multiple LLM clients. Currently, the codebase only supports Claude Code CLI. The goal is to add a Python SDK implementation with a clean, extensible interface.

## Current Architecture
```
ask_claude() -> _find_claude_executable() -> execute_command() -> Claude Code CLI
```

## Target Architecture
```
ask_llm() -> ask_claude_code() -> ask_claude_code_cli() (existing)
                               -> ask_claude_code_api() (new)
```

## Key Design Principles
- **Extensibility**: Easy to add new LLM clients in the future
- **Clean Architecture**: Clear separation between CLI and API implementations
- **KISS Principle**: Minimal complexity, maximum maintainability
- **Essential Testing**: Focus on core functionality and method equivalence

## Files to be Created/Modified
- `src/mcp_coder/llm_interface.py` (new) - High-level interface
- `src/mcp_coder/claude_code_interface.py` (new) - Claude-specific routing
- `src/mcp_coder/claude_code_cli.py` (new) - Move existing CLI implementation
- `src/mcp_coder/claude_code_api.py` (new) - Python SDK implementation
- `src/mcp_coder/claude_client.py` (modify) - Simplified as compatibility wrapper
- `src/mcp_coder/__init__.py` (modify) - Export new interfaces
- `pyproject.toml` (modify) - Add new dependency
- Tests for all new modules

## Success Criteria
1. Both CLI and API methods work with identical functionality
2. New Python SDK implementation provides same capabilities as CLI
3. Clean separation of concerns between CLI and API implementations
4. Easy to extend for future LLM providers
5. SDK uses existing CLI subscription authentication automatically
6. Comprehensive testing validates both implementations work equivalently
