# Issue #562: LLM Provider Connection Behind Corporate Proxy

## Problem

When running `mcp-coder verify` behind a corporate firewall/proxy with SSL inspection, the LLM provider test fails with `WinError 10054` (connection reset). The current `truststore.inject_into_ssl()` global monkey-patch is insufficient because:

1. httpx may cache its SSL context before injection runs
2. No proxy routing — `HTTPS_PROXY`/`HTTP_PROXY` env vars are not explicitly used
3. Error output is generic with no actionable proxy/firewall guidance

## Architecture / Design Changes

### New Module: `src/mcp_coder/llm/providers/langchain/_http.py`

Shared httpx client factory with **explicit** truststore-backed SSL context. Replaces implicit reliance on global monkey-patching with deterministic SSL context injection.

```
_http.py
├── create_ssl_context()        → ssl.SSLContext (truststore or default)
├── create_http_client()        → httpx.Client(verify=ssl_ctx)
└── create_async_http_client()  → httpx.AsyncClient(verify=ssl_ctx)
```

Both clients automatically respect `HTTPS_PROXY`/`HTTP_PROXY` (httpx native behavior). DEBUG-level logging of proxy presence and SSL context type. Never logs secrets.

### Modified Module: `src/mcp_coder/llm/providers/langchain/_exceptions.py`

Extended with error classification and diagnostic formatting (merged here instead of a separate `_diagnostics.py` — KISS). New functions:

- `classify_connection_error(exc)` — maps exception type + error codes to human-readable category
- `format_diagnostics(exc)` — builds diagnostic block (proxy set? truststore active?) for connection failures
- `_is_connection_reset(exc)` — iterative chain walk with max depth of 5 (no unbounded recursion)

Proxy detection checks both uppercase and lowercase env vars (`HTTPS_PROXY`/`https_proxy`/`HTTP_PROXY`/`http_proxy`).

### Modified Backends: Explicit HTTP Client Injection

All three LangChain backends (`openai_backend.py`, `anthropic_backend.py`, `gemini_backend.py`) and the model-listing module (`_models.py`) now receive explicit httpx clients with the truststore SSL context, instead of relying on global monkey-patch timing.

### Modified CLI: `src/mcp_coder/cli/commands/verify.py`

Test prompt failure shows a short summary + `--debug` hint instead of raw exception text. Classification is guarded: only connection-related exceptions (`OSError`, `ConnectionError`) are classified; other exceptions show `type(exc).__name__: str(exc)` directly.

### Preserved: `_ssl.py` (Safety Net)

The global `truststore.inject_into_ssl()` is kept as a belt-and-suspenders safety net for any code paths not using the new explicit clients (e.g., Gemini SDK internals).

## Design Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| `_http.py` placement | `langchain/` not `llm/` | Only langchain consumers exist; YAGNI |
| Diagnostics placement | Merged into `_exceptions.py` | All error handling in one module; <100 lines added |
| Proxy config | Env vars only | Standard mechanism, no config.toml duplication |
| Gemini | Document limitation, no custom HTTP | SDK does not support custom httpx clients; relies on global truststore |
| `_ssl.py` | Unchanged | Safety net for missed code paths |
| httpx dependency | Explicit in langchain extras | Already transitive, now pinned `>=0.27.0` |

## Files Changed

| File | Change |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_http.py` | **New** — httpx client factory with explicit truststore SSL |
| `src/mcp_coder/llm/providers/langchain/_exceptions.py` | **Modified** — add error classification + diagnostics |
| `src/mcp_coder/llm/providers/langchain/openai_backend.py` | **Modified** — pass `http_client` / `http_async_client` |
| `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` | **Modified** — pass `http_client` / `http_async_client` |
| `src/mcp_coder/llm/providers/langchain/gemini_backend.py` | **Modified** — add limitation comment (no functional change) |
| `src/mcp_coder/llm/providers/langchain/_models.py` | **Modified** — pass `http_client` to native SDK clients |
| `src/mcp_coder/cli/commands/verify.py` | **Modified** — improve test prompt failure message |
| `pyproject.toml` | **Modified** — add `httpx>=0.27.0` to langchain extras, mypy override |
| `tests/llm/providers/langchain/test_langchain_http.py` | **New** — tests for `_http.py` |
| `tests/llm/providers/langchain/test_langchain_diagnostics.py` | **New** — tests for diagnostics in `_exceptions.py` |
| `tests/llm/providers/langchain/test_langchain_openai.py` | **Modified** — verify http_client passed |
| `tests/llm/providers/langchain/test_langchain_anthropic.py` | **Modified** — verify http_client passed |
| `tests/llm/providers/langchain/test_langchain_gemini.py` | **Modified** — verify limitation documented |
| `tests/llm/providers/langchain/test_langchain_models.py` | **Modified** — verify http_client passed to SDK clients |
| `tests/cli/commands/test_verify_orchestration.py` | **Modified** — verify improved failure message |

## Implementation Steps (5 total)

1. **`_http.py`** — SSL context + httpx client factories + tests (checks lowercase proxy env vars too)
2. **`_exceptions.py`** — Error classification + diagnostics + tests (parameterized tests, lowercase proxy detection, iterative `_is_connection_reset` with depth limit)
3. **`openai_backend.py` + `anthropic_backend.py`** — Inject http clients into both backends + tests
4. **`_models.py` + `gemini_backend.py`** — Inject http clients into model listing (OpenAI/Anthropic) + document Gemini limitation + tests
5. **`verify.py` + `pyproject.toml`** — Guard classification (connection errors only), improve failure output + add httpx dep + tests
