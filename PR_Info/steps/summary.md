# Prompt Command Implementation Summary

## Overview
Add a new `prompt` command to the MCP Coder CLI that allows users to execute arbitrary prompts against Claude API with comprehensive debug output, multiple verbosity levels, and session storage/continuation capabilities.

## Goal
Enable users to run:
```bash
mcp-coder prompt "What is the capital of France?"
mcp-coder prompt "Explain async/await" --verbose
mcp-coder prompt "Debug this error" --raw --store-response
mcp-coder prompt "Follow up question" --continue-from response_20250918_143022.json
```

## Technical Approach
- **Use detailed API**: Leverage `ask_claude_code_api_detailed_sync()` function for rich debug info
- **Follow established patterns**: Mirror existing command structure (help, verify, commit)
- **Essential testing**: 5 key tests covering core functionality without over-testing
- **KISS principle**: Minimal complexity, maximum debugging transparency
- **TDD approach**: 12 small implementation steps with test-first development

## Key Components
1. **Command Module**: `src/mcp_coder/cli/commands/prompt.py`
2. **CLI Integration**: Update parser and routing in `main.py`
3. **Help System**: Update help text and examples
4. **Tests**: Essential unit tests with mocked Claude CLI calls
5. **Verbosity System**: Three output levels (just-text, verbose, raw)
6. **Storage System**: Session storage in `.mcp-coder/responses/` directory
7. **Continuation System**: Load previous sessions for follow-up questions

## Implementation Strategy
- 12 self-contained TDD steps
- Each step builds incrementally with test-first approach
- Clear separation of concerns
- Minimal cross-file dependencies
- Small, focused functions following KISS principles

## Function Structure
```python
# src/mcp_coder/cli/commands/prompt.py
execute_prompt(args) -> int                    # Main entry point
_format_just_text(response_data) -> str        # Default: Claude response + tool summary
_format_verbose(response_data) -> str          # Full debug without raw JSON
_format_raw(response_data) -> str              # Everything including JSON structures
_store_response(response_data, path) -> str    # Handle session storage
_load_previous_chat(file_path) -> dict         # Load for continuation
```

## Verbosity Levels

### --just-text (default)
- Claude's response text
- Tool interactions summary (e.g., "Used 3 tools: file_read, web_search, calculator")

### --verbose  
- Claude's response text
- Detailed tool interactions with parameters
- Performance metrics (duration, cost, tokens)
- Session information (model, working directory)

### --raw
- Everything from --verbose
- Complete raw JSON API response structures
- Full MCP server status and available tools
- Raw message content for maximum debugging

## Storage & Continuation Features
- **--store-response**: Save complete session to `.mcp-coder/responses/response_TIMESTAMP.json`
- **--continue-from**: Load previous session for follow-up questions
- **Session Structure**: Include prompt, context, responses, metadata for full conversation continuity

## Test Strategy
- **5 Essential Tests**: Core functionality without over-testing
- **TDD Approach**: Test first, then implement
- **Mocking Strategy**: Mock `ask_claude_code_api_detailed_sync()` responses
- **Focus Areas**: Success cases, error handling, verbosity levels, storage, continuation

## Success Criteria
- All verbosity levels work correctly
- Session storage and continuation function properly
- MCP tool interactions visible at appropriate detail levels
- Performance metrics displayed when requested
- Clean, maintainable code following KISS principles
