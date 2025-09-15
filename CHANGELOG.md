# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Extensible LLM Interface**: New `ask_llm()` function as main entry point for LLM interactions
  - Supports multiple providers (currently Claude)
  - Supports multiple implementation methods (CLI and API)
  - Designed for easy extension to additional LLM providers

- **Claude Code Python SDK Support**: New API method using `claude-code-sdk`
  - Added `ask_claude_code()` function with method routing
  - Support for both CLI (`method="cli"`) and API (`method="api"`) methods
  - Automatic authentication using existing CLI subscription
  - Enhanced error handling and response parsing

- **Modular Architecture**: Clean separation of concerns
  - `llm_interface.py`: High-level provider-agnostic interface
  - `claude_code_interface.py`: Claude-specific routing logic
  - `claude_code_cli.py`: Extracted CLI implementation
  - `claude_code_api.py`: New Python SDK implementation

- **Comprehensive Testing**: Full test coverage for new features
  - Integration tests validating both CLI and API methods
  - Unit tests for all new modules
  - Parameterized tests ensuring method equivalence

- **Documentation**: Complete API reference and usage examples
  - Updated README.md with new interface examples
  - Comprehensive docstrings for all public functions
  - Migration guide for existing users

### Changed

- **Refactored CLI Implementation**: Moved existing Claude Code CLI logic to dedicated module
  - `claude_code_cli.py`: Contains extracted CLI implementation
  - `claude_client.py`: Now serves as backward-compatible wrapper
  - Maintains full backward compatibility with existing code

- **Enhanced Module Exports**: Updated `__init__.py` to export new interfaces
  - Added `ask_llm` to public API
  - Maintained all existing exports for backward compatibility

### Dependencies

- **Added**: `claude-code-sdk` for Python SDK support
- **Development**: Enhanced testing and code quality tools

### Technical Details

#### Architecture Changes
```
Before:
ask_claude() -> _find_claude_executable() -> execute_command() -> Claude Code CLI

After:  
ask_llm() -> ask_claude_code() -> ask_claude_code_cli() (existing)
                               -> ask_claude_code_api() (new)
```

#### Key Design Principles
- **Extensibility**: Easy to add new LLM clients in the future
- **Clean Architecture**: Clear separation between CLI and API implementations
- **KISS Principle**: Minimal complexity, maximum maintainability
- **Backward Compatibility**: All existing code continues to work unchanged

#### Implementation Methods
- **CLI Method**: Uses Claude Code CLI executable via subprocess
- **API Method**: Uses Claude Code Python SDK with automatic CLI authentication
- Both methods provide identical functionality and responses

### Migration Guide

#### For New Projects
```python
# Use the new extensible interface
from mcp_coder import ask_llm

response = ask_llm("Your question", provider="claude", method="api")
```

#### For Existing Projects
```python
# Existing code continues to work unchanged
from mcp_coder import ask_claude

response = ask_claude("Your question")  # Still works!
```

#### Upgrading to New Interface
```python
# Old way
from mcp_coder import ask_claude
response = ask_claude("Your question")

# New way (recommended)
from mcp_coder import ask_llm
response = ask_llm("Your question", provider="claude", method="api")
```

## Version History

### [0.1.0] - Initial Release
- Basic Claude Code CLI integration
- Subprocess-based command execution
- Core ask_claude() functionality
