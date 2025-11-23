# Step 3: Add API Request and Response Logging to ask_claude_code_api()

## Where

**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`

**Location**: In `ask_claude_code_api()` function

- **Request Logging**: Before `detailed = ask_claude_code_api_detailed_sync(...)`
- **Response Logging**: After `return create_api_response_dict(...)`

## What

Add request logging (like CLI) plus response metadata logging (unique to API) to show execution flow and costs.

### Changes Type
- **Request Logging**: Call helper function before detailed call
- **Response Logging**: Log response metadata after creating response dict
- **Non-breaking**: No changes to function behavior

## How

### Pseudocode - Request Logging

```
1. Before calling ask_claude_code_api_detailed_sync():
2. Call _log_llm_request_debug() with:
   - method="api"
   - provider="claude"
   - session_id=<from parameter>
   - command=None (API doesn't have command)
   - prompt=<question>
   - timeout=<timeout>
   - env_vars=<env_vars>
   - cwd=<cwd>
   - mcp_config=None (API doesn't use mcp_config)
3. Continue with existing detailed API call
```

### Pseudocode - Response Logging

```
1. After response dict created
2. Extract response metadata from result_info:
   - duration_ms, duration_api_ms, cost_usd, usage, result, num_turns, is_error
3. Log each field on separate line with consistent indentation
4. Format: "Response:" header then indented fields
5. Use logger.debug() for all output
```

## Algorithm

### Request Logging
```python
# Import from claude_code_cli if needed
from .claude_code_cli import _log_llm_request_debug

# Before detailed API call:
_log_llm_request_debug(
    method="api",
    provider="claude",
    session_id=session_id,
    command=None,  # API doesn't have command line
    prompt=question,
    timeout=timeout,
    env_vars=env_vars,
    cwd=cwd,
    mcp_config=None,  # API doesn't use mcp_config
)
```

### Response Logging
```python
def _log_api_response_debug(detailed_response: dict[str, Any]) -> None:
    """Log API response metadata (cost, duration, usage)."""
    result_info = detailed_response.get("result_info", {})
    
    # Log header
    logger.debug("    Response:")
    
    # Log each field from result_info
    for key, value in result_info.items():
        logger.debug(f"                 {key}: {value}")
```

## Code Changes

### Change 1: Add Request Logging

**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`

**Location**: In `ask_claude_code_api()` function, before `detailed = ask_claude_code_api_detailed_sync(...)`

**Before**:
```python
    try:
        # Call detailed function with session_id for native resumption
        detailed = ask_claude_code_api_detailed_sync(
            question, timeout, session_id, env_vars, cwd
        )
```

**After**:
```python
    try:
        # Log comprehensive request details
        # Import the helper from CLI module
        from .claude_code_cli import _log_llm_request_debug
        
        _log_llm_request_debug(
            method="api",
            provider="claude",
            session_id=session_id,
            command=None,  # API method doesn't use CLI command
            prompt=question,
            timeout=timeout,
            env_vars=env_vars,
            cwd=cwd,
            mcp_config=None,  # API method doesn't use mcp_config
        )
        
        # Call detailed function with session_id for native resumption
        detailed = ask_claude_code_api_detailed_sync(
            question, timeout, session_id, env_vars, cwd
        )
```

**Note**: The import can be moved to top-level imports if preferred, or done inline.

### Change 2: Add Response Logging Helper

**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`

**Location**: Add new helper function before `ask_claude_code_api()` definition

```python
def _log_api_response_debug(detailed_response: dict[str, Any]) -> None:
    """Log API response metadata (cost, duration, usage, etc).
    
    Args:
        detailed_response: Full response dict from ask_claude_code_api_detailed_sync()
    """
    result_info = detailed_response.get("result_info", {})
    
    if not result_info:
        logger.debug("    Response:  {}")
        return
    
    logger.debug("    Response:")
    for key, value in result_info.items():
        logger.debug(f"                 {key}: {value}")
```

### Change 3: Add Response Logging Call

**File**: `src/mcp_coder/llm/providers/claude/claude_code_api.py`

**Location**: In `ask_claude_code_api()` function, before returning response

**Before**:
```python
        # Build and return response
        return create_api_response_dict(detailed["text"], actual_session_id, detailed)
```

**After**:
```python
        # Build response
        response = create_api_response_dict(detailed["text"], actual_session_id, detailed)
        
        # Log response metadata
        _log_api_response_debug(detailed)
        
        return response
```

## Data Structures

### Request Logging Parameters
- `method`: str = "api"
- `provider`: str = "claude"
- `session_id`: str | None (from parameter)
- `command`: None (API doesn't have command)
- `prompt`: str (from question parameter)
- `timeout`: float (from timeout parameter)
- `env_vars`: dict[str, str] | None (from parameter)
- `cwd`: str | None (from parameter)
- `mcp_config`: None (API doesn't use this)

### Response Metadata Fields (from result_info dict)
```python
{
    "duration_ms": int | None,
    "duration_api_ms": int | None,
    "cost_usd": float | None,
    "usage": dict[str, int] | None,
    "result": str | None,
    "num_turns": int | None,
    "is_error": bool,
}
```

## Testing

**Test File**: `tests/llm/providers/claude/test_claude_code_api.py`

**Test Cases**:

### Test 1: Request Logging
```python
def test_ask_claude_code_api_logs_request_details(mocker, caplog):
    """Verify API request logging."""
    # Mock the detailed API call
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync',
        return_value={
            'text': 'Test response',
            'session_info': {'session_id': 'new-session'},
            'result_info': {'duration_ms': 100, 'cost_usd': 0.01},
            'raw_messages': []
        }
    )
    
    with caplog.at_level(logging.DEBUG):
        result = ask_claude_code_api(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars={'TEST': 'value'},
            cwd='/test'
        )
    
    log_text = '\n'.join(r.message for r in caplog.records if r.levelname == 'DEBUG')
    
    # Verify request logging
    assert "Claude API execution [new]" in log_text
    assert "Method:    api" in log_text
    assert "Command:" not in log_text  # API shouldn't show command
```

### Test 2: Response Logging
```python
def test_ask_claude_code_api_logs_response_metadata(mocker, caplog):
    """Verify API response metadata logging."""
    mock_response = {
        'text': 'Response text',
        'session_info': {'session_id': 'session-123'},
        'result_info': {
            'duration_ms': 2801,
            'duration_api_ms': 2500,
            'cost_usd': 0.058779,
            'usage': {'input_tokens': 100, 'output_tokens': 50},
            'num_turns': 1,
            'is_error': False,
        },
        'raw_messages': []
    }
    
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync',
        return_value=mock_response
    )
    
    with caplog.at_level(logging.DEBUG):
        result = ask_claude_code_api("Question")
    
    log_text = '\n'.join(r.message for r in caplog.records if r.levelname == 'DEBUG')
    
    # Verify response metadata logged
    assert "Response:" in log_text
    assert "duration_ms: 2801" in log_text
    assert "cost_usd: 0.058779" in log_text
    assert "input_tokens: 100" in log_text
```

### Test 3: Resuming Session
```python
def test_ask_claude_code_api_logs_resuming_session(mocker, caplog):
    """Verify [resuming] indicator for existing session."""
    mock_response = {
        'text': 'Response',
        'session_info': {'session_id': 'existing-session'},
        'result_info': {},
        'raw_messages': []
    }
    
    mocker.patch(
        'mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync',
        return_value=mock_response
    )
    
    with caplog.at_level(logging.DEBUG):
        result = ask_claude_code_api("Question", session_id="existing-session")
    
    log_text = '\n'.join(r.message for r in caplog.records if r.levelname == 'DEBUG')
    
    # Should show [resuming] not [new]
    assert "Claude API execution [resuming]" in log_text
    assert "Session:   existing-session" in log_text
```

## Files to Create/Modify

| File | Type | Details |
|------|------|---------|
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | Modify | Add request logging call, response logging helper, and response logging call |
| `tests/llm/providers/claude/test_claude_code_api.py` | Modify | Add test cases for API logging |

## Integration Points

- **Imports**: `from .claude_code_cli import _log_llm_request_debug` (cross-module)
- **Function Called**: 
  - `_log_llm_request_debug()` from CLI module (Step 1)
  - `_log_api_response_debug()` new helper in this module
- **Called By**: `ask_claude_code_api()` entry point
- **Dependencies**: Existing `ask_claude_code_api_detailed_sync()`

## Success Criteria

- ✅ Request logging added before detailed API call
- ✅ Response logging added after response creation
- ✅ All parameters passed to request logging helper
- ✅ Response metadata extracted and logged from result_info
- ✅ Session status indicator shows "[new]" or "[resuming]"
- ✅ Existing API functionality unchanged
- ✅ Tests verify both request and response logging
- ✅ Code quality checks pass
- ✅ No breaking changes to function signature

## Example Log Output

When user runs:
```python
result = ask_claude_code_api(
    "What is 5+5?",
    session_id="abc123",
    timeout=30,
    env_vars={'TEST': 'value'},
    cwd='/project'
)
```

Should log:
```
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:Claude API execution [resuming]:
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Provider:  claude
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Method:    api
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Session:   abc123
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Prompt:    13 chars - What is 5+5?
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    cwd:       /project
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Timeout:   30s
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    env_vars:  {'TEST': 'value'}
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:    Response:
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:                 duration_ms: 2801
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:                 cost_usd: 0.058779
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:                 usage: {'input_tokens': 4, 'output_tokens': 5}
DEBUG:mcp_coder.llm.providers.claude.claude_code_api:                 num_turns: 1
```
