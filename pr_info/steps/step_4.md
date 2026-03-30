# Step 4: LLM Service Protocol

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Step 1 (types)

## Goal
Create the services layer with a `Protocol` for LLM interaction, a real implementation wrapping `prompt_llm_stream()`, and a `FakeLLMService` for deterministic testing.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/services/llm_service.py`
- `tests/icoder/test_llm_service.py`

## WHAT — Main Functions and Signatures

### `services/llm_service.py`

```python
class LLMService(Protocol):
    """Protocol for LLM interaction. Enables DI for testing."""

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Stream LLM response events for the given input."""
        ...

    @property
    def session_id(self) -> str | None:
        """Current session ID (updated after each stream completes)."""
        ...


class RealLLMService:
    """Production LLM service wrapping prompt_llm_stream()."""

    def __init__(
        self,
        provider: str = "claude",
        session_id: str | None = None,
        execution_dir: str | None = None,
        mcp_config: str | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None: ...

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Call prompt_llm_stream() with stored config. Updates session_id from 'done' events."""

    @property
    def session_id(self) -> str | None: ...


class FakeLLMService:
    """Fake LLM for testing. Returns canned streaming responses."""

    def __init__(self, responses: list[list[StreamEvent]] | None = None) -> None:
        """Initialize with optional canned response sequences.
        
        Each call to stream() pops the next response from the list.
        Default: single response with one text_delta + done event.
        """

    def stream(self, question: str) -> Iterator[StreamEvent]:
        """Yield next canned response sequence."""

    @property
    def session_id(self) -> str | None: ...
```

## HOW — Integration Points

- `RealLLMService` imports and calls `prompt_llm_stream()` from `mcp_coder.llm.interface`
- `RealLLMService` uses `ResponseAssembler` from `mcp_coder.llm.types` to extract `session_id` from `done` events
- `FakeLLMService` is in the same module (not in tests/) so core tests can import it easily
- `StreamEvent` is re-exported from `mcp_coder.llm.types`

## ALGORITHM — Core Logic

```
# RealLLMService.stream():
def stream(self, question):
    for event in prompt_llm_stream(question, provider=self._provider,
            session_id=self._session_id, execution_dir=self._execution_dir,
            mcp_config=self._mcp_config, env_vars=self._env_vars):
        if event.get("type") == "done":
            sid = event.get("session_id")
            if isinstance(sid, str):
                self._session_id = sid
        yield event

# FakeLLMService.stream():
def stream(self, question):
    if self._responses:
        events = self._responses.pop(0)
    else:
        events = [{"type": "text_delta", "text": "fake response"}, {"type": "done"}]
    yield from events
```

## DATA — Return Values

- `stream()` yields `StreamEvent` dicts (same as `prompt_llm_stream()`)
- `session_id` property returns `str | None`
- `FakeLLMService` default response: `[{"type": "text_delta", "text": "fake response"}, {"type": "done"}]`

## Tests — `tests/icoder/test_llm_service.py`

```python
# Test FakeLLMService yields default response
def test_fake_default_response():
    service = FakeLLMService()
    events = list(service.stream("hello"))
    assert any(e["type"] == "text_delta" for e in events)
    assert events[-1]["type"] == "done"

# Test FakeLLMService yields canned responses in order
def test_fake_canned_responses():
    responses = [
        [{"type": "text_delta", "text": "first"}, {"type": "done"}],
        [{"type": "text_delta", "text": "second"}, {"type": "done"}],
    ]
    service = FakeLLMService(responses=responses)
    first = list(service.stream("q1"))
    second = list(service.stream("q2"))
    assert first[0]["text"] == "first"
    assert second[0]["text"] == "second"

# Test FakeLLMService with error event
def test_fake_error_response():
    responses = [[{"type": "error", "message": "boom"}, {"type": "done"}]]
    service = FakeLLMService(responses=responses)
    events = list(service.stream("q"))
    assert events[0]["type"] == "error"
    assert events[0]["message"] == "boom"

# Test FakeLLMService session_id is initially None
def test_fake_session_id_initially_none():
    service = FakeLLMService()
    assert service.session_id is None

# Test FakeLLMService updates session_id from done event
def test_fake_session_id_from_done():
    responses = [[{"type": "done", "session_id": "abc-123"}]]
    service = FakeLLMService(responses=responses)
    list(service.stream("q"))
    assert service.session_id == "abc-123"

# Test RealLLMService satisfies LLMService protocol (structural check)
def test_real_service_satisfies_protocol():
    """Verify RealLLMService is structurally compatible with LLMService."""
    service = RealLLMService(provider="claude")
    assert hasattr(service, "stream")
    assert hasattr(service, "session_id")

# Test RealLLMService.stream() delegates to prompt_llm_stream
def test_real_service_delegates_to_prompt_llm_stream(monkeypatch):
    """Patch prompt_llm_stream and verify RealLLMService.stream() calls it correctly."""
    fake_events = [{"type": "text_delta", "text": "hi"}, {"type": "done"}]
    def mock_stream(question, **kwargs):
        assert question == "hello"
        assert kwargs["provider"] == "claude"
        yield from fake_events
    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream", mock_stream
    )
    service = RealLLMService(provider="claude")
    events = list(service.stream("hello"))
    assert events == fake_events

# Test FakeLLMService satisfies LLMService protocol
def test_fake_service_satisfies_protocol():
    service = FakeLLMService()
    assert hasattr(service, "stream")
    assert hasattr(service, "session_id")
```

## LLM Prompt

```
You are implementing Step 4 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement services/llm_service.py with LLMService Protocol, RealLLMService, FakeLLMService
2. Write tests in tests/icoder/test_llm_service.py
3. Run pylint, mypy, pytest to verify all checks pass

Key details:
- LLMService is a Protocol (not ABC) with stream() and session_id
- RealLLMService wraps prompt_llm_stream() from mcp_coder.llm.interface
- RealLLMService updates its session_id when it sees a "done" event with session_id
- FakeLLMService accepts canned response sequences; pops one per stream() call
- FakeLLMService also updates session_id from done events (same logic)
- StreamEvent type is from mcp_coder.llm.types
- Tests do NOT call the real LLM — only test FakeLLMService and structural compliance

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
