# Step 3: Inject HTTP Clients into OpenAI Backend

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #562).

## Goal

Pass explicit httpx clients (with truststore SSL context) to `ChatOpenAI` and `AzureChatOpenAI`, so SSL/proxy works regardless of global monkey-patch timing.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/providers/langchain/openai_backend.py` | **Modify** |
| `tests/llm/providers/langchain/test_langchain_openai.py` | **Modify** — add http_client tests |

## WHAT — Modified Function

```python
def create_openai_model(
    model: str,
    api_key: str | None,
    endpoint: str | None = None,
    api_version: str | None = None,
    timeout: int = 30,
) -> ChatOpenAI | AzureChatOpenAI:
```

Signature unchanged. Internal change: passes `http_client` and `http_async_client` kwargs.

## HOW — Integration Points

- Import `create_http_client`, `create_async_http_client` from `._http`
- Pass to `ChatOpenAI(http_client=..., http_async_client=...)` and `AzureChatOpenAI(http_client=..., http_async_client=...)`

## ALGORITHM

```python
from ._http import create_async_http_client, create_http_client

def create_openai_model(model, api_key, endpoint=None, api_version=None, timeout=30):
    effective_api_key = os.getenv("OPENAI_API_KEY") or api_key
    secret_key = SecretStr(effective_api_key) if effective_api_key else None
    http_client = create_http_client()
    async_http_client = create_async_http_client()
    if api_version:
        return AzureChatOpenAI(..., http_client=http_client, http_async_client=async_http_client)
    return ChatOpenAI(..., http_client=http_client, http_async_client=async_http_client)
```

## DATA — No new return types

Same return type as before: `ChatOpenAI | AzureChatOpenAI`.

## TESTS — Added to `test_langchain_openai.py`

Write tests **first** (TDD), then implement.

### New Tests

**`TestCreateOpenaiModelHttpClient`**:
- `test_http_client_passed_to_chat_openai` — mock `create_http_client`, verify `ChatOpenAI` receives `http_client=` kwarg
- `test_http_async_client_passed_to_chat_openai` — mock `create_async_http_client`, verify `ChatOpenAI` receives `http_async_client=` kwarg
- `test_http_client_passed_to_azure_chat_openai` — same for Azure path (when `api_version` is set)
- `test_http_async_client_passed_to_azure_chat_openai` — same for Azure async

All tests mock both `_http.create_http_client` and `_http.create_async_http_client` to return sentinel `MagicMock` objects, then check the kwargs passed to the LangChain constructor.

## LLM Prompt

```
Implement Step 3 of Issue #562 (see pr_info/steps/summary.md for context).

Modify `src/mcp_coder/llm/providers/langchain/openai_backend.py` to:
- Import `create_http_client` and `create_async_http_client` from `._http`
- Pass `http_client` and `http_async_client` to both `ChatOpenAI` and `AzureChatOpenAI`

TDD approach: add tests to `tests/llm/providers/langchain/test_langchain_openai.py` first,
then implement. Follow existing test patterns (mock ChatOpenAI, check kwargs).
Run all three code quality checks after implementation.
```
