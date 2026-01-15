# Step 1: Add Sensitive Field Redaction to `@log_function_call` Decorator

## LLM Prompt

```
Implement Step 1 of Issue #228 (see pr_info/steps/summary.md for context).

Add `sensitive_fields` parameter to the `@log_function_call` decorator that redacts 
sensitive values before logging. Follow TDD - write tests first, then implement.

Requirements:
- Decorator must work both as `@log_function_call` and `@log_function_call(sensitive_fields=[...])`
- Redact parameter values where param name matches sensitive_fields
- Redact dict return values where key matches sensitive_fields (recursive for nested dicts)
- Display redacted values as "***"
- Original function parameters and return values must NOT be modified
```

## WHERE: File Paths

- **Test file**: `tests/utils/test_log_utils.py`
- **Implementation**: `src/mcp_coder/utils/log_utils.py`

## WHAT: Main Functions

### New Helper Function
```python
def _redact_for_logging(
    data: dict[str, Any], 
    sensitive_fields: set[str]
) -> dict[str, Any]:
    """Create a copy of data with sensitive fields redacted for logging."""
```

### Modified Decorator Signature
```python
def log_function_call(
    func: Callable[..., T] | None = None,
    *,
    sensitive_fields: list[str] | None = None
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log function calls with optional sensitive field redaction."""
```

## HOW: Integration Points

1. Decorator pattern with optional arguments (keyword-only `sensitive_fields`)
2. Use `functools.wraps` to preserve function metadata
3. Redact copies of `serializable_params` and `result_for_log` before logging

## ALGORITHM: Redaction Logic (5 lines)

```
function _redact_for_logging(data, sensitive_fields):
    result = shallow_copy(data)
    for key in result:
        if key in sensitive_fields:
            result[key] = "***"
        elif isinstance(result[key], dict):
            result[key] = _redact_for_logging(result[key], sensitive_fields)
    return result
```

## DATA: Structures

**Input to redaction:**
```python
{"github": {"token": "ghp_secret123", "user": "myuser"}, "timeout": 30}
```

**Output after redaction (sensitive_fields=["token"]):**
```python
{"github": {"token": "***", "user": "myuser"}, "timeout": 30}
```

## Test Cases to Implement

### Test 1: Decorator works without sensitive_fields (backward compatible)
```python
def test_log_function_call_without_sensitive_fields():
    @log_function_call
    def simple_func(x: int) -> int:
        return x * 2
    assert simple_func(5) == 10
```

### Test 2: Parameter redaction
```python
def test_log_function_call_redacts_sensitive_params(mock_logger):
    @log_function_call(sensitive_fields=["token", "password"])
    def auth_func(token: str, username: str) -> bool:
        return True
    
    auth_func(token="secret123", username="user")
    
    # Verify log contains "***" for token, but "user" for username
    log_call = mock_logger.debug.call_args_list[0]
    assert "***" in str(log_call)
    assert "secret123" not in str(log_call)
    assert "user" in str(log_call)
```

### Test 3: Return value redaction (flat dict)
```python
def test_log_function_call_redacts_sensitive_return_value(mock_logger):
    @log_function_call(sensitive_fields=["token"])
    def get_config() -> dict:
        return {"token": "secret", "name": "test"}
    
    result = get_config()
    
    # Original return value unchanged
    assert result["token"] == "secret"
    # Log should have redacted value
    log_call = mock_logger.debug.call_args_list[1]  # completion log
    assert "***" in str(log_call)
    assert "secret" not in str(log_call)
```

### Test 4: Return value redaction (nested dict)
```python
def test_log_function_call_redacts_nested_sensitive_values(mock_logger):
    @log_function_call(sensitive_fields=["token", "api_token"])
    def load_config() -> dict:
        return {
            "github": {"token": "ghp_xxx"},
            "jenkins": {"api_token": "jenkins_xxx", "url": "http://..."}
        }
    
    result = load_config()
    
    # Original unchanged
    assert result["github"]["token"] == "ghp_xxx"
    # Log redacted
    log_call = mock_logger.debug.call_args_list[1]
    assert "ghp_xxx" not in str(log_call)
    assert "jenkins_xxx" not in str(log_call)
```

### Test 5: Helper function unit test
```python
def test_redact_for_logging_handles_nested_dicts():
    data = {"outer": {"token": "secret", "safe": "visible"}}
    result = _redact_for_logging(data, {"token"})
    
    assert result["outer"]["token"] == "***"
    assert result["outer"]["safe"] == "visible"
    # Original unchanged
    assert data["outer"]["token"] == "secret"
```

## Implementation Checklist

- [ ] Add `_redact_for_logging()` helper function
- [ ] Modify `log_function_call` to accept optional `sensitive_fields` parameter
- [ ] Apply redaction to `serializable_params` before logging
- [ ] Apply redaction to `result_for_log` before logging
- [ ] Write tests first (TDD)
- [ ] Run tests to verify
