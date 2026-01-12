# Issue #275: Remove Direct Structlog Imports and Enhance Console Logging

## Summary

This implementation removes direct `structlog` imports from two modules that violate the library isolation rule. Only `log_utils.py` should know about structlog - all other modules must use standard Python `logging` with `extra={}` for structured data.

## Architectural / Design Changes

### Before
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   data_files.py │     │    client.py    │     │   log_utils.py  │
│                 │     │                 │     │                 │
│ import structlog│     │ import structlog│     │ import structlog│
│ (VIOLATION)     │     │ (VIOLATION)     │     │ (CORRECT)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### After
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   data_files.py │     │    client.py    │     │   log_utils.py  │
│                 │     │                 │     │                 │
│ import logging  │     │ import logging  │     │ import structlog│
│ extra={...}     │     │ extra={...}     │     │ (ONLY HERE)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Key Design Decisions

1. **Console Formatter Enhancement**: Simple `format()` override that appends `extra` fields as `[key=value]` pairs. No complex class hierarchy.

2. **Minimal Log Merging**: Only merge consecutive log calls where obviously cleaner. Preserve debuggability over brevity.

3. **Standard Library Pattern**: All modules use `logging.getLogger(__name__)` with `extra={}` dict for structured data.

4. **Test Migration**: Replace `structlog.testing.LogCapture` with pytest's built-in `caplog` fixture.

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/log_utils.py` | Modify | Add `ExtraFieldsFormatter` class, update console handler, add docstring example |
| `src/mcp_coder/utils/jenkins_operations/client.py` | Modify | Replace structlog with standard logging |
| `src/mcp_coder/utils/data_files.py` | Modify | Replace structlog with standard logging (~45 calls) |
| `tests/utils/test_data_files.py` | Modify | Replace structlog LogCapture with pytest caplog |

## Implementation Steps Overview

| Step | Description | TDD |
|------|-------------|-----|
| 1 | Update console formatter in `log_utils.py` + module docstring | Yes |
| 2 | Refactor `jenkins_operations/client.py` | No (no logging tests exist) |
| 3 | Refactor `data_files.py` | No (tests updated in step 4) |
| 4 | Update tests in `test_data_files.py` | N/A (test migration) |
| 5 | Finalization: `.importlinter` cleanup + verification | No |

## Success Criteria

1. No `import structlog` in `data_files.py` or `client.py`
2. All existing tests pass
3. `extra` fields visible in console output
4. Logging behavior unchanged for file output (JSON format)

## Usage Pattern After Implementation

```python
import logging

logger = logging.getLogger(__name__)

def my_function(user_id: str, action: str) -> None:
    logger.info("Action performed", extra={"user_id": user_id, "action": action})
    # Console output: 2024-01-15 10:30:00 - module - INFO - Action performed {"user_id": "123", "action": "login"}
```

## Decisions

See [Decisions.md](Decisions.md) for discussion outcomes:
1. Extra fields format: JSON object with `json.dumps()`
2. `log_function_call` decorator: Leave as-is (allowed to use structlog)
3. Numbering bug: Fix `/4` → `/5` during refactor
4. Log merging policy: Merge only identical messages on adjacent lines
5. Empty extra dict: Show nothing (no suffix)
6. Non-JSON-serializable values: Auto-convert with `str()` via `default=str`
