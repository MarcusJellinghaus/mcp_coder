# Prompt Manager Implementation Summary

## Overview
Implement a simplified prompt manager to centralize prompts in markdown files instead of hardcoding them throughout the codebase.

## Core Functionality
- **Main functions**: `get_prompt()`, `validate_prompt_markdown()`, and `validate_prompt_directory()`
- **Simple markdown format**: Headers (any level: `#`, `##`, `###`, `####`) followed by code blocks with triple backticks
- **Flexible input**: File path, directory/wildcard, OR string content (auto-detected)
- **Cross-file support**: Virtual concatenation for multi-file prompt directories
- **Comprehensive validation**: Detailed error reporting with file names and line numbers

## Technical Approach
- Single file implementation: `src/mcp_coder/prompt_manager.py`
- Functions accept file path, directory/wildcard, OR string content (auto-detected)
- Comprehensive prompt file: `src/mcp_coder/prompts/prompts.md`
- Virtual file concatenation for cross-file duplicate detection
- Package data configuration for prompt files
- Unit tests only with embedded test data (no separate integration tests)

## Key Design Decisions
- **KISS principle**: Minimal complexity, fail completely on errors (no partial results)
- **TDD approach**: Comprehensive unit tests with both file paths and string content
- **Simple regex parsing**: No complex markdown parsers, expect well-formed input
- **Flexible input**: Auto-detect file path vs string content using simple heuristics
- **Error handling**: Clear `ValueError` messages with duplicate locations across files
- **Wildcard support**: `prompts/*`, `prompts/*.md`, or directory auto-expansion

## Success Criteria
1. `get_prompt(source, "Header")` works with file paths, directories, wildcards, and string content
2. `validate_prompt_markdown(source)` returns detailed validation results
3. `validate_prompt_directory(directory)` checks cross-file duplicates
4. Duplicate headers raise clear `ValueError` with file locations and line numbers
5. Any header level (`#`, `##`, `###`, `####`) matches the same prompt name
6. Comprehensive unit tests pass with both file and string content scenarios

## File Structure Created
```
src/mcp_coder/
├── prompt_manager.py          # Core implementation with three main functions
└── prompts/
    └── prompts.md            # Comprehensive documentation + prompts file
tests/
└── test_prompt_manager.py    # Unit tests with file and string content scenarios
```
