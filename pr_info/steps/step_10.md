# Step 10: Unify Session History Format

> **Context**: See `pr_info/steps/summary.md` for full issue context (#517).
> **Depends on**: Step 9.
> **Source**: Code review round 2 — decision 43.

## LLM Prompt

```
Implement Step 10 of issue #517 (MCP tool-use support for LangChain provider).
Read pr_info/steps/summary.md for context, then implement this step.

This step: unify the session history serialization format between text mode and
agent mode. Both paths should use LangChain's native model_dump() /
messages_from_dict() format. Update _ask_text() to serialize history via
model_dump() instead of manual {"role": ..., "content": ...} dicts. Update
_to_lc_messages or remove it if no longer needed. Follow TDD — update tests
first, then implement.
Do not modify any other files beyond what this step specifies.
```

## WHERE

### Files to modify
- `src/mcp_coder/llm/providers/langchain/__init__.py` — change `_ask_text()` history serialization to use `model_dump()`
- `src/mcp_coder/llm/providers/langchain/_utils.py` — update or remove `_to_lc_messages()` (may become unused)

### Files to modify (tests)
- `tests/llm/providers/langchain/test_langchain_provider.py` — update history assertions to expect `model_dump()` format
- `tests/llm/providers/langchain/test_langchain_agent_mode.py` — verify both paths now produce compatible format

## WHAT

### __init__.py — `_ask_text()` history changes

**Current** (text mode stores `"role"` keys):
```python
updated_history = history + [
    {"role": "human", "content": question},
    {"role": "ai", "content": text},
]
store_langchain_history(session_id, updated_history)
```

**After** (text mode stores LangChain native format via `model_dump()`):
```python
from langchain_core.messages import HumanMessage, messages_from_dict

# Load history using LangChain native deserialization
prior_messages = messages_from_dict(history) if history else []

# Build input messages
input_messages = prior_messages + [HumanMessage(content=question)]

chat_model = _create_chat_model(config, timeout=timeout)
ai_msg = chat_model.invoke(input_messages)

text = ai_msg.content if isinstance(ai_msg.content, str) else str(ai_msg.content)

# Serialize all messages via model_dump() — same format as agent mode
all_messages = input_messages + [ai_msg]
serialized: list[dict[str, Any]] = []
for msg in all_messages:
    if hasattr(msg, "model_dump"):
        serialized.append(cast(dict[str, Any], msg.model_dump()))
    else:
        serialized.append(cast(dict[str, Any], msg.dict()))
store_langchain_history(session_id, serialized)
```

### _utils.py — `_to_lc_messages()` removal

After this change, `_to_lc_messages()` is no longer used:
- Text mode now uses `messages_from_dict()` directly
- Agent mode already uses `messages_from_dict()` in `agent.py`

Remove `_to_lc_messages()`. If `_utils.py` is now empty (after `_ai_message_to_dict` was removed in Step 8), delete the file entirely.

## HOW

### Integration
- `messages_from_dict` is imported from `langchain_core.messages` (deferred import inside `_ask_text`)
- `model_dump()` / `.dict()` fallback follows the same pattern used in `agent.py`
- The `cast(dict[str, Any], ...)` pattern is already established in `agent.py`
- History load/store uses the same `load_langchain_history` / `store_langchain_history` — no changes to storage layer

### Backward compatibility
- Old sessions stored with `"role"` keys will fail `messages_from_dict()`. This is an accepted known limitation (Decision 20 from original plan). Users start fresh sessions.
- New sessions from both text mode and agent mode use the same format.

## ALGORITHM

### Unified _ask_text flow
```
history = load_langchain_history(session_id)
prior = messages_from_dict(history) if history else []
input_msgs = prior + [HumanMessage(content=question)]
ai_msg = _create_chat_model(config, timeout).invoke(input_msgs)
text = ai_msg.content
serialized = [msg.model_dump() for msg in input_msgs + [ai_msg]]
store_langchain_history(session_id, serialized)
return LLMResponseDict(text=text, ...)
```

## DATA

### History format (unified, both modes)

```python
# Stored via model_dump() — LangChain native format
[
    {"type": "human", "content": "What is 2+2?", "id": None, ...},
    {"type": "ai", "content": "4", "id": None, "tool_calls": [], ...},
]
```

Both text mode and agent mode now produce the same top-level structure. Agent mode messages may additionally include `tool_calls` on `AIMessage` entries and `ToolMessage` entries.

## TEST CASES

### test_langchain_provider.py — updated history tests

```python
class TestAskLangchain:
    def test_text_mode_stores_history_in_native_format(self):
        """_ask_text stores history via model_dump(), not manual role dicts."""
        # Call ask_langchain in text mode
        # Inspect store_langchain_history call
        # Assert each entry has "type" key (not "role")
        # Assert format is compatible with messages_from_dict()

    def test_text_mode_loads_native_history(self):
        """_ask_text deserializes prior history via messages_from_dict()."""
        # Pre-populate history with model_dump() format
        # Call ask_langchain — should work without errors
        # Assert chat_model.invoke received correct message objects
```

### test_langchain_agent_mode.py — format compatibility

```python
class TestAskLangchainAgentMode:
    def test_text_and_agent_history_format_compatible(self):
        """Both text and agent mode produce messages_from_dict()-compatible history."""
        # Verify both paths store dicts with "type" key
```

### Mock strategy
- Mock `messages_from_dict` to return LangChain message objects
- Mock `chat_model.invoke` to return a mock AIMessage with `model_dump()` method
- Assert `store_langchain_history` receives `model_dump()` format dicts
