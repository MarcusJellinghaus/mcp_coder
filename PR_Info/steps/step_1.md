# Step 1: Create CLI Directory Structure and Basic Entry Point

## Objective
Set up the basic CLI module structure and create a minimal entry point that can be installed and executed.

## LLM Prompt
```
Based on the MCP Coder CLI Implementation Summary, implement Step 1: Create the basic CLI directory structure and entry point.

Requirements:
- Create CLI module structure under src/mcp_coder/cli/
- Implement minimal main.py with argument parsing
- Update pyproject.toml to add CLI entry point
- Follow KISS principle - keep it simple
- Use existing mcp-coder infrastructure patterns

Create a basic CLI that can be installed and shows help when run with no arguments.
```

## WHERE (File Structure)
```
src/mcp_coder/cli/
├── __init__.py
├── main.py
└── commands/
    └── __init__.py

pyproject.toml (modified)
```

## WHAT (Functions & Classes)

### `src/mcp_coder/cli/__init__.py`
```python
"""MCP Coder CLI module."""
from .main import main

__all__ = ["main"]
```

### `src/mcp_coder/cli/main.py`
```python
def main() -> int:
    """Main CLI entry point. Returns exit code."""

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""

def handle_no_command(args: argparse.Namespace) -> int:
    """Handle case when no command is provided."""
```

### `src/mcp_coder/cli/commands/__init__.py`
```python
"""CLI command modules."""
# Empty for now, will be populated in later steps
```

## HOW (Integration Points)

### pyproject.toml Updates
```toml
# Uncomment and update existing entry point
[project.scripts]
mcp-coder = "mcp_coder.cli.main:main"
```

### Import Pattern
```python
import argparse
import sys
from pathlib import Path
from ..log_utils import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)
```

## ALGORITHM (Core Logic)
```
1. Initialize structured logging from Step 0
2. Parse command line arguments using argparse
3. Log CLI startup and arguments
4. If no command provided → show help and exit with code 1
5. Route to appropriate command handler (placeholder for now)
6. Handle exceptions with proper logging and return appropriate exit codes
7. Return 0 for success, 1 for user errors, 2 for system errors
```

## DATA (Return Values)

### main() → int
- `0`: Success
- `1`: User error (invalid arguments, wrong directory, etc.)
- `2`: System error (git failure, LLM failure, etc.)

### create_parser() → argparse.ArgumentParser
- Configured parser with subcommands structure
- Help text and version information

## Tests Required

### `tests/cli/test_main.py`
```python
def test_main_no_args_shows_help():
    """Test that running with no args shows help and exits with 1."""

def test_main_help_flag():
    """Test that --help flag works."""

def test_create_parser():
    """Test parser creation and basic configuration."""

def test_cli_entry_point_exists():
    """Test that CLI entry point is properly configured."""
```

## Acceptance Criteria
1. ✅ CLI directory structure created
2. ✅ Basic argument parser implemented
3. ✅ Entry point updated in pyproject.toml (uncommented and corrected)
4. ✅ Logging integration from Step 0 working
5. ✅ `mcp-coder` command shows help when run with no arguments
6. ✅ All tests pass
7. ✅ Package can be installed and CLI is available
8. ✅ Structured logging operational for CLI commands
