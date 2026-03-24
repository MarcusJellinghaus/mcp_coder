# Step 4: Inject HTTP Clients into Model Listing + Document Gemini Limitation

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Pass explicit httpx clients to the native SDK clients (`openai.OpenAI`, `anthropic.Anthropic`) used in model-listing functions. Document the Gemini SDK limitation — it does not support custom HTTP clients, so it relies on global truststore.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_models.py` | **Modify** — inject http_client for OpenAI/Anthropic |
| `src/mcp_coder/llm/providers/langchain/gemini_backend.py` | **Modify** — add limitation comment |
| `tests/llm/providers/langchain/test_langchain_models.py` | **Modify** — add http_client tests |
| `tests/llm/providers/langchain/test_langchain_gemini.py` | **Modify** — add limitation documentation test |

## WHAT — Modified Functions

### `_models.py`

```python
def list_openai_models(api_key: str | None, endpoint: str | None = None) -> list[str]:
    # Now passes http_client to openai.OpenAI()

def list_anthropic_models(api_key: str | None) -> list[str]:
    # Now passes http_client to anthropic.Anthropic()

def list_gemini_models(api_key: str | None) -> list[str]:
    # Unchanged — relies on global truststore
```

### `gemini_backend.py`

Add a limitation comment to `create_gemini_model`:

```python
# Gemini SDK (google-genai) does not support custom httpx clients or SSL
# contexts. Proxy/SSL relies on global truststore via _ssl.ensure_truststore().
# See issue #562.
def create_gemini_model(model, api_key, timeout=30):
    # ... existing code unchanged ...
```

## HOW — Integration Points

- `_models.py`: Import `create_http_client` from `._http`, pass to `openai.OpenAI()` and `anthropic.Anthropic()`
- `gemini_backend.py`: Add comment only, no functional change
- Gemini model listing in `_models.py`: unchanged (relies on global truststore)

## ALGORITHM — `list_openai_models` (updated)

```python
from ._http import create_http_client

def list_openai_models(api_key, endpoint=None):
    import openai
    ensure_truststore()  # kept as safety net
    client = openai.OpenAI(
        api_key=api_key if api_key else None,
        base_url=endpoint if endpoint else None,
        http_client=create_http_client(),
    )
    return sorted(m.id for m in client.models.list())
```

## ALGORITHM — `list_anthropic_models` (updated)

```python
def list_anthropic_models(api_key):
    import anthropic
    ensure_truststore()  # kept as safety net
    client = anthropic.Anthropic(
        api_key=api_key if api_key else None,
        http_client=create_http_client(),
    )
    return sorted(m.id for m in client.models.list())
```

## DATA — No new return types

Same return types: `list[str]` for all functions.

## TESTS

Write tests **first** (TDD), then implement.

### New Tests in `test_langchain_models.py`

**In `TestListOpenaiModels`**:
- `test_http_client_passed_to_openai_client` — mock `create_http_client`, verify `openai.OpenAI` called with `http_client=` kwarg

**In `TestListAnthropicModels`**:
- `test_http_client_passed_to_anthropic_client` — mock `create_http_client`, verify `anthropic.Anthropic` called with `http_client=` kwarg

### New Tests in `test_langchain_gemini.py`

- `test_gemini_limitation_documented` — verify the function or module contains the limitation comment (inspect source or docstring)

Pattern: mock `_models.create_http_client` (since it's imported into `_models.py`), return a sentinel MagicMock, verify it appears in the SDK constructor call.

## LLM Prompt

```
Implement Step 4 of Issue #562 (see pr_info/steps/summary.md for context).

Two parts:

1. Modify `src/mcp_coder/llm/providers/langchain/_models.py`:
   - Import `create_http_client` from `._http`
   - Pass `http_client=create_http_client()` to `openai.OpenAI()` in `list_openai_models`
   - Pass `http_client=create_http_client()` to `anthropic.Anthropic()` in `list_anthropic_models`
   - Leave `list_gemini_models` unchanged (SDK limitation)
   - Keep existing `ensure_truststore()` calls as safety net

2. Modify `src/mcp_coder/llm/providers/langchain/gemini_backend.py`:
   - Add a comment documenting that Gemini SDK does not support custom httpx
     clients or SSL contexts, relying on global truststore instead

TDD approach: add tests first, then implement.
Run all three code quality checks after implementation.
```
