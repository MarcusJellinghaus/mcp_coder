# Step 9: Timeout Propagation + asyncio.TimeoutError Handling

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 8.
> **Source**: Code review round 2 — decisions 35, 42.

## LLM Prompt

```
Implement Step 9 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: (1) Add an asyncio.TimeoutError handler in prompt_llm() alongside
the existing TimeoutExpired handler. (2) Thread the timeout parameter through
_create_chat_model() to each backend factory so the caller's timeout value
reaches the HTTP request layer. Follow TDD — write tests first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/interface.py` — add `except asyncio.TimeoutError` block
- `src/mcp_coder/llm/providers/langchain/__init__.py` — pass `timeout` to `_create_chat_model()`
- `src/mcp_coder/llm/providers/langchain/openai_backend.py` — no changes (already accepts `timeout`)
- `src/mcp_coder/llm/providers/langchain/gemini_backend.py` — no changes (already accepts `timeout`)
- `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` — no changes (already accepts `timeout`)

### Files to modify (tests)
- `tests/llm/test_interface.py` — add `asyncio.TimeoutError` test
- `tests/llm/providers/langchain/test_langchain_provider.py` — add timeout forwarding test

## WHAT

### interface.py — `asyncio.TimeoutError` handler (Decision 35)

Add a parallel except block next to the existing `TimeoutExpired` handler in `prompt_llm()`:

```python
except asyncio.TimeoutError:
    logger.warning(
        "LLM request timed out (prompt length: %d, method: %s)",
        len(question),
        method,
    )
    raise
```

Import `asyncio` at the top of the file.

### __init__.py — pass timeout through (Decision 42)

Update `_create_chat_model()` to accept and forward `timeout`:

```python
def _create_chat_model(
    config: dict[str, str | None],
    timeout: int = 30,
) -> BaseChatModel:
```

Pass it through to each backend factory call:

```python
return create_openai_model(
    model=config.get("model") or "",
    api_key=config.get("api_key"),
    endpoint=config.get("endpoint"),
    api_version=config.get("api_version"),
    timeout=timeout,
)
```

Same pattern for `create_gemini_model(...)` and `create_anthropic_model(...)`.

Update both callers:
- `_ask_text()`: `chat_model = _create_chat_model(config, timeout=timeout)`
- `_ask_agent()`: `chat_model = _create_chat_model(config, timeout=timeout)`

## HOW

### interface.py integration
- Import `asyncio` at the top
- The `except asyncio.TimeoutError` block goes right after the existing `except TimeoutExpired` block
- Same log format for consistency

### __init__.py integration
- `_create_chat_model()` signature gains `timeout: int = 30` parameter
- Each `create_*_model()` call already accepts `timeout` — just pass it through
- Both `_ask_text()` and `_ask_agent()` already have `timeout` in scope

## ALGORITHM

### Timeout flow (after change)
```
ask_langchain(timeout=60)
  → _ask_text(timeout=60)  or  _ask_agent(timeout=60)
    → _create_chat_model(config, timeout=60)
      → create_openai_model(timeout=60)   # HTTP request timeout
    → agent: asyncio.wait_for(timeout=60)  # overall agent timeout
```

## DATA

No data structure changes.

## TEST CASES

### test_interface.py — asyncio.TimeoutError

```python
class TestPromptLLM:
    def test_asyncio_timeout_error_is_logged_and_reraised(self):
        """asyncio.TimeoutError from langchain agent is logged and re-raised."""
        # Patch ask_langchain to raise asyncio.TimeoutError
        # Assert asyncio.TimeoutError is raised
        # Assert logger.warning was called with prompt length and method
```

### test_langchain_provider.py — timeout forwarding

```python
class TestCreateChatModel:
    def test_timeout_forwarded_to_backend(self):
        """Caller's timeout reaches the backend factory."""
        # Patch create_openai_model
        # Call _create_chat_model(config, timeout=60)
        # Assert create_openai_model was called with timeout=60
```

### Mock strategy
- For interface test: patch `ask_langchain` to raise `asyncio.TimeoutError`
- For provider test: patch backend factory, assert `timeout` kwarg
