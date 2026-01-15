# Issue #228: Security - Redact Secrets from Logs + Refactor Config Reading

## Summary

This implementation addresses a **critical security vulnerability** where sensitive values (tokens, API keys) are logged in plaintext at DEBUG level. It also improves logging accuracy and config reading efficiency.

## Problems Being Solved

1. **Security**: `@log_function_call` decorator logs secrets in plaintext
2. **Wrong logger name**: Logs show `mcp_coder.utils.log_utils` instead of decorated function's module
3. **Verbosity**: Each `get_config_value()` call produces 6+ log lines from nested decorated calls
4. **Inefficiency**: Config file read from disk on every `get_config_value()` call

## Architectural / Design Changes

### 1. Decorator Enhancement (`log_function_call`)

**Before:**
```python
@log_function_call
def load_config() -> dict[str, Any]:
    ...
```

**After:**
```python
@log_function_call(sensitive_fields=["token", "api_token"])
def load_config() -> dict[str, Any]:
    ...
```

**Design decisions:**
- Decorator accepts optional `sensitive_fields` parameter (keyword-only)
- Redaction is performed on a **copy** of data before logging (original values unchanged)
- Logger uses `func.__module__` instead of module-level logger
- Simple flat redaction for params; recursive redaction for nested dicts in return values

### 2. Config API Refactoring

**Before:** Individual calls, each reading disk
```python
token = get_config_value("github", "token")
url = get_config_value("jenkins", "server_url")
```

**After:** Single batch call, one disk read
```python
values = get_config_values([
    ("github", "token"),
    ("jenkins", "server_url"),
])
token = values[("github", "token")]
url = values[("jenkins", "server_url")]
```

**Design decisions:**
- Environment variable priority preserved per-key
- Single disk read per batch
- Returns `dict[tuple[str, str], str | None]` for type safety

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/mcp_coder/utils/log_utils.py` | Modify | Add `sensitive_fields` param, fix logger name, add `_redact_for_logging()` |
| `src/mcp_coder/utils/user_config.py` | Modify | Replace `get_config_value()` with `get_config_values()` |
| `src/mcp_coder/utils/github_operations/base_manager.py` | Modify | Use batch config function |
| `src/mcp_coder/utils/jenkins_operations/client.py` | Modify | Use batch config function |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Modify | Use batch config function |
| `tests/conftest.py` | Modify | Use batch config function |
| `tests/utils/test_log_utils.py` | Modify | Add redaction tests, logger name tests |
| `tests/utils/test_user_config.py` | Modify | Update for new batch API |
| `tests/utils/test_user_config_integration.py` | Modify | Update for new batch API |
| `tests/utils/jenkins_operations/test_integration.py` | Modify | Use batch config function |

## Files NOT Being Modified (Out of Scope)

- `llm/providers/claude/logging_utils.py` - Environment variable filtering is separate issue
- Exception message redaction - separate issue
- Prompt content redaction - separate issue

## Acceptance Criteria

- [ ] `@log_function_call` accepts `sensitive_fields` parameter
- [ ] Sensitive parameter values display as `***` in logs
- [ ] Sensitive return value keys display as `***` in logs  
- [ ] Logger name reflects the decorated function's module
- [ ] `get_config_value()` removed, replaced with `get_config_values()`
- [ ] All 8 callers refactored to use batch function
- [ ] Config reading produces minimal log entries (one per batch call)
- [ ] Tests verify redaction works correctly
- [ ] All existing tests pass

## Implementation Order

1. **Step 1**: Add redaction to `@log_function_call` decorator + tests
2. **Step 2**: Fix logger name in decorator + tests
3. **Step 3**: Add `get_config_values()` batch function + tests
4. **Step 4**: Refactor callers to use batch function
5. **Step 5**: Final cleanup and verification
