# Issue #228: Security - Redact Secrets from Logs

## Problem Statement

**Priority: CRITICAL (security vulnerability)**

1. **Security**: `@log_function_call` decorator logs sensitive values (tokens, API keys) in plaintext
2. **Verbosity**: Each `get_config_value()` call triggers nested decorator logs (6+ lines per value)
3. **Wrong logger**: Logs show `mcp_coder.utils.log_utils` instead of the decorated function's module
4. **LLM logging**: `log_llm_request()` logs `env_vars` and `prompt` content which may contain secrets

## Design Approach (KISS)

Instead of creating a new batch config function and refactoring all callers, we use a simpler approach:

1. **Auto-redaction in decorator**: Add automatic redaction for keys matching sensitive patterns
2. **Remove unnecessary decorators**: Remove `@log_function_call` from low-level config helpers
3. **Fix logger name**: Use the decorated function's module logger, not `log_utils`

This achieves the same goals with fewer changes and no caller refactoring.

## Architecture Changes

### Before
```
@log_function_call  ─► logs to mcp_coder.utils.log_utils
def load_config():   ─► returns {'github': {'token': 'ghp_xxx...'}}  # EXPOSED!

@log_function_call  ─► logs to mcp_coder.utils.log_utils  
def get_config_value():  ─► calls load_config() ─► 6+ log lines per call
```

### After
```
@log_function_call  ─► logs to mcp_coder.utils.user_config (correct module)
def load_config():   ─► returns {'github': {'token': '***'}}  # REDACTED

def get_config_value():  ─► NO decorator, minimal logging
```

## Files to Modify

| File | Change |
|------|--------|
| `src/mcp_coder/utils/log_utils.py` | Add redaction + fix logger name |
| `src/mcp_coder/utils/user_config.py` | Remove decorators from helpers |
| `src/mcp_coder/llm/providers/claude/logging_utils.py` | Remove env_vars/prompt logging |
| `tests/utils/test_log_utils.py` | Add redaction tests |

## Acceptance Criteria

- [x] Tokens and secrets NEVER appear in any log output
- [x] Redacted values display as `***`
- [x] Config reading produces minimal log entries
- [x] Logger name reflects the decorated function's module
- [ ] ~~All callers refactored to use `get_config_values()`~~ (not needed - simpler approach)
- [x] Tests verify redaction works correctly
- [x] All existing tests pass

## Implementation Steps

1. **Step 1**: Enhance `@log_function_call` decorator with auto-redaction and correct logger
2. **Step 2**: Remove decorators from config helpers + fix LLM logging
3. **Step 3**: Add tests for redaction functionality
