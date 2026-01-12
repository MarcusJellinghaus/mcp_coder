# Step 5: Finalization and Verification

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 5.
Remove the structlog exceptions from .importlinter and run final verification.
```

## WHERE
- **File**: `.importlinter`

## WHAT

### Remove .importlinter Exceptions

Remove these lines from the `structlog_isolation` contract:
```ini
# TODO: Remove after fixing issue #275
mcp_coder.utils.data_files -> structlog
mcp_coder.utils.jenkins_operations.client -> structlog
```

The contract should only have:
```ini
ignore_imports =
    mcp_coder.utils.log_utils -> structlog
```

## HOW

Edit `.importlinter` to remove the two exception lines for `data_files` and `client`.

## ALGORITHM

N/A - Configuration cleanup only.

## DATA

N/A - Configuration cleanup only.

## IMPLEMENTATION CHECKLIST

- [ ] Remove the two structlog exception lines from `.importlinter`
- [ ] Run import linter: `./tools/lint_imports.sh`
- [ ] Verify no structlog imports outside log_utils.py: `grep -r "import structlog" src/mcp_coder/ --include="*.py" | grep -v log_utils.py`
- [ ] Run full test suite: `mcp__code-checker__run_pytest_check`
- [ ] Run pylint: `mcp__code-checker__run_pylint_check`
- [ ] Run mypy: `mcp__code-checker__run_mypy_check`

## DOCSTRING REFERENCE

Note: The module docstring update is now part of Step 1. The new docstring should be:

```python
"""Logging utilities for the MCP server.

This module is the ONLY place that should import structlog directly.
All other modules should use standard Python logging with extra fields.

Usage Pattern
-------------
In any module that needs logging:

    import logging
    
    logger = logging.getLogger(__name__)
    
    def my_function(user_id: str, action: str) -> None:
        # Simple message
        logger.info("Processing request")
        
        # Message with structured data
        logger.info(
            "Action performed",
            extra={"user_id": user_id, "action": action}
        )
        
        # Debug with multiple fields
        logger.debug(
            "Operation details",
            extra={
                "operation": "fetch",
                "target": "database",
                "timeout_ms": 5000,
            }
        )

Console Output Format
---------------------
When extra fields are provided, they appear as a JSON object:

    2024-01-15 10:30:00 - mymodule - INFO - Action performed {"user_id": "123", "action": "login"}

File Output Format
------------------
File logging uses JSON format with all extra fields included as top-level keys.

Note
----
Do NOT import structlog in other modules. This maintains library isolation
and allows the logging implementation to be changed without affecting the
rest of the codebase.
"""
```
