# Step 2: Implement Help Command

## Objective
Create a comprehensive help command that displays usage information for all CLI commands.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary and Step 1 completion, implement Step 2: Create the help command.

Requirements:
- Implement help command in src/mcp_coder/cli/commands/help.py
- Display comprehensive usage information for all commands
- Integrate with main.py argument parser
- Follow existing mcp-coder code patterns and error handling
- Keep it simple following KISS principle

The help should show usage for: help, commit auto, commit clipboard commands.
```

## WHERE (File Structure)
```
src/mcp_coder/cli/commands/
├── __init__.py (updated)
└── help.py (new)

src/mcp_coder/cli/main.py (updated)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/cli/commands/help.py`
```python
def execute_help(args: argparse.Namespace) -> int:
    """Execute help command. Returns exit code."""

def get_help_text() -> str:
    """Get comprehensive help text for all commands."""

def get_usage_examples() -> str:
    """Get usage examples for common workflows."""
```

### `src/mcp_coder/cli/commands/__init__.py`
```python
"""CLI command modules."""
from .help import execute_help

__all__ = ["execute_help"]
```

## HOW (Integration Points)

### Updated main.py
```python
# Add subparser for help command
help_parser = subparsers.add_parser('help', help='Show help information')

# Command routing
if args.command == 'help':
    return execute_help(args)
```

### Import Pattern
```python
import argparse
from typing import Optional
```

## ALGORITHM (Core Logic)
```
1. Check if specific command help requested (future enhancement)
2. Generate comprehensive help text with command descriptions
3. Include usage examples and common workflows
4. Display formatted help text to stdout
5. Return success exit code (0)
```

## DATA (Return Values)

### execute_help() → int
- `0`: Always success (help display successful)

### get_help_text() → str
- Multi-line string with command descriptions
- Formatted for terminal display

### get_usage_examples() → str
- Examples showing common usage patterns
- Real-world workflow examples

## Tests Required

### `tests/cli/commands/test_help.py`
```python
def test_execute_help_returns_success():
    """Test help command returns exit code 0."""

def test_get_help_text_contains_all_commands():
    """Test help text includes all available commands."""

def test_get_usage_examples_has_examples():
    """Test usage examples are provided."""

def test_help_text_formatting():
    """Test help text is properly formatted."""
```

### `tests/cli/test_main.py` (additions)
```python
def test_main_help_command():
    """Test 'mcp-coder help' command works."""
```

## Expected Help Output
```
MCP Coder - AI-powered software development automation toolkit

USAGE:
    mcp-coder <command> [options]

COMMANDS:
    help                    Show this help information
    commit auto             Auto-generate commit message using LLM analysis
    commit clipboard        Use commit message from clipboard

EXAMPLES:
    mcp-coder help                    # Show this help
    mcp-coder commit auto             # Analyze changes and auto-commit
    mcp-coder commit clipboard        # Commit with clipboard message

For more information, visit: https://github.com/MarcusJellinghaus/mcp_coder
```

## Acceptance Criteria
1. ✅ Help command implemented in separate module
2. ✅ Comprehensive help text with all commands
3. ✅ Usage examples included
4. ✅ Integration with main.py parser
5. ✅ `mcp-coder help` displays help and exits with 0
6. ✅ All tests pass
7. ✅ Help text is well-formatted and informative
