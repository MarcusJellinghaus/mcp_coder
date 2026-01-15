# Step 1: Enhance `@log_function_call` Decorator

## LLM Prompt
```
Implement Step 1 of Issue #228 (see pr_info/steps/summary.md).
Enhance the @log_function_call decorator in log_utils.py with:
1. Automatic redaction of sensitive values
2. Use decorated function's module logger instead of log_utils logger
Follow TDD: write tests first, then implement.
```

## Overview

Enhance the `@log_function_call` decorator to:
1. Automatically redact sensitive keys in parameters and return values
2. Use the decorated function's module as the logger name (not `log_utils`)

---

## WHERE

**File to modify**: `src/mcp_coder/utils/log_utils.py`

---

## WHAT

### New Constants

```python
# Patterns that indicate sensitive data - keys containing these are redacted
SENSITIVE_KEY_PATTERNS: frozenset[str] = frozenset({
    "token",
    "api_token", 
    "password",
    "secret",
    "api_key",
    "credential",
})

REDACTED_VALUE: str = "***"
```

### New Helper Function

```python
def _redact_sensitive_data(data: Any, sensitive_patterns: frozenset[str]) -> Any:
    """Recursively redact sensitive keys in dicts.
    
    Args:
        data: Data to redact (dict, list, or scalar)
        sensitive_patterns: Key patterns to redact
        
    Returns:
        Data with sensitive values replaced by '***'
    """
```

### Modified Function

```python
def log_function_call(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to log function calls with parameters, timing, and results.
    
    Changes:
    - Uses decorated function's module logger (not log_utils)
    - Automatically redacts sensitive keys in params and results
    """
```

---

## HOW

### Integration Points

1. **Logger selection**: Replace `stdlogger` with `logging.getLogger(func.__module__)`
2. **Parameter redaction**: Call `_redact_sensitive_data()` on `serializable_params` before logging
3. **Result redaction**: Call `_redact_sensitive_data()` on `result_for_log` before logging

---

## ALGORITHM

### `_redact_sensitive_data` (5 lines pseudocode)

```
function redact_sensitive_data(data, patterns):
    if data is dict:
        for each key, value in data:
            if any pattern in key.lower(): set value = "***"
            else: recurse on value
    if data is list: recurse on each item
    return data
```

### Decorator changes (5 lines pseudocode)

```
function log_function_call(func):
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)  # NEW: use function's module
        params = redact_sensitive_data(params, SENSITIVE_KEY_PATTERNS)  # NEW
        result = func(*args, **kwargs)
        result_log = redact_sensitive_data(result, SENSITIVE_KEY_PATTERNS)  # NEW
        logger.debug(...)  # Use logger instead of stdlogger
```

---

## DATA

### Input Example
```python
{'github': {'token': 'ghp_secret123', 'user': 'john'}, 'timeout': 30}
```

### Output Example (after redaction)
```python
{'github': {'token': '***', 'user': 'john'}, 'timeout': 30}
```

### Sensitive Patterns Match Logic
- `"token"` matches keys: `token`, `api_token`, `github_token`, `my_token_value`
- `"api_key"` matches keys: `api_key`, `my_api_key`
- Case-insensitive matching

---

## Test Cases (to write first)

1. `test_redact_sensitive_data_simple_dict` - Redacts `token` key in flat dict
2. `test_redact_sensitive_data_nested_dict` - Redacts in nested structures
3. `test_redact_sensitive_data_preserves_non_sensitive` - Non-sensitive keys unchanged
4. `test_redact_sensitive_data_list_of_dicts` - Handles lists containing dicts
5. `test_log_function_call_uses_correct_logger_name` - Logger is function's module
6. `test_log_function_call_redacts_sensitive_params` - Params are redacted in logs
7. `test_log_function_call_redacts_sensitive_return_values` - Return values redacted
