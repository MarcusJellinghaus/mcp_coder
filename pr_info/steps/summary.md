# Refactor execute_prompt: Add Explicit Parameters and File Save Features

## Overview
This PR refactors the `execute_prompt` function from using `argparse.Namespace` to explicit parameters, improving testability and enabling programmatic usage. Additionally, it adds two new file save features for conversation persistence.

## Architectural Changes

### 1. Function Signature Refactoring
**Current Architecture:**
```python
def execute_prompt(args: argparse.Namespace) -> int:
    # Tightly coupled to CLI argument parsing
    # Hard to test and use programmatically
```

**New Architecture:**
```python
def execute_prompt(args: argparse.Namespace) -> int:
    """CLI wrapper - converts argparse.Namespace to explicit parameters"""
    return prompt_claude(
        prompt=args.prompt,
        verbosity=getattr(args, "verbosity", "just-text"),
        # ... other parameters
    )

def prompt_claude(
    prompt: str,
    verbosity: str = "just-text",
    timeout: int = 30,
    store_response: bool = False,
    continue_from: Optional[str] = None,
    continue_latest: bool = False,
    save_conversation_md: Optional[str] = None,
    save_conversation_full_json: Optional[str] = None
) -> int:
    """Core function with explicit parameters - easy to test and use"""
```

### 2. Separation of Concerns
- **CLI Layer**: `execute_prompt()` handles argparse.Namespace conversion
- **Core Logic**: `prompt_claude()` contains business logic with explicit parameters
- **File Operations**: New save functions handle conversation persistence

### 3. New File Save Features
- **Markdown Export**: Human-readable conversation format
- **Full JSON Export**: Complete conversation data with metadata
- **Flexible Paths**: Users specify full path+filename for both formats

## Design Principles Applied

### KISS Principle
- **Minimal changes**: Existing CLI functionality unchanged
- **Simple separation**: Clear distinction between CLI wrapper and core logic
- **Straightforward parameters**: Full path+filename (no complex directory logic)

### Dependency Inversion
- **Before**: Core logic depends on argparse.Namespace
- **After**: Core logic depends on primitive types (str, int, bool)

### Single Responsibility
- `execute_prompt()`: CLI argument handling only
- `prompt_claude()`: Core Claude interaction logic
- `_save_conversation_*()`: File persistence operations

## Files Modified/Created

### Modified Files
```
src/mcp_coder/cli/commands/prompt.py
├── execute_prompt()           # Converted to CLI wrapper
├── prompt_claude()            # NEW: Core function with explicit parameters
├── _save_conversation_markdown()     # NEW: Save as readable markdown
└── _save_conversation_full_json()    # NEW: Save complete JSON data

tests/cli/commands/test_prompt.py
├── TestExecutePrompt         # EXISTING: Comprehensive tests (20+ methods) - UNCHANGED
├── test_prompt_claude_parameter_mapping()  # NEW: 1-2 methods for wrapper testing
└── test_save_conversation_functions()      # NEW: 2 methods for save functionality
```

### No New Files Created
All changes are contained within existing modules to maintain project structure.

## Implementation Benefits

### 1. **Improved Testability**
- Core function can be tested without creating argparse.Namespace objects
- Clear function signatures enable precise unit testing
- Easier mocking and parameter verification
- **Existing comprehensive tests remain unchanged** - they will catch any regressions

### 2. **Programmatic Usage**
```python
# Before: Required argparse.Namespace
args = argparse.Namespace(prompt="test", verbosity="verbose")
execute_prompt(args)

# After: Direct function calls
prompt_claude("What is Python?", verbosity="verbose")
prompt_claude("Explain design patterns", save_conversation_md="/path/to/file.md")
```

### 3. **Enhanced Conversation Persistence**
- **Markdown files**: Easy to read, share, and review
- **JSON files**: Complete data for analysis, debugging, and future processing
- **User control**: Full path+filename specification

### 4. **Backward Compatibility**
- Existing CLI commands work unchanged
- No breaking changes to public API
- Smooth transition path for existing users

## Data Structures

### Markdown File Format
```markdown
# Conversation with Claude

**Date:** 2025-01-01 12:00:00
**Model:** claude-sonnet-4
**Session ID:** session-123

## User Prompt
What is Python?

## Claude's Response
Python is a programming language...

## Session Summary
- **Duration:** 1.50s
- **Cost:** $0.0250
- **Tokens:** 10 input, 8 output
- **Tools Used:** None

## Tool Interactions
- file_writer: {"filename": "test.py"}
```

### Full JSON File Format
```json
{
  "prompt": "What is Python?",
  "response_data": {
    "text": "Python is a programming language...",
    "session_info": {...},
    "result_info": {...},
    "raw_messages": [...]
    // Complete response_data from ask_claude_code_api_detailed_sync stored as-is
  },
  "metadata": {
    "timestamp": "2025-01-01T12:00:00Z",
    "working_directory": "/current/dir",
    "model": "claude-sonnet-4"
  }
}
```

## Migration Path

### Phase 1: Internal Refactoring (This PR)
- Split functions maintaining backward compatibility
- Add new save features
- Comprehensive test coverage

### Phase 2: Future Enhancements (Subsequent PRs)
- CLI arguments for new save parameters
- Integration with existing `--store-response` functionality
- Additional export formats if needed

This design ensures minimal disruption while providing significant architectural improvements and new functionality.
