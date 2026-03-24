# Step 1: Create `_http.py` — Shared httpx Client Factory

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Create a shared httpx client factory that builds clients with an **explicit** truststore-backed SSL context, eliminating dependency on global monkey-patching and initialization order. Both sync and async clients automatically respect `HTTPS_PROXY`/`HTTP_PROXY` env vars (httpx native behavior).

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_http.py` | **Create** |
| `tests/llm/providers/langchain/test_langchain_http.py` | **Create** |
| `tests/llm/providers/langchain/conftest.py` | **Modify** — add httpx mock if not installed |

## WHAT — Functions

```python
# src/mcp_coder/llm/providers/langchain/_http.py

def create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context using truststore if available, else default."""

def create_http_client() -> httpx.Client:
    """Create a sync httpx client with explicit truststore SSL context."""

def create_async_http_client() -> httpx.AsyncClient:
    """Create an async httpx client with explicit truststore SSL context."""
```

## HOW — Integration Points

- Imports: `ssl`, `logging`, and try-import for `truststore` and `httpx`
- `create_ssl_context()` is the shared core used by both factory functions
- DEBUG-level logging: proxy configured (yes/no based on `HTTPS_PROXY`/`https_proxy`/`HTTP_PROXY`/`http_proxy` presence), SSL context type (truststore vs default)
- **Security**: Never log env var values, only presence

## ALGORITHM — `create_ssl_context()`

```python
def create_ssl_context():
    try:
        import truststore
        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        logger.debug("SSL context: truststore (OS certificate store)")
        return ctx
    except ImportError:
        ctx = ssl.create_default_context()
        logger.debug("SSL context: default (certifi/system)")
        return ctx
```

## ALGORITHM — `create_http_client()`

```python
def create_http_client():
    ctx = create_ssl_context()
    proxy_configured = bool(
        os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    )
    logger.debug("httpx client: proxy_configured=%s", proxy_configured)
    return httpx.Client(verify=ctx)
```

## DATA — Return Values

| Function | Returns |
|----------|---------|
| `create_ssl_context()` | `ssl.SSLContext` |
| `create_http_client()` | `httpx.Client` |
| `create_async_http_client()` | `httpx.AsyncClient` |

## TESTS — `test_langchain_http.py`

Write tests **first** (TDD), then implement.

### Test Classes

**`TestCreateSslContext`**:
- `test_returns_truststore_context_when_available` — mock truststore, verify `truststore.SSLContext` called with `ssl.PROTOCOL_TLS_CLIENT`
- `test_returns_default_context_when_truststore_missing` — patch truststore import to fail, verify `ssl.create_default_context()` called
- `test_logs_truststore_context_type` — caplog check for "truststore" in debug log
- `test_logs_default_context_type` — caplog check for "default" in debug log

**`TestCreateHttpClient`**:
- `test_returns_httpx_client` — verify return type is `httpx.Client`
- `test_passes_ssl_context_as_verify` — mock `create_ssl_context`, verify `httpx.Client(verify=ctx)` called
- `test_logs_proxy_configured_true` — set `HTTPS_PROXY` env var, caplog check
- `test_logs_proxy_configured_true_lowercase` — set `https_proxy` env var, caplog check
- `test_logs_proxy_configured_false` — clear all proxy env vars (upper and lowercase), caplog check
- `test_never_logs_proxy_value` — set `HTTPS_PROXY=http://secret:pass@proxy:8080`, verify value NOT in logs

**`TestCreateAsyncHttpClient`**:
- `test_returns_httpx_async_client` — verify return type is `httpx.AsyncClient`
- `test_passes_ssl_context_as_verify` — same pattern as sync

### conftest.py Update

Add `httpx` to the session-scoped mock block if not installed:

```python
if "httpx" not in sys.modules:
    mocks["httpx"] = MagicMock()
```

## LLM Prompt

```
Implement Step 1 of Issue #562 (see pr_info/steps/summary.md for context).

Create `src/mcp_coder/llm/providers/langchain/_http.py` with three functions:
- `create_ssl_context()` → returns truststore-backed or default SSL context
- `create_http_client()` → returns httpx.Client with explicit SSL context
- `create_async_http_client()` → returns httpx.AsyncClient with explicit SSL context

TDD approach: write tests in `tests/llm/providers/langchain/test_langchain_http.py` first,
then implement the module. Update conftest.py if needed for httpx mocking.

Follow existing code patterns in `_ssl.py` and `test_langchain_ssl.py`.
Run all three code quality checks after implementation.
```
