# Refactor for Extensible LLM Interface

## Overview
Refactor the current `ask_claude()` function to create an extensible architecture that supports multiple LLM clients. Currently, the codebase only supports Claude Code CLI. The goal is to add a Python SDK implementation while maintaining backward compatibility.

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
- **Backward Compatibility**: Existing `ask_claude()` function remains unchanged
- **KISS Principle**: Minimal complexity, maximum maintainability
- **Essential Testing**: Focus on core functionality, skip performance benchmarking

## Files to be Created/Modified
- `src/mcp_coder/llm_interface.py` (new) - High-level interface
- `src/mcp_coder/claude_code_interface.py` (new) - Claude-specific routing
- `src/mcp_coder/claude_code_cli.py` (new) - Move existing CLI implementation
- `src/mcp_coder/claude_code_api.py` (new) - Python SDK implementation
- `src/mcp_coder/claude_client.py` (modify) - Keep as compatibility layer
- `src/mcp_coder/__init__.py` (modify) - Update exports
- `pyproject.toml` (modify) - Add new dependency
- Tests for all new modules

## Success Criteria
1. All existing tests pass without modification
2. New Python SDK implementation works with basic functionality
3. Clean separation of concerns between CLI and API implementations
4. Easy to extend for future LLM providers
5. SDK uses existing CLI subscription authentication automatically
