# Step 3: Add Redaction Tests

## LLM Prompt
```
Implement Step 3 of Issue #228 (see pr_info/steps/summary.md).
Add comprehensive tests for the redaction functionality added in Step 1.
Tests should verify sensitive data is properly redacted in logs.
```

## Overview

Add tests to verify:
1. `_redact_sensitive_data()` helper function works correctly
2. `@log_function_call` decorator redacts sensitive params and results
3. Logger name is the decorated function's module

---

## WHERE

**File to modify**: `tests/utils/test_log_utils.py`

---

## WHAT

### New Test Class: `TestRedactSensitiveData`

```python
class TestRedactSensitiveData:
    """Tests for _redact_sensitive_data helper function."""
    
    def test_redacts_token_key(self) -> None: ...
    def test_redacts_api_token_key(self) -> None: ...
    def test_redacts_nested_sensitive_keys(self) -> None: ...
    def test_preserves_non_sensitive_keys(self) -> None: ...
    def test_handles_list_of_dicts(self) -> None: ...
    def test_handles_empty_dict(self) -> None: ...
    def test_handles_non_dict_input(self) -> None: ...
    def test_case_insensitive_matching(self) -> None: ...
```

### New Test Class: `TestLogFunctionCallRedaction`

```python
class TestLogFunctionCallRedaction:
    """Tests for redaction in @log_function_call decorator."""
    
    def test_uses_decorated_function_module_logger(self) -> None: ...
    def test_redacts_sensitive_parameters(self) -> None: ...
    def test_redacts_sensitive_return_values(self) -> None: ...
```

---

## HOW

### Test Helper Setup

```python
from mcp_coder.utils.log_utils import (
    _redact_sensitive_data,
    SENSITIVE_KEY_PATTERNS,
    REDACTED_VALUE,
    log_function_call,
)
```

---

## DATA

### Test Cases with Examples

#### `test_redacts_token_key`
```python
# Input
{"token": "ghp_secret123", "user": "john"}
# Expected Output
{"token": "***", "user": "john"}
```

#### `test_redacts_nested_sensitive_keys`
```python
# Input
{"github": {"token": "ghp_xxx", "repo": "test"}, "timeout": 30}
# Expected Output
{"github": {"token": "***", "repo": "test"}, "timeout": 30}
```

#### `test_handles_list_of_dicts`
```python
# Input
[{"token": "secret1"}, {"token": "secret2"}]
# Expected Output
[{"token": "***"}, {"token": "***"}]
```

#### `test_case_insensitive_matching`
```python
# Input
{"TOKEN": "secret", "Api_Token": "secret2", "MyToken": "secret3"}
# Expected Output
{"TOKEN": "***", "Api_Token": "***", "MyToken": "***"}
```

#### `test_uses_decorated_function_module_logger`
```python
# Setup: Create a function in a test module
@log_function_call
def test_func():
    return "result"

# Verify: Logger name should be the test module, not "mcp_coder.utils.log_utils"
# Check mock_logger was called with correct module name
```

#### `test_redacts_sensitive_parameters`
```python
# Setup
@log_function_call
def func_with_token(token: str, name: str) -> str:
    return f"Hello {name}"

# Execute
result = func_with_token(token="secret123", name="Alice")

# Verify: Log output contains "token": "***", not "token": "secret123"
```

#### `test_redacts_sensitive_return_values`
```python
# Setup
@log_function_call
def func_returns_sensitive() -> dict:
    return {"api_token": "sk-secret", "data": "public"}

# Execute
result = func_returns_sensitive()

# Verify: Log output contains "api_token": "***"
# Verify: Actual return value is NOT redacted (only log is)
```

---

## ALGORITHM

### Test Pattern for Log Verification

```python
def test_redacts_sensitive_parameters(self, caplog):
    # 1. Set log level to DEBUG
    caplog.set_level(logging.DEBUG)
    
    # 2. Define and call decorated function with sensitive param
    @log_function_call
    def func(token: str): return token
    
    result = func(token="secret123")
    
    # 3. Verify actual result unchanged
    assert result == "secret123"
    
    # 4. Verify log contains redacted value
    assert "***" in caplog.text
    assert "secret123" not in caplog.text
```

---

## Acceptance Verification

After implementing these tests:

1. Run: `pytest tests/utils/test_log_utils.py -v`
2. All new tests should pass
3. All existing tests should still pass
4. Run full test suite: `pytest` to ensure no regressions
