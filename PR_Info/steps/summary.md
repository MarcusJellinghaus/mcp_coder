# Prompt Manager Implementation Summary

## Overview
Implement a simplified prompt manager to centralize prompts in markdown files instead of hardcoding them throughout the codebase.

## Core Functionality
- **Two main functions**: `get_prompt()` and `validate_prompt_markdown()`
- **Simple markdown format**: Headers (`# Header`) followed by code blocks with triple backticks
- **Flexible input**: Read from file path OR memory stream (for testing)

## Technical Approach
- Single file implementation: `src/mcp_coder/prompt_manager.py`
- Functions accept file path OR string content (memory stream)
- Package data configuration for real prompt files
- Test data embedded in test file (no external test files needed)

## Key Design Decisions
- **KISS principle**: Minimal complexity, just find header → extract code block → return text
- **TDD approach**: Write simple test first using memory streams
- **Simple regex parsing**: No complex markdown parsers needed
- **Flexible input**: File path string OR markdown content string

## Success Criteria
1. `get_prompt(markdown_content, "Header")` returns prompt text from code block
2. `validate_prompt_markdown(markdown_content)` validates basic structure
3. Works with both file paths and memory streams
4. Simple test passes with embedded test data

## File Structure Created
```
src/mcp_coder/
└── prompt_manager.py          # Core implementation with setup instructions
tests/
└── test_prompt_manager.py    # Simple test with embedded test data
```
