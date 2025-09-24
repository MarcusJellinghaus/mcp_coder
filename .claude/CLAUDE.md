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

## Access to files

Prefer these tools for access and managing files:
```
      "mcp__filesystem__get_reference_projects",
      "mcp__filesystem__list_reference_directory",
      "mcp__filesystem__read_reference_file",
      "mcp__filesystem__list_directory",
      "mcp__filesystem__read_file",
      "mcp__filesystem__save_file",
      "mcp__filesystem__append_file",
      "mcp__filesystem__delete_this_file",
      "mcp__filesystem__move_file",
      "mcp__filesystem__edit_file"
```

## Issue with MCP servers

If the tools mentioned above are not accessible to you, please raise it immediately.