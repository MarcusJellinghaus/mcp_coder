# Step 4: Inject HTTP Clients into Anthropic Backend

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Pass explicit httpx clients (with truststore SSL context) to `ChatAnthropic`, so SSL/proxy works regardless of global monkey-patch timing.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` | **Modify** |
| `tests/llm/providers/langchain/test_langchain_anthropic.py` | **Modify** — add http_client tests |

## WHAT — Modified Function

```python
def create_anthropic_model(
    model: str,
    api_key: str | None,
    timeout: int = 30,
) -> ChatAnthropic:
```

Signature unchanged. Internal change: passes `http_client` and `http_async_client` kwargs.

## HOW — Integration Points

- Import `create_http_client`, `create_async_http_client` from `._http`
- Add `http_client` and `http_async_client` to the `kwargs` dict passed to `ChatAnthropic`

## ALGORITHM

```python
from ._http import create_async_http_client, create_http_client

def create_anthropic_model(model, api_key, timeout=30):
    effective_api_key = os.getenv("ANTHROPIC_API_KEY") or api_key
    kwargs = {
        "model_name": model,
        "default_request_timeout": float(timeout),
        "http_client": create_http_client(),
        "http_async_client": create_async_http_client(),
    }
    if effective_api_key:
        kwargs["anthropic_api_key"] = SecretStr(effective_api_key)
    return ChatAnthropic(**kwargs)
```

## DATA — No new return types

Same return type: `ChatAnthropic`.

## TESTS — Added to `test_langchain_anthropic.py`

Write tests **first** (TDD), then implement.

### New Tests

**`TestCreateAnthropicModelHttpClient`**:
- `test_http_client_passed_to_chat_anthropic` — mock `create_http_client`, verify `ChatAnthropic` receives `http_client=` kwarg
- `test_http_async_client_passed_to_chat_anthropic` — mock `create_async_http_client`, verify `ChatAnthropic` receives `http_async_client=` kwarg

Pattern: mock `_http.create_http_client` → returns sentinel MagicMock, check `ChatAnthropic` constructor kwargs.

## LLM Prompt

```
Implement Step 4 of Issue #562 (see pr_info/steps/summary.md for context).

Modify `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` to:
- Import `create_http_client` and `create_async_http_client` from `._http`
- Pass `http_client` and `http_async_client` to `ChatAnthropic`

TDD approach: add tests to `tests/llm/providers/langchain/test_langchain_anthropic.py` first,
then implement. Follow existing test patterns (mock ChatAnthropic, check kwargs).
Run all three code quality checks after implementation.
```
