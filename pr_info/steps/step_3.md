# Step 3: Add API Logging

## WHERE
**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`
**Function**: `ask_claude_code_api()`

## WHAT

Add request/response/error logging around API execution:

```python
from .logging_utils import log_llm_request, log_llm_response, log_llm_error

def ask_claude_code_api(...) -> LLMResponse:
    # Prepare parameters...
    
    # ADD: Log request
    log_llm_request(
        method="api",
        provider="claude",
        session_id=session_id,
        prompt=prompt,
        timeout=timeout,
        env_vars=env_vars,
        cwd=cwd,
    )
    
    start_time = time.time()
    try:
        # Call API...
        response = ask_claude_code_api_detailed_sync(...)
        
        # ADD: Log response
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_response(
            method="api",
            duration_ms=duration_ms,
            cost_usd=response.cost_usd,
            usage=response.usage,
            num_turns=response.num_turns,
        )
        
        return LLMResponse(...)
    except Exception as e:
        # ADD: Log error
        duration_ms = int((time.time() - start_time) * 1000)
        log_llm_error(method="api", error=e, duration_ms=duration_ms)
        raise
```

## TESTING

**File**: `tests/llm/providers/claude/test_claude_code_api.py`

**Tests**:
- `test_api_logs_request` - Mock API call, check request log contains: method, prompt preview, session
- `test_api_logs_response` - Check response log contains: duration, cost, usage, turns
- `test_api_logs_error` - Mock exception, check error log contains: error type, message

## SUCCESS
- ✅ Logs appear before/after API execution
- ✅ Response metadata logged (cost, usage, turns)
- ✅ Error logging works on exception
- ✅ Tests pass
- ✅ Code quality checks pass
