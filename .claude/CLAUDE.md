--- This file is used by Claude Code - similar to a system prompt. ---

## Code Quality Requirements

**IMPORTANT**: After making any code changes, always run all three code quality checks:

```
mcp__checker__run_pylint_check
mcp__checker__run_pytest_check
mcp__checker__run_mypy_check
```

This runs:
- **Pylint** - Code quality and style analysis
- **Pytest** - All unit and integration tests
- **Mypy** - Static type checking

All checks must pass before considering the task complete. If any issues are found, fix them immediately.

### Markers for pytest

Please check all pytest markers in `pyproject.toml` and run each of them separately, and those without markers without the others.

## Tool Preference - MCP Servers First

**ALWAYS prefer MCP server tools over built-in tools when available.**

### File Operations - Use MCP Filesystem Tools
For all file operations, use these MCP tools instead of built-in Read/Write/Edit tools:
```
      "mcp__filesystem__read_file"           - instead of Read
      "mcp__filesystem__save_file"           - instead of Write
      "mcp__filesystem__edit_file"           - instead of Edit/MultiEdit
      "mcp__filesystem__delete_this_file"    - instead of Bash rm commands
      "mcp__filesystem__move_file"           - instead of Bash mv commands
      "mcp__filesystem__list_directory"      - instead of Bash ls commands
      "mcp__filesystem__append_file"         - for appending content
```

### Code Quality - Use MCP Code Checker Tools
For all code quality checks, use these MCP tools instead of Bash commands:
```
      "mcp__code-checker__run_pylint_check"  - instead of "pylint src/"
      "mcp__code-checker__run_pytest_check"  - instead of "pytest tests/"
      "mcp__code-checker__run_mypy_check"    - instead of "mypy src/"
      "mcp__code-checker__run_all_checks"    - for comprehensive checking
```

### Reference Projects
Use these for accessing reference implementations:
```
      "mcp__filesystem__get_reference_projects"
      "mcp__filesystem__list_reference_directory"
      "mcp__filesystem__read_reference_file"
```

## Issue with MCP servers

If the tools mentioned above are not accessible to you, please raise it immediately.