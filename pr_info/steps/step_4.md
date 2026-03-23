# Step 4: Wrap `_ask_text()` and `_ask_agent()` with connection/auth error catching

> **Context**: See `pr_info/steps/summary.md` for the full issue and architecture.

## Goal

Add connection/auth error catching to `_ask_text()` (around `chat_model.invoke()`) and `_ask_agent()` (around `asyncio.run(run_agent(...))`) in `__init__.py`. Also call `ensure_truststore()` before model creation.

## LLM Prompt

```
Implement Step 4 of Issue #555 (see pr_info/steps/summary.md for full context).

Wrap _ask_text() and _ask_agent() in __init__.py with connection/auth error catching.
Add ensure_truststore() calls before _create_chat_model(). Write tests first (TDD), then implementation.
Run all code quality checks after.
Follow the specifications in this step file exactly.
```

## WHERE

- **Modified**: `src/mcp_coder/llm/providers/langchain/__init__.py`
- **Modified tests**: `tests/llm/providers/langchain/test_langchain_provider.py`

## WHAT

### Imports added to `__init__.py`

```python
from ._exceptions import (
    CONNECTION_ERRORS,
    OPENAI_AUTH_ERRORS,
    ANTHROPIC_AUTH_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    LLMAuthError,
    LLMConnectionError,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)
from ._ssl import ensure_truststore
```

### Helper to resolve provider-specific error params

```python
_BACKEND_ERROR_PARAMS: dict[str, tuple[str, str, str]] = {
    "openai": ("OpenAI", "OPENAI_API_KEY", "endpoint/base_url if using a custom server"),
    "gemini": ("Gemini", "GEMINI_API_KEY", ""),
    "anthropic": ("Anthropic", "ANTHROPIC_API_KEY", ""),
}
```

### Changes to `_ask_text()`

Add `ensure_truststore()` call before `_create_chat_model()`. Extend the existing try/except around `chat_model.invoke()` to also catch connection/auth errors **before** the existing 404 check.

### Changes to `_ask_agent()`

Add `ensure_truststore()` call before `_create_chat_model()`. Wrap `asyncio.run(run_agent(...))` with connection/auth error catching. Only catch connection/auth — let MCP/tool errors propagate.

## HOW

### `_ask_text()` integration

The existing try/except already catches `Exception` and checks for 404. We add auth/connection catching **above** the generic handler:

```python
ensure_truststore()
chat_model = _create_chat_model(config, timeout=timeout)

try:
    ai_msg = chat_model.invoke(lc_messages)
except (*_auth_errors_for_backend(backend),) as exc:
    provider, env_var, endpoint_hint = _BACKEND_ERROR_PARAMS.get(backend, (backend, "", ""))
    if backend == "gemini" and not is_google_auth_error(exc):
        raise_connection_error(provider, env_var, exc, endpoint_hint)
    raise_auth_error(provider, env_var, exc)
except CONNECTION_ERRORS as exc:
    provider, env_var, endpoint_hint = _BACKEND_ERROR_PARAMS.get(backend, (backend, "", ""))
    raise_connection_error(provider, env_var, exc, endpoint_hint)
except Exception as exc:
    # existing 404 handling unchanged
    ...
```

### Auth error tuple resolution helper

```python
def _auth_errors_for_backend(backend: str | None) -> tuple[type[Exception], ...]:
    """Return the auth error tuple for the given backend."""
    if backend == "openai":
        return OPENAI_AUTH_ERRORS
    if backend == "anthropic":
        return ANTHROPIC_AUTH_ERRORS
    if backend == "gemini":
        return GOOGLE_CLIENT_ERRORS  # needs is_google_auth_error() check at call site
    return ()
```

**Google special case in `_ask_text()`/`_ask_agent()`**: For Gemini, catch `GOOGLE_CLIENT_ERRORS` and check `is_google_auth_error()` — if auth, raise auth error; otherwise raise connection error. This matches the pattern in Step 3.

```python
# Gemini-aware auth/connection handling (used in both _ask_text and _ask_agent):
except (*_auth_errors_for_backend(backend),) as exc:
    provider, env_var, endpoint_hint = _BACKEND_ERROR_PARAMS.get(backend, (backend, "", ""))
    if backend == "gemini" and not is_google_auth_error(exc):
        raise_connection_error(provider, env_var, exc, endpoint_hint)
    raise_auth_error(provider, env_var, exc)
```

### `_ask_agent()` integration

```python
ensure_truststore()
chat_model = _create_chat_model(config, timeout=timeout)
# ... existing history loading ...

try:
    text, messages, stats = asyncio.run(run_agent(...))
except (*_auth_errors_for_backend(config.get("backend")),) as exc:
    # ... same pattern as _ask_text
except CONNECTION_ERRORS as exc:
    # ... same pattern as _ask_text
```

## ALGORITHM

### `_ask_text` error handling (extended)
```
1. Call ensure_truststore()
2. Create chat model
3. Try invoke
4. Except auth errors for backend → raise_auth_error with provider params
5. Except CONNECTION_ERRORS → raise_connection_error with provider params
6. Except generic Exception → existing 404/not_found handling (unchanged)
```

### `_ask_agent` error handling (new)
```
1. Call ensure_truststore()
2. Create chat model, load history
3. Try asyncio.run(run_agent(...))
4. Except auth errors for backend → raise_auth_error with provider params
5. Except CONNECTION_ERRORS → raise_connection_error with provider params
6. All other exceptions propagate unchanged (MCP/tool errors)
```

## DATA

- Return types unchanged — `LLMResponseDict` from both functions
- New exceptions raised: `LLMConnectionError`, `LLMAuthError`
- `_BACKEND_ERROR_PARAMS` — `dict[str, tuple[str, str, str]]` mapping backend name to (provider_display_name, env_var, endpoint_hint)

## Tests (added to `test_langchain_provider.py`)

### New test classes

**`TestAskTextConnectionError`**
- `test_connection_error_raises_llm_connection_error` — mock `chat_model.invoke()` to raise `OSError`, verify `LLMConnectionError` raised
- `test_connection_error_message_contains_provider_hint` — verify "OpenAI" and "OPENAI_API_KEY" in message (for openai backend)

**`TestAskTextAuthError`**
- `test_auth_error_raises_llm_auth_error` — mock `chat_model.invoke()` to raise openai `AuthenticationError`, verify `LLMAuthError` raised
- `test_auth_error_message_contains_provider_hint` — verify hint content

**`TestAskAgentConnectionError`**
- `test_connection_error_raises_llm_connection_error` — mock `asyncio.run` path to raise `OSError`, verify `LLMConnectionError` raised
- `test_non_connection_error_propagates` — mock non-connection error, verify it propagates unchanged

**`TestAskAgentAuthError`**
- `test_auth_error_raises_llm_auth_error` — mock auth error in agent path, verify `LLMAuthError` raised

**`TestEnsureTruststoreCalled`**
- `test_ask_text_calls_ensure_truststore` — verify `ensure_truststore()` called in text path
- `test_ask_agent_calls_ensure_truststore` — verify `ensure_truststore()` called in agent path

### Existing tests unchanged
- `TestAskTextModelNotFound` tests still work — 404 errors don't match auth/connection patterns
- `TestAskLangchain` tests still work — mocked model doesn't raise errors
