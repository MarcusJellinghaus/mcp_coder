# Step 1: Custom exceptions, error tuples, and message helpers

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Create `_exceptions.py` as the single source of truth for error detection and user-facing error messaging. This module is the foundation that all subsequent steps import from.

## LLM Prompt

```
Implement Step 1 of Issue #555 (see pr_info/steps/summary.md for full context).

Create _exceptions.py with custom exceptions, try-import error tuples, and message helpers.
Write tests first (TDD), then the implementation. Run all code quality checks after.
Follow the specifications in this step file exactly.
```

## WHERE

- **New**: `src/mcp_coder/llm/providers/langchain/_exceptions.py`
- **New tests**: `tests/llm/providers/langchain/test_langchain_exceptions.py`

## WHAT

### Exception classes

```python
class LLMConnectionError(ConnectionError):
    """Network, SSL, or transport failure connecting to an LLM provider."""

class LLMAuthError(Exception):
    """Authentication failure (HTTP 401/403) from an LLM provider."""
```

### Try-import fallback tuples (module-level)

```python
# Connection errors — httpx transport failures + OS-level socket errors
try:
    import httpx
    CONNECTION_ERRORS: tuple[type[Exception], ...] = (httpx.ConnectError, httpx.ConnectTimeout, OSError)
except ImportError:
    CONNECTION_ERRORS = (OSError,)

# Auth errors per provider — SDK-native exception classes
try:
    import openai
    OPENAI_AUTH_ERRORS: tuple[type[Exception], ...] = (openai.AuthenticationError,)
except ImportError:
    OPENAI_AUTH_ERRORS = ()

try:
    import anthropic
    ANTHROPIC_AUTH_ERRORS: tuple[type[Exception], ...] = (anthropic.AuthenticationError,)
except ImportError:
    ANTHROPIC_AUTH_ERRORS = ()

try:
    from google.genai import errors as genai_errors
    GOOGLE_CLIENT_ERRORS: tuple[type[Exception], ...] = (genai_errors.ClientError,)
except ImportError:
    GOOGLE_CLIENT_ERRORS = ()
```

### Message helper functions

```python
_SSL_HINT = (
    "For SSL errors behind a corporate proxy, try:\n"
    "  pip install 'mcp-coder[truststore]'\n"
    "  or set SSL_CERT_FILE / REQUESTS_CA_BUNDLE env var to your corporate CA bundle."
)

def raise_connection_error(provider: str, env_var: str, original: Exception, endpoint_hint: str = "") -> NoReturn:
    """Build multi-line connection error message and raise LLMConnectionError."""

def raise_auth_error(provider: str, env_var: str, original: Exception) -> NoReturn:
    """Build multi-line auth error message and raise LLMAuthError."""

def is_google_auth_error(exc: Exception) -> bool:
    """Check if a google.genai ClientError is an auth error (code 401 or 403)."""
```

### Signatures and return values

- `raise_connection_error(provider, env_var, original, endpoint_hint)` → `NoReturn` (always raises `LLMConnectionError`)
- `raise_auth_error(provider, env_var, original)` → `NoReturn` (always raises `LLMAuthError`)
- `is_google_auth_error(exc)` → `bool`

## ALGORITHM

### `raise_connection_error`
```
1. Build message: f"Connection to {provider} API failed: {original}"
2. Append "Check:" block with numbered items: env_var, endpoint_hint (if provided), network/firewall/proxy
3. Append _SSL_HINT
4. Raise LLMConnectionError(message) from original
```

### `raise_auth_error`
```
1. Build message: f"Authentication to {provider} API failed: {original}"
2. Append "Check:" block with numbered items: env_var env var, api_key in config.toml
3. Raise LLMAuthError(message) from original
```

### `is_google_auth_error`
```
1. If GOOGLE_CLIENT_ERRORS is empty, return False
2. If not isinstance(exc, GOOGLE_CLIENT_ERRORS), return False
3. Return getattr(exc, 'code', None) in (401, 403)
```

## DATA

### Error message format (connection)
```
Connection to OpenAI API failed: [original error]
Check:
  1. OPENAI_API_KEY env var or api_key in config.toml
  2. endpoint/base_url if using a custom server
  3. Network/firewall/proxy settings
For SSL errors behind a corporate proxy, try:
  pip install 'mcp-coder[truststore]'
  or set SSL_CERT_FILE / REQUESTS_CA_BUNDLE env var to your corporate CA bundle.
```

### Error message format (auth)
```
Authentication to OpenAI API failed: [original error]
Check:
  1. OPENAI_API_KEY env var is set and valid
  2. api_key in config.toml is correct
```

## Tests (`test_langchain_exceptions.py`)

### Test classes and cases

**`TestLLMConnectionError`**
- `test_is_subclass_of_connection_error` — verify `issubclass(LLMConnectionError, ConnectionError)`
- `test_can_be_caught_as_connection_error` — `except ConnectionError` catches it

**`TestLLMAuthError`**
- `test_is_subclass_of_exception` — verify `issubclass(LLMAuthError, Exception)`
- `test_not_subclass_of_connection_error` — ensure it's separate from `ConnectionError`

**`TestRaiseConnectionError`**
- `test_raises_llm_connection_error` — verify it raises `LLMConnectionError`
- `test_message_contains_provider_and_original` — check "OpenAI" and original error text in message
- `test_message_contains_env_var_hint` — check env var name in message
- `test_message_contains_ssl_hint` — check SSL/truststore hint in message
- `test_message_contains_endpoint_hint_when_provided` — check endpoint hint appears
- `test_message_omits_endpoint_hint_when_empty` — check no endpoint line when not provided
- `test_chains_original_exception` — verify `__cause__` is set

**`TestRaiseAuthError`**
- `test_raises_llm_auth_error` — verify it raises `LLMAuthError`
- `test_message_contains_provider_and_original` — check provider name and original error
- `test_message_contains_env_var_hint` — check env var name
- `test_message_does_not_contain_ssl_hint` — auth errors shouldn't mention SSL
- `test_chains_original_exception` — verify `__cause__` is set

**`TestIsGoogleAuthError`**
- `test_returns_true_for_401` — mock `ClientError` with code=401
- `test_returns_true_for_403` — mock `ClientError` with code=403
- `test_returns_false_for_other_codes` — mock with code=500
- `test_returns_false_for_non_client_error` — plain `Exception`
- `test_returns_false_when_google_not_installed` — when `GOOGLE_CLIENT_ERRORS` is empty

**`TestErrorTuples`**
- `test_connection_errors_contains_oserror` — `OSError` is always present
- `test_openai_auth_tuple_is_tuple` — type check
- `test_anthropic_auth_tuple_is_tuple` — type check
- `test_google_client_tuple_is_tuple` — type check
