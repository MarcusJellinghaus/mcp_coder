# Step 5: Auto-store iCoder sessions for Claude provider

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.
> **Depends on:** Step 4 (`--continue-session` flag). Without auto-storage, `--continue-session` finds nothing for Claude provider users.

## Goal

Auto-store LLM responses after each iCoder stream completes, so `--continue-session` works for Claude provider (langchain already auto-stores). Uses `ResponseAssembler` + `store_session()` — the same pattern as the `prompt` command.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/icoder/services/llm_service.py` | Modify — add `provider` property to protocol + implementations |
| `src/mcp_coder/icoder/core/app_core.py` | Modify — auto-store in `stream_llm()` |
| `tests/icoder/test_app_core.py` | Modify — add auto-storage test |

## WHAT

### `llm_service.py` — add `provider` property

`AppCore.stream_llm()` needs the provider to create `ResponseAssembler`. Add a read-only `provider` property to:

**`LLMService` protocol:**
```python
@property
def provider(self) -> str: ...
```

**`RealLLMService`:**
```python
@property
def provider(self) -> str:
    return self._provider
```

**`FakeLLMService`:**
```python
@property
def provider(self) -> str:
    return self._provider  # Already stored in __init__
```

Check if `FakeLLMService.__init__` already has a `provider` parameter — if not, add `provider: str = "claude"` with a `self._provider` field.

### `app_core.py` — auto-store in `stream_llm()`

Update `stream_llm()` to assemble and store the response after streaming:

```python
def stream_llm(self, text: str) -> Iterator[StreamEvent]:
    """Stream LLM response and auto-store for session continuation."""
    from ...llm.storage import store_session
    from ...llm.types import ResponseAssembler

    assembler = ResponseAssembler(self._llm_service.provider)
    self._event_log.emit("llm_request_start", text=text)

    for event in self._llm_service.stream(text):
        assembler.add(event)
        yield event

    self._event_log.emit("llm_request_end")

    # Auto-store response for --continue-session
    response_data = assembler.result()
    store_session(response_data, text)
```

This mirrors `prompt.py` lines 135–166 (ResponseAssembler + store_session pattern).

## HOW

- `ResponseAssembler` accumulates stream events and produces `LLMResponseDict` via `.result()`.
- `store_session()` writes to `.mcp-coder/responses/response_{timestamp}.json` (default path).
- The `yield` still passes events to the UI in real-time — storage happens after the stream ends.
- `provider` property is a simple accessor, no logic.

## Tests (TDD — write first)

### `test_app_core.py` — add one test:

1. **`test_stream_llm_stores_response`** — Create `AppCore` with `FakeLLMService`, consume `stream_llm("hello")`, then verify `store_session` was called with the assembled response. Use `monkeypatch` to mock `store_session` in `app_core` module.

### `test_llm_service.py` — add provider property tests:

2. **`test_fake_provider_property`** — `FakeLLMService().provider == "claude"` (default).
3. **`test_real_provider_property`** — `RealLLMService(provider="langchain").provider == "langchain"`.

## Commit

```
feat(icoder): auto-store sessions for --continue-session support (#765)
```

## LLM Prompt

```
Implement Step 5 from pr_info/steps/step_5.md (see pr_info/steps/summary.md for context).

Add provider property to LLMService protocol and implementations.
Update AppCore.stream_llm() to auto-store responses using ResponseAssembler + store_session.
Add tests. Run all code quality checks. Commit when green.
```
