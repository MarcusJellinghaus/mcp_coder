# Step 2: Fix Logger Name to Use Decorated Function's Module

## LLM Prompt

```
Implement Step 2 of Issue #228 (see pr_info/steps/summary.md for context).

Fix the logger name in `@log_function_call` to use the decorated function's module 
instead of the log_utils module. Follow TDD - write tests first, then implement.

Requirements:
- Logger name should reflect `func.__module__` (e.g., "mcp_coder.utils.user_config")
- NOT the log_utils module name ("mcp_coder.utils.log_utils")
- Both standard logger and structlog should use the correct module name
```

## WHERE: File Paths

- **Test file**: `tests/utils/test_log_utils.py`
- **Implementation**: `src/mcp_coder/utils/log_utils.py`

## WHAT: Changes Required

### Current (Wrong)
```python
# Module-level logger
stdlogger = logging.getLogger(__name__)  # Always "mcp_coder.utils.log_utils"

def log_function_call(func):
    def wrapper(*args, **kwargs):
        # Uses module-level stdlogger
        stdlogger.debug("Calling %s...", func_name, ...)
```

### After (Correct)
```python
def log_function_call(func):
    def wrapper(*args, **kwargs):
        # Get logger for the decorated function's module
        func_logger = logging.getLogger(func.__module__)
        func_logger.debug("Calling %s...", func_name, ...)
```

## HOW: Integration Points

1. Replace all `stdlogger.debug(...)` calls with `func_logger.debug(...)`
2. Replace all `stdlogger.error(...)` calls with `func_logger.error(...)`
3. Keep module-level `stdlogger` for `setup_logging()` function (it logs about itself)
4. Update structlog logger to also use `func.__module__`

## ALGORITHM: Logger Selection (3 lines)

```
function wrapper(*args, **kwargs):
    func_logger = logging.getLogger(func.__module__)
    # ... use func_logger instead of stdlogger for all logs
```

## DATA: Expected Log Output

**Before:**
```
2026-01-02 21:32:15 - mcp_coder.utils.log_utils - DEBUG - load_config completed...
```

**After:**
```
2026-01-02 21:32:15 - mcp_coder.utils.user_config - DEBUG - load_config completed...
```

## Test Cases to Implement

### Test 1: Logger name matches decorated function's module
```python
def test_log_function_call_uses_correct_logger_name():
    """Verify logger name is the decorated function's module, not log_utils."""
    captured_logger_name = None
    
    # Create a mock that captures the logger name
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Define function in a specific module context
        @log_function_call
        def my_func() -> int:
            return 42
        
        # Trigger the logging
        my_func()
        
        # Verify getLogger was called with the function's module
        # The function is defined in this test module
        calls = [call[0][0] for call in mock_get_logger.call_args_list]
        assert __name__ in calls or "tests.utils.test_log_utils" in calls
```

### Test 2: Logger name NOT log_utils module
```python
def test_log_function_call_logger_not_log_utils():
    """Verify logs don't show mcp_coder.utils.log_utils as the logger name."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        @log_function_call
        def test_func() -> str:
            return "result"
        
        test_func()
        
        # Verify log_utils was NOT used as logger name for function logging
        call_args = [str(call) for call in mock_get_logger.call_args_list]
        # Should not see log_utils as the logger for function calls
        func_logger_calls = [c for c in call_args if "log_utils" not in c]
        assert len(func_logger_calls) > 0  # At least one call without log_utils
```

### Test 3: Structlog also uses correct module name
```python
def test_log_function_call_structlog_uses_correct_module():
    """Verify structlog logger also uses decorated function's module."""
    with patch("mcp_coder.utils.log_utils.structlog") as mock_structlog:
        mock_structlogger = MagicMock()
        mock_structlog.get_logger.return_value = mock_structlogger
        
        # Simulate file handler present (triggers structlog path)
        with patch.object(logging.getLogger(), "handlers", [logging.FileHandler("/tmp/test.log")]):
            @log_function_call
            def logged_func() -> int:
                return 1
            
            logged_func()
            
            # Verify structlog.get_logger was called with function's module
            mock_structlog.get_logger.assert_called()
```

## Implementation Checklist

- [ ] Write tests first (TDD)
- [ ] Create `func_logger = logging.getLogger(func.__module__)` inside wrapper
- [ ] Replace `stdlogger.debug(...)` → `func_logger.debug(...)`
- [ ] Replace `stdlogger.error(...)` → `func_logger.error(...)`  
- [ ] Update structlog call: `structlog.get_logger(module_name)` uses same module
- [ ] Keep `stdlogger` for `setup_logging()` internal logs
- [ ] Run tests to verify
