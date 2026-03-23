# Issue #555: Catch connection/auth errors with helpful hints and optional truststore support

## Problem

The LangChain provider lets raw connection and authentication errors propagate (e.g. `WinError 10054`, SSL failures, HTTP 401/403) with no actionable guidance. This affects:
- `list_*_models()` in `_models.py`
- `_ask_text()` and `_ask_agent()` in `__init__.py`
- `_list_models_for_backend()` in `verification.py`

Additionally, Python's `httpx`/`certifi` doesn't use the OS certificate store, so SSL fails behind corporate proxies even when `curl` works.

## Solution Overview

1. **Custom exceptions** — `LLMConnectionError(ConnectionError)` and `LLMAuthError(Exception)` with provider-specific multi-line hint messages
2. **Centralized error detection** — try-import fallback tuples and message-building helpers in one module (`_exceptions.py`)
3. **Error wrapping** — all user-facing paths catch raw SDK errors and re-raise as custom exceptions with actionable hints
4. **Optional truststore** — auto-detect and activate `truststore` for OS certificate store integration via `_ssl.py`

## Architectural / Design Changes

### New modules
- **`_exceptions.py`** — Single source of truth for error detection and messaging. Contains:
  - `LLMConnectionError`, `LLMAuthError` exception classes
  - Try-import fallback tuples (`CONNECTION_ERRORS`, `OPENAI_AUTH_ERRORS`, `ANTHROPIC_AUTH_ERRORS`, `GOOGLE_CLIENT_ERRORS`)
  - `raise_connection_error()` / `raise_auth_error()` helpers that build provider-specific messages and raise the custom exceptions
- **`_ssl.py`** — Idempotent `ensure_truststore()` helper (~15 lines)

### Modified modules
- **`_models.py`** — Each `list_*_models()` wrapped with connection/auth error catching using imports from `_exceptions.py`; calls `ensure_truststore()` before API calls
- **`__init__.py`** — `_ask_text()` and `_ask_agent()` wrapped with connection/auth error catching; calls `ensure_truststore()` before model creation
- **`verification.py`** — `_list_models_for_backend()` catches `LLMConnectionError`/`LLMAuthError` specifically instead of bare `Exception`
- **`pyproject.toml`** — Adds `truststore` optional dependency group

### Design decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Error tuples location | Centralized in `_exceptions.py` | Single source of truth, no duplication |
| Message building | `raise_connection_error()` / `raise_auth_error()` helpers | Provider name + env var parameterized, SSL hint exists once |
| Google auth detection | `getattr(e, 'code', None) in (401, 403)` on `ClientError` | Defensive against SDK API changes |
| `ensure_truststore()` calls | Explicit in `_models.py` and `__init__.py` | "Explicit is better than implicit" |
| Azure OpenAI | Same message as OpenAI | Same SDK, same checks |

## Files Created / Modified

### New files
| File | Purpose |
|------|---------|
| `src/mcp_coder/llm/providers/langchain/_exceptions.py` | Custom exceptions, error tuples, message helpers |
| `src/mcp_coder/llm/providers/langchain/_ssl.py` | `ensure_truststore()` helper |

### Modified files
| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_models.py` | Wrap `list_*_models()` with error catching, call `ensure_truststore()` |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | Wrap `_ask_text()`/`_ask_agent()` with error catching, call `ensure_truststore()` |
| `src/mcp_coder/llm/providers/langchain/verification.py` | Catch specific exceptions in `_list_models_for_backend()` |
| `pyproject.toml` | Add `truststore` optional dependency group |

### Test files (new tests added to existing files)
| File | Tests added |
|------|-------------|
| `tests/llm/providers/langchain/test_langchain_models.py` | Connection/auth error wrapping for each `list_*_models()` |
| `tests/llm/providers/langchain/test_langchain_provider.py` | Connection/auth error wrapping for `_ask_text()` and `_ask_agent()` |
| `tests/llm/providers/langchain/test_langchain_verification.py` | Diagnostic output with `LLMConnectionError`/`LLMAuthError` |

## Implementation Steps

- **Step 1**: `_exceptions.py` — custom exceptions, error tuples, message helpers + tests
- **Step 2**: `_ssl.py` — `ensure_truststore()` helper + `pyproject.toml` truststore dep + tests
- **Step 3**: `_models.py` — wrap `list_*_models()` with error catching + tests
- **Step 4**: `__init__.py` — wrap `_ask_text()` and `_ask_agent()` + tests
- **Step 5**: `verification.py` — catch specific exceptions in `_list_models_for_backend()` + tests
