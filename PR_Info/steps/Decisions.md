# Project Plan Decisions Log

## Overview
This document records the decisions made during the project plan review discussion on September 17, 2025.

## Decision Summary

### 1. Preview Mode for Auto Commit
**Decision**: Add `--preview` flag to `mcp-coder commit auto`
- **Option Chosen**: A - Add `--preview` flag that shows generated message and asks for confirmation
- **Impact**: Step 5 will include both direct commit and preview modes
- **Rationale**: Provides user control while keeping implementation simple

### 2. Error Message Enhancement
**Decision**: Keep simple, clean error messages
- **Option Chosen**: C - Keep current simple error messages
- **Impact**: No changes to planned error handling approach
- **Rationale**: KISS principle - avoid over-engineering error messages

### 3. Cross-Platform Clipboard Testing
**Decision**: Keep current plan with documentation
- **Option Chosen**: C - Assume tkinter works consistently, document compatibility
- **Impact**: Add documentation in source code and help text about cross-platform compatibility
- **Rationale**: Trust tkinter's cross-platform reliability, document any known issues

### 4. LLM Provider Strategy
**Decision**: Use existing `ask_llm()` function with API default
- **Option Chosen**: Use high-level function, change default method to "api"
- **Impact**: 
  - CLI will use `ask_llm(question, provider="claude", method="api")` by default
  - Better performance and integration than CLI method
- **Rationale**: Leverage existing extensible architecture, prefer API for better error handling

### 5. Error Recovery Strategy
**Decision**: KISS approach - leave files staged on failure
- **Option Chosen**: A - Leave files staged, show error, let user handle manually
- **Impact**: No additional unstaging logic needed
- **Rationale**: Simple, predictable behavior that follows git conventions

### 6. Configuration File Support
**Decision**: Design for future config support with KISS implementation
- **Option Chosen**: D - No config file now, but architecture ready for future addition
- **Impact**: Use simple getter functions for defaults, easy to extend later
- **Rationale**: Balance between future flexibility and current simplicity

### 7. Logging Strategy
**Decision**: Add structured logging infrastructure from mcp_server_filesystem
- **Option Chosen**: Copy proven logging pattern
- **Impact**: 
  - New Step 0: Setup logging infrastructure
  - Add dependencies: `structlog>=25.2.0`, `python-json-logger>=3.3.0`
  - Copy `log_utils.py` and tests
- **Rationale**: Professional-grade logging from the start using proven patterns

### 8. Entry Point Configuration
**Decision**: Update pyproject.toml entry point to CLI
- **Option Chosen**: A - Uncomment and update to `mcp-coder = "mcp_coder.cli.main:main"`
- **Impact**: CLI becomes the main interface for mcp-coder command
- **Rationale**: Clean, single entry point for CLI functionality

### 9. Test Strategy Enhancement
**Decision**: Stick with comprehensive unit/integration testing
- **Option Chosen**: B - No property-based testing for initial implementation
- **Impact**: Focus on planned unit and integration tests
- **Rationale**: Keep testing strategy manageable and focused

### 10. Implementation Timeline
**Decision**: Sequential step-by-step implementation
- **Option Chosen**: B/C - KISS approach, implement 0→1→2→3→4→5→6→7→8
- **Impact**: No sprint organization overhead
- **Rationale**: Natural progression for solo development, simpler planning

## Updated Step Sequence

### Step 0: Setup Logging Infrastructure (NEW)
- Copy `log_utils.py` from mcp_server_filesystem
- Add structlog dependencies
- Set up structured logging foundation

### Steps 1-8: As Originally Planned
- With modifications for preview mode in Step 5
- With API method default throughout
- With updated entry point in Step 7

## Technical Specifications

### Default LLM Configuration
```python
# CLI will use:
ask_llm(question, provider="claude", method="api")
```

### Preview Mode Implementation
```bash
mcp-coder commit auto           # Direct commit (original)
mcp-coder commit auto --preview # Show message + confirmation (new)
```

### Logging Dependencies
```toml
dependencies = [
    # ... existing dependencies ...
    "structlog>=25.2.0",
    "python-json-logger>=3.3.0",
]
```

### Entry Point Update
```toml
[project.scripts]
mcp-coder = "mcp_coder.cli.main:main"
```

## Implementation Notes

### Cross-Platform Documentation
- Add comments in clipboard utilities about tkinter compatibility
- Document any known platform-specific issues in help text
- Trust tkinter's cross-platform reliability

### Configuration Architecture
- Use getter functions for defaults to enable easy config integration later
- Keep current implementation simple with hardcoded values
- Structure code to accommodate config files in future versions

### Error Recovery Philosophy
- Follow git's natural behavior patterns
- Provide clear error messages without automatic recovery
- Let users make decisions about next steps

## Review Date
September 17, 2025

## Participants
- Project Owner
- Claude (AI Assistant)

## Status
✅ All decisions finalized and ready for implementation
