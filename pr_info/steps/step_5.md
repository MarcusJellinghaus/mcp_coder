# Step 5: Investigate and Handle Gemini Backend

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Investigate whether `ChatGoogleGenerativeAI` or the underlying `google.genai.Client` supports custom HTTP client / SSL configuration. If supported, inject it. If not, document the limitation and rely on global truststore.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/gemini_backend.py` | **Modify** — add comment or `http_options` if supported |
| `tests/llm/providers/langchain/test_langchain_gemini.py` | **Modify** — add test for limitation/support |

## WHAT — Investigation Steps

1. Check if `ChatGoogleGenerativeAI` constructor accepts `http_client`, `transport`, or `http_options` kwargs
2. Check if `google.genai.Client` (used in `_models.py`) accepts `http_options` with proxy/SSL settings
3. Based on findings:
   - **If supported**: pass `http_client` or `http_options` with SSL context
   - **If not supported**: add a code comment documenting the limitation, keep relying on global `ensure_truststore()` via `_ssl.py`

## HOW — Integration Points

- If `ChatGoogleGenerativeAI` supports it: import from `._http`, pass client
- If not: add a docstring note explaining the limitation

## ALGORITHM — Expected Outcome (Likely: Not Supported)

```python
# google-genai SDK does not currently support custom httpx clients
# or SSL contexts via ChatGoogleGenerativeAI. Proxy/SSL for Gemini
# relies on global truststore injection via _ssl.ensure_truststore().
# See issue #562 for context.
def create_gemini_model(model, api_key, timeout=30):
    # ... existing code unchanged ...
```

If supported (less likely):
```python
from ._http import create_http_client
def create_gemini_model(model, api_key, timeout=30):
    kwargs["http_options"] = {"client": create_http_client()}  # or similar
```

## DATA — No new return types

Same return type: `ChatGoogleGenerativeAI`.

## TESTS — Added to `test_langchain_gemini.py`

### New Tests

**If not supported**:
- `test_gemini_limitation_documented` — verify the module docstring or function docstring mentions proxy/SSL limitation

**If supported**:
- `test_http_client_passed_to_gemini` — verify the appropriate kwarg is passed

## LLM Prompt

```
Implement Step 5 of Issue #562 (see pr_info/steps/summary.md for context).

Investigate whether `ChatGoogleGenerativeAI` (from langchain-google-genai) or
`google.genai.Client` supports custom HTTP clients, `http_options`, or SSL contexts.

Check the SDK documentation/source for supported constructor kwargs.

- If supported: inject `create_http_client()` from `._http`
- If not supported: add a clear code comment documenting the limitation,
  noting that Gemini relies on global truststore via `_ssl.ensure_truststore()`

Add appropriate test to `tests/llm/providers/langchain/test_langchain_gemini.py`.
Run all three code quality checks after implementation.
```
