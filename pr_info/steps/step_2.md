# Step 2: Add CLI Logging

## WHERE
**File**: `src/mcp_coder/llm/providers/claude/claude_code_cli.py`
**Function**: `ask_claude_code_cli()`

## WHAT

Add request/response/error logging around subprocess execution:

```python
from .logging_utils import log_llm_request, log_llm_response, log_llm_error

def ask_claude_code_cli(...) -> LLMResponse:
    # Build command, prepare env...
    
    # ADD: Log request
    log_llm_request(
        method="cli",
        provider="claude",
        session_id=session_id,
        prompt=prompt,
        timeout=timeout,
        env_vars=env_vars,
        cwd=cwd,
        command=command,
        mcp_config=mcp_config_path,
    )
    
    start_time = time.time()
    try:
        # Execute subprocess...
        result = execute_subprocess(...)
        
        # ADD: Log response
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_response(method="cli", duration_ms=duration_ms)
        
        return result
    except Exception as e:
        # ADD: Log error
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(method="cli", error=e, duration_ms=duration_ms)
        raise
```

## TESTING

**File**: `tests/llm/providers/claude/test_claude_code_cli.py`

**Tests**:
- `test_cli_logs_request` - Mock subprocess, check request log contains: method, prompt preview, command
- `test_cli_logs_response` - Check response log contains: duration
- `test_cli_logs_error` - Mock exception, check error log contains: error type, message

## SUCCESS
- ✅ Logs appear before/after subprocess execution
- ✅ Error logging works on exception
- ✅ Tests pass
- ✅ Code quality checks pass
