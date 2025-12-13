# Issue #194: Config File Errors - Show Name of Config File

## Overview

Improve TOML config parse error messages to show the file path and error context in Python's `SyntaxError` style format.

## Problem

When `config.toml` has a syntax error, users see:
```
Error: Illegal character '\n' (at line 25, column 49)
```

Users don't know which file has the error or what the content looks like.

## Solution

Show errors in Python's standard `SyntaxError` style:
```
  File "C:\Users\me\.mcp_coder\config.toml", line 25
    executor_os = "linux
                       ^
TOML parse error: Illegal character '\n'
```

## Architectural Changes

### Design Approach: KISS

- **No custom exception class** - reuse `ValueError` with formatted message
- **Single helper function** for error formatting
- **Single `load_config()` function** as the canonical config loader
- **Behavior change**: Parse errors now raise instead of returning `None`

### Component Changes

```
src/mcp_coder/utils/user_config.py
├── _format_toml_error()     [NEW] - Format error with file path, line, pointer
├── load_config()            [NEW] - Load full config dict, raise on parse error
└── get_config_value()       [MODIFIED] - Use load_config() internally

src/mcp_coder/cli/commands/coordinator.py
└── execute_coordinator_run() [MODIFIED] - Use load_config() instead of tomllib
```

## Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/mcp_coder/utils/user_config.py` | MODIFY | Add `_format_toml_error()`, `load_config()`, refactor `get_config_value()` |
| `src/mcp_coder/cli/commands/coordinator.py` | MODIFY | Replace direct `tomllib.load()` with `load_config()` |
| `tests/utils/test_user_config.py` | MODIFY | Add tests for error formatting and `load_config()` |

## Implementation Steps

| Step | Description | TDD |
|------|-------------|-----|
| 1 | Add `_format_toml_error()` helper and tests | Yes |
| 2 | Add `load_config()` function and tests | Yes |
| 3 | Refactor `get_config_value()` and update tests | Yes |
| 4 | Update `coordinator.py` to use `load_config()` | No (integration) |

## Acceptance Criteria

- [ ] Error output includes file path
- [ ] Error output includes the error line content
- [ ] Error output includes `^` pointer at error position
- [ ] Error output follows Python `SyntaxError` format
- [ ] `get_config_value()` raises on parse errors (behavior change)
- [ ] `coordinator.py` uses `load_config()` instead of direct `tomllib.load()`
- [ ] All existing tests pass
- [ ] New tests cover error formatting
