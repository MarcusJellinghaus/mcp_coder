# Step 6: Inject HTTP Clients into Model Listing (`_models.py`)

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Pass explicit httpx clients to the native SDK clients (`openai.OpenAI`, `anthropic.Anthropic`) used in model-listing functions, so proxy/SSL works when listing models during verification.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/_models.py` | **Modify** |
| `tests/llm/providers/langchain/test_langchain_models.py` | **Modify** — add http_client tests |

## WHAT — Modified Functions

```python
def list_openai_models(api_key: str | None, endpoint: str | None = None) -> list[str]:
    # Now passes http_client to openai.OpenAI()

def list_anthropic_models(api_key: str | None) -> list[str]:
    # Now passes http_client to anthropic.Anthropic()

def list_gemini_models(api_key: str | None) -> list[str]:
    # Unchanged — relies on global truststore (see Step 5 investigation)
```

## HOW — Integration Points

- Import `create_http_client` from `._http`
- Pass `http_client=create_http_client()` to `openai.OpenAI()` and `anthropic.Anthropic()`
- Gemini: no change (SDK doesn't support custom HTTP clients; see Step 5)

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

## TESTS — Added to `test_langchain_models.py`

Write tests **first** (TDD), then implement.

### New Tests in `TestListOpenaiModels`

- `test_http_client_passed_to_openai_client` — mock `create_http_client`, verify `openai.OpenAI` called with `http_client=` kwarg

### New Tests in `TestListAnthropicModels`

- `test_http_client_passed_to_anthropic_client` — mock `create_http_client`, verify `anthropic.Anthropic` called with `http_client=` kwarg

Pattern: mock `_models.create_http_client` (since it's imported into `_models.py`), return a sentinel MagicMock, verify it appears in the SDK constructor call.

## LLM Prompt

```
Implement Step 6 of Issue #562 (see pr_info/steps/summary.md for context).

Modify `src/mcp_coder/llm/providers/langchain/_models.py` to:
- Import `create_http_client` from `._http`
- Pass `http_client=create_http_client()` to `openai.OpenAI()` in `list_openai_models`
- Pass `http_client=create_http_client()` to `anthropic.Anthropic()` in `list_anthropic_models`
- Leave `list_gemini_models` unchanged (SDK limitation, see Step 5)
- Keep existing `ensure_truststore()` calls as safety net

TDD approach: add tests to `tests/llm/providers/langchain/test_langchain_models.py` first,
then implement. Follow existing test patterns (mock SDK constructors, check kwargs).
Run all three code quality checks after implementation.
```
