# Step 5: Update Documentation in log_utils.py

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 5.
Update the log_utils.py module docstring with a usage example showing the correct logging pattern.
```

## WHERE
- **File**: `src/mcp_coder/utils/log_utils.py`

## WHAT

### Current Docstring (line 1)
```python
"""Logging utilities for the MCP server."""
```

### New Docstring
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
When extra fields are provided, they appear as [key=value] pairs:

    2024-01-15 10:30:00 - mymodule - INFO - Action performed [user_id=123] [action=login]

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

## HOW

Replace the single-line docstring at the top of `log_utils.py` with the expanded docstring above.

## ALGORITHM

N/A - Documentation only.

## DATA

N/A - Documentation only.

## IMPLEMENTATION CHECKLIST

- [ ] Replace module docstring in `log_utils.py`
- [ ] Verify docstring renders correctly: `python -c "import mcp_coder.utils.log_utils; help(mcp_coder.utils.log_utils)"`
- [ ] Run full test suite to ensure nothing broken: `pytest tests/ -v`

## FINAL VERIFICATION

After all steps complete, verify:

```bash
# 1. No structlog imports outside log_utils.py
grep -r "import structlog" src/mcp_coder/ --include="*.py" | grep -v log_utils.py
# Should return nothing

# 2. All tests pass
pytest tests/ -v

# 3. Pylint passes
pylint src/mcp_coder/utils/data_files.py src/mcp_coder/utils/jenkins_operations/client.py

# 4. Mypy passes  
mypy src/mcp_coder/utils/data_files.py src/mcp_coder/utils/jenkins_operations/client.py
```
