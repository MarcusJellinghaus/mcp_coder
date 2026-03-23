# Step 3: Wrap `list_*_models()` with connection/auth error catching

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Wrap each `list_*_models()` function in `_models.py` with try/except blocks that catch connection and auth errors and re-raise as `LLMConnectionError` / `LLMAuthError` with provider-specific hints. Also call `ensure_truststore()` before API calls.

## LLM Prompt

```
Implement Step 3 of Issue #555 (see pr_info/steps/summary.md for full context).

Wrap list_*_models() in _models.py with connection/auth error catching using _exceptions.py helpers.
Add ensure_truststore() calls. Write tests first (TDD), then the implementation.
Run all code quality checks after.
Follow the specifications in this step file exactly.
```

## WHERE

- **Modified**: `src/mcp_coder/llm/providers/langchain/_models.py`
- **Modified tests**: `tests/llm/providers/langchain/test_langchain_models.py`

## WHAT

### Changes to each function

All three functions get the same pattern:
1. Call `ensure_truststore()` after the SDK import block
2. Wrap the API call in try/except for connection errors → `raise_connection_error()`
3. Wrap the API call in try/except for auth errors → `raise_auth_error()` (or `is_google_auth_error()` for Gemini)

### Imports added to `_models.py`

```python
from ._ssl import ensure_truststore
from ._exceptions import (
    CONNECTION_ERRORS,
    OPENAI_AUTH_ERRORS,
    ANTHROPIC_AUTH_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
```

## HOW

### Integration pattern for each function

```python
def list_openai_models(api_key, endpoint=None):
    # ... existing ImportError handling ...
    ensure_truststore()
    try:
        client = openai.OpenAI(...)
        return sorted(m.id for m in client.models.list())
    except OPENAI_AUTH_ERRORS as exc:
        raise_auth_error("OpenAI", "OPENAI_API_KEY", exc)
    except CONNECTION_ERRORS as exc:
        raise_connection_error("OpenAI", "OPENAI_API_KEY", exc,
                               endpoint_hint="endpoint/base_url if using a custom server")
```

**Note on except order**: Auth errors must be caught before connection errors. `openai.AuthenticationError` inherits from `openai.APIStatusError`, not from `OSError`/`httpx` errors, so order matters only for clarity. For Google, `ClientError` for auth vs `httpx`/`OSError` for connection are disjoint, but we check auth first for consistency.

### Provider-specific parameters

| Provider | `provider` | `env_var` | `endpoint_hint` |
|----------|-----------|-----------|-----------------|
| OpenAI | `"OpenAI"` | `"OPENAI_API_KEY"` | `"endpoint/base_url if using a custom server"` |
| Gemini | `"Gemini"` | `"GEMINI_API_KEY"` | `""` (empty) |
| Anthropic | `"Anthropic"` | `"ANTHROPIC_API_KEY"` | `""` (empty) |

### Google/Gemini special case

```python
except (*GOOGLE_CLIENT_ERRORS,) as exc:
    if is_google_auth_error(exc):
        raise_auth_error("Gemini", "GEMINI_API_KEY", exc)
    raise_connection_error("Gemini", "GEMINI_API_KEY", exc)
except CONNECTION_ERRORS as exc:
    raise_connection_error("Gemini", "GEMINI_API_KEY", exc)
```

If `GOOGLE_CLIENT_ERRORS` is empty (SDK not installed), the except clause is effectively skipped.

## ALGORITHM

### `list_openai_models` (representative — others follow same pattern)
```
1. Import openai SDK (existing ImportError handling stays)
2. Call ensure_truststore()
3. Try: create client, call client.models.list(), return sorted IDs
4. Except OPENAI_AUTH_ERRORS: raise_auth_error("OpenAI", "OPENAI_API_KEY", exc)
5. Except CONNECTION_ERRORS: raise_connection_error("OpenAI", "OPENAI_API_KEY", exc, endpoint_hint=...)
```

## DATA

- Input/output signatures unchanged — same `list[str]` return
- New exception types raised: `LLMConnectionError`, `LLMAuthError` (in addition to existing `ImportError`)
- Existing non-connection, non-auth errors still propagate unchanged

## Tests (added to `test_langchain_models.py`)

### New test classes

**`TestListOpenaiModelsConnectionError`**
- `test_oserror_raises_llm_connection_error` — `client.models.list()` raises `OSError` → caught as `LLMConnectionError`
- `test_connection_error_message_contains_hints` — verify message has "OPENAI_API_KEY" and "endpoint"

**`TestListOpenaiModelsAuthError`**
- `test_auth_error_raises_llm_auth_error` — mock `openai.AuthenticationError`, verify `LLMAuthError` raised
- `test_auth_error_message_contains_hints` — verify message has "OPENAI_API_KEY"

**`TestListGeminiModelsConnectionError`**
- `test_oserror_raises_llm_connection_error` — `client.models.list()` raises `OSError` → `LLMConnectionError`
- `test_connection_error_message_contains_hints` — verify "GEMINI_API_KEY" in message

**`TestListGeminiModelsAuthError`**
- `test_client_error_401_raises_llm_auth_error` — mock `ClientError` with code=401 → `LLMAuthError`
- `test_client_error_500_raises_llm_connection_error` — mock `ClientError` with code=500 → `LLMConnectionError` (non-auth ClientError treated as connection issue)

**`TestListAnthropicModelsConnectionError`**
- `test_oserror_raises_llm_connection_error` — `client.models.list()` raises `OSError` → `LLMConnectionError`
- `test_connection_error_message_contains_hints` — verify "ANTHROPIC_API_KEY" in message

**`TestListAnthropicModelsAuthError`**
- `test_auth_error_raises_llm_auth_error` — mock `anthropic.AuthenticationError` → `LLMAuthError`
- `test_auth_error_message_contains_hints` — verify "ANTHROPIC_API_KEY" in message

**`TestListModelsEnsureTruststore`**
- `test_openai_calls_ensure_truststore` — verify `ensure_truststore()` called
- `test_gemini_calls_ensure_truststore` — verify `ensure_truststore()` called
- `test_anthropic_calls_ensure_truststore` — verify `ensure_truststore()` called

### Existing tests unchanged
The existing `TestListModelsCommon.test_list_*_handles_api_error` tests use generic `Exception("API error")` which doesn't match any SDK-specific error tuple, so they continue to propagate unchanged. No modifications needed.
