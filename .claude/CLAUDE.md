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