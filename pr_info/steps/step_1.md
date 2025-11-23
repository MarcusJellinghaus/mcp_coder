# Step 1: Create Logging Helpers Module

## WHERE
**New file**: `src/mcp_coder/llm/providers/claude/logging_utils.py`

## WHAT

Create 3 helper functions:

```python
def log_llm_request(
    method: str,  # 'cli' or 'api'
    provider: str,  # 'claude'
    session_id: str | None,
    prompt: str,
    timeout: int,
    env_vars: dict[str, str],
    cwd: str,
    command: list[str] | None = None,  # CLI only
    mcp_config: str | None = None,
) -> None:
    """Log LLM request details at DEBUG level."""
```

```python
def log_llm_response(
    method: str,
    duration_ms: int,
    cost_usd: float | None = None,  # API only
    usage: dict | None = None,  # API only
    num_turns: int | None = None,  # API only
) -> None:
    """Log LLM response metadata at DEBUG level."""
```

```python
def log_llm_error(
    method: str,
    error: Exception,
    duration_ms: int | None = None,
) -> None:
    """Log LLM error at DEBUG level."""
```

## IMPLEMENTATION

**log_llm_request():**
- Show session status: `[new]` if session_id is None, else `[resuming]`
- Show prompt preview: `{len(prompt)} chars - {prompt[:250]}...`
- Show all parameters in aligned format
- Use `logger.debug()` for output

**log_llm_response():**
- Show duration, cost (if available), usage tokens
- Format as indented fields under "Response:" header

**log_llm_error():**
- Show error type and message
- Show duration if available
- Format consistently with request/response

## TESTING

**File**: `tests/llm/providers/claude/test_logging_utils.py` (create new)

**Tests** (verify these fields exist in log output):
- `test_log_llm_request_cli` - Check: method='cli', session=[new], command present, prompt preview
- `test_log_llm_request_api` - Check: method='api', session=[resuming], no command
- `test_log_llm_response` - Check: duration, cost, usage present
- `test_log_llm_error` - Check: error type, message present

Use pytest `caplog` fixture to capture DEBUG logs.

## SUCCESS
- ✅ Module created with 3 functions
- ✅ All functions use logger.debug()
- ✅ Tests verify field presence (not formatting)
- ✅ Code quality checks pass
