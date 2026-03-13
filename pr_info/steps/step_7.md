# Step 7: Unify Text Backend via `_create_chat_model`

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 6 (TYPE_CHECKING guard must be in place).
> **Source**: Code review finding — decision 33.

## LLM Prompt

```
Implement Step 7 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: refactor _ask_text() in __init__.py to use the _create_chat_model()
factory instead of calling ask_openai/ask_gemini/ask_anthropic directly. Then
delete the old ask_* functions from each backend module. Update all affected
tests. Follow TDD — update tests first, then refactor.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/__init__.py` — rewrite `_ask_text()` to use `_create_chat_model()` + generic `.invoke()`
- `src/mcp_coder/llm/providers/langchain/openai_backend.py` — delete `ask_openai()` function
- `src/mcp_coder/llm/providers/langchain/gemini_backend.py` — delete `ask_gemini()` function
- `src/mcp_coder/llm/providers/langchain/anthropic_backend.py` — delete `ask_anthropic()` function

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_provider.py` — update tests for new `_ask_text` flow
- `tests/llm/providers/langchain/test_langchain_openai.py` — remove/update `ask_openai` tests, keep `create_openai_model` tests
- `tests/llm/providers/langchain/test_langchain_gemini.py` — remove/update `ask_gemini` tests, keep `create_gemini_model` tests
- `tests/llm/providers/langchain/test_langchain_anthropic.py` — remove/update `ask_anthropic` tests, keep `create_anthropic_model` tests

## WHAT

### __init__.py — rewrite `_ask_text()`

Replace the 3-way if/elif/else dispatch with a single path using `_create_chat_model()`:

```python
def _ask_text(
    question: str,
    config: dict[str, str | None],
    backend: str | None,
    session_id: str,
    timeout: int,
) -> LLMResponseDict:
    """Text-only backend dispatch using unified chat model factory."""
    from langchain_core.messages import AIMessage

    from ._utils import _to_lc_messages

    history = load_langchain_history(session_id)
    lc_messages = _to_lc_messages(history + [{"role": "human", "content": question}])

    chat_model = _create_chat_model(config)
    ai_msg = chat_model.invoke(lc_messages)

    text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

    raw: dict[str, object] = {
        "backend": backend,
        "model": config.get("model", ""),
        "response_content": text,
    }

    updated_history = history + [
        {"role": "human", "content": question},
        {"role": "ai", "content": text},
    ]
    store_langchain_history(session_id, updated_history)

    return LLMResponseDict(
        version=LLM_RESPONSE_VERSION,
        timestamp=datetime.now().isoformat(),
        text=text,
        session_id=session_id,
        method="api",
        provider="langchain",
        raw_response=raw,
    )
```

### Backend modules — delete `ask_*` functions

Each backend module keeps:
- `create_*_model()` — used by `_create_chat_model()`
- Module-level imports and error handling

Each backend module loses:
- `ask_openai()`, `ask_gemini()`, `ask_anthropic()` — no longer called

**Important**: The `ask_*` functions contain model-not-found error handling
(catching 404 errors and suggesting available models). This logic should be
preserved. Options:
1. Move 404 handling into `_ask_text()` as a generic try/except around `.invoke()`
2. Accept loss of model-suggestion hints (simpler)

Recommendation: Option 1 — wrap `.invoke()` in a try/except that catches the
404 pattern and calls `_list_models_for_backend()` from `_models.py`.

## HOW

### Error handling preservation

```python
try:
    ai_msg = chat_model.invoke(lc_messages)
except Exception as exc:
    exc_str = str(exc)
    if "404" in exc_str or "not_found" in exc_str.lower() or "NOT_FOUND" in exc_str:
        from ._models import list_openai_models, list_gemini_models, list_anthropic_models
        # Attempt to list available models and include in error message
        ...
    raise
```

### Integration points
- `_create_chat_model()` already handles backend dispatch — no changes needed
- `_to_lc_messages()` from `_utils.py` handles message conversion
- Session storage unchanged

## ALGORITHM

### `_ask_text` refactored flow
```
history = load_langchain_history(session_id)
lc_messages = _to_lc_messages(history + [human_message])
chat_model = _create_chat_model(config)
ai_msg = chat_model.invoke(lc_messages)   # may raise on 404
text = ai_msg.content
store history + [human, ai]
return LLMResponseDict(...)
```

### Model-not-found error handler
```
except Exception as exc:
    if looks_like_model_not_found(exc):
        hint = f"Model {model!r} not found."
        models = list_models_for_backend(backend, api_key, endpoint)
        hint += format_available_models(models)
        raise ValueError(hint) from exc
    raise
```

## DATA

### `raw_response` format change

Before (per-backend): varied dict structures from each `ask_*` function.

After (unified):
```python
{
    "backend": "openai",
    "model": "gpt-4",
    "response_content": "The answer is...",
}
```

**Note**: This is a minor breaking change in `raw_response` format. Since
`raw_response` is not part of the public API and is only used for debugging,
this is acceptable.

## TEST CASES

### `test_langchain_provider.py` — updates

Existing tests for `ask_langchain()` text mode should be updated to mock
`_create_chat_model` instead of individual `ask_openai`/etc:

```python
class TestAskLangchainTextMode:
    def test_text_mode_uses_create_chat_model(self):
        """_ask_text routes through _create_chat_model factory."""

    def test_text_mode_stores_history(self):
        """Session history updated after text response."""

    def test_text_mode_model_not_found_error(self):
        """404 from model invoke raises ValueError with hint."""
```

### Backend test files — updates

Remove tests for deleted `ask_*` functions. Keep tests for `create_*_model()`.

```python
# test_langchain_openai.py
# REMOVE: TestAskOpenai class (or rename to test create_openai_model)
# KEEP: tests for create_openai_model() if they exist

# Same pattern for gemini and anthropic
```

### Mock strategy
- Mock `_create_chat_model` to return a mock chat model with `.invoke()` 
- Mock chat model's `.invoke()` to return a mock AIMessage
- No real LLM calls needed
