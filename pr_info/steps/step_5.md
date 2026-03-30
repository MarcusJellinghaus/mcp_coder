# Step 5: AppCore — Central Input Routing

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Step 1 (types), Step 2 (event log), Step 3 (command registry), Step 4 (LLM service)

## Goal
Implement `AppCore` — the central coordinator that routes user input to slash commands or the LLM service, manages session state, and emits structured events. This is the "brain" of iCoder, fully testable without Textual.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/core/app_core.py`
- `tests/icoder/test_app_core.py`

### Modified files
- `tests/icoder/conftest.py` — add shared fixtures

## WHAT — Main Functions and Signatures

### `core/app_core.py`

```python
class AppCore:
    """Central input router. No Textual dependency."""

    def __init__(
        self,
        llm_service: LLMService,
        event_log: EventLog,
        registry: CommandRegistry | None = None,
    ) -> None:
        """Initialize with injected dependencies.
        
        Args:
            llm_service: LLM service for non-command input
            event_log: Structured event log
            registry: Command registry (default: create_default_registry())
        """

    def handle_input(self, text: str) -> Response:
        """Route user input to commands or flag for LLM streaming.
        
        - Slash commands: dispatch via registry, emit events, return Response
        - Empty input: ignore (return empty Response)
        - Other text: return Response(send_to_llm=True) so UI can start streaming
        
        Always emits "input_received" event.
        """

    def stream_llm(self, text: str) -> Iterator[StreamEvent]:
        """Stream LLM response for the given text.
        
        Called by UI layer after handle_input() returns send_to_llm=True.
        Emits events for each stream phase.
        Yields StreamEvent dicts for UI to render.
        """

    @property
    def session_id(self) -> str | None:
        """Current session ID from LLM service."""
```

## HOW — Integration Points

- Uses `CommandRegistry` from step 3 (default: `create_default_registry()`)
- Uses `EventLog` from step 2 for structured event emission
- Uses `LLMService` protocol from step 4 (injected — testable with `FakeLLMService`)
- `handle_input()` is synchronous — returns immediately
- `stream_llm()` is a synchronous generator — yields `StreamEvent` dicts
- The UI layer calls `handle_input()` first, then `stream_llm()` in a worker thread if needed

## ALGORITHM — Core Logic

```
handle_input(text):
    text = text.strip()
    if not text:
        return Response()
    self._event_log.emit("input_received", text=text)
    
    response = self._registry.dispatch(text)
    if response is not None:
        self._event_log.emit("command_matched", command=text.split()[0].lower())
        if response.text:
            self._event_log.emit("output_emitted", text=response.text)
        return response
    
    # Not a command → send to LLM
    return Response(send_to_llm=True)

stream_llm(text):
    self._event_log.emit("llm_request_start", text=text)
    for event in self._llm_service.stream(text):
        yield event
    self._event_log.emit("llm_request_end")
```

## DATA — Return Values

- `handle_input()` returns `Response`:
  - Empty input → `Response()` (no-op)
  - Slash command → `Response` from command handler
  - Free text → `Response(send_to_llm=True)`
- `stream_llm()` yields `StreamEvent` dicts from the LLM service
- `session_id` delegates to `llm_service.session_id`

## Tests — `tests/icoder/test_app_core.py`

```python
# Fixtures in conftest.py:
# - fake_llm: FakeLLMService instance
# - event_log: EventLog with tmp_path
# - app_core: AppCore(fake_llm, event_log)

# Test /help returns help text
def test_handle_help(app_core):
    response = app_core.handle_input("/help")
    assert "/help" in response.text
    assert not response.send_to_llm

# Test /unknown returns error
def test_handle_unknown_command(app_core):
    response = app_core.handle_input("/unknown")
    assert "Unknown command" in response.text

# Test free text returns send_to_llm=True
def test_handle_free_text(app_core):
    response = app_core.handle_input("hello world")
    assert response.send_to_llm is True

# Test /clear returns clear_output=True
def test_handle_clear(app_core):
    response = app_core.handle_input("/clear")
    assert response.clear_output is True

# Test /quit returns quit=True
def test_handle_quit(app_core):
    response = app_core.handle_input("/quit")
    assert response.quit is True

# Test empty input returns empty Response
def test_handle_empty_input(app_core):
    response = app_core.handle_input("")
    assert response.text == ""
    assert not response.send_to_llm

# Test whitespace-only input returns empty Response
def test_handle_whitespace_input(app_core):
    response = app_core.handle_input("   ")
    assert response.text == ""

# Test stream_llm yields events from LLM service
def test_stream_llm(app_core):
    events = list(app_core.stream_llm("hello"))
    assert any(e["type"] == "text_delta" for e in events)
    assert events[-1]["type"] == "done"

# Test event log records input_received for commands
def test_event_log_command(app_core, event_log):
    app_core.handle_input("/help")
    events = event_log.entries
    assert any(e.event == "input_received" for e in events)
    assert any(e.event == "command_matched" for e in events)

# Test event log records input_received for free text
def test_event_log_free_text(app_core, event_log):
    app_core.handle_input("hello")
    events = event_log.entries
    assert any(e.event == "input_received" for e in events)

# Test event log records llm_request events during streaming
def test_event_log_llm_stream(app_core, event_log):
    list(app_core.stream_llm("hello"))
    events = event_log.entries
    assert any(e.event == "llm_request_start" for e in events)
    assert any(e.event == "llm_request_end" for e in events)

# Test empty input does not emit events
def test_empty_input_no_events(app_core, event_log):
    app_core.handle_input("")
    assert len(event_log.entries) == 0

# Test session_id delegates to LLM service
def test_session_id(app_core):
    assert app_core.session_id is None

# Test state consistency across multiple inputs
def test_multiple_inputs(app_core, event_log):
    app_core.handle_input("/help")
    app_core.handle_input("question")
    list(app_core.stream_llm("question"))
    app_core.handle_input("/clear")
    assert len(event_log.entries) >= 4
```

### `tests/icoder/conftest.py`

```python
@pytest.fixture
def fake_llm():
    return FakeLLMService()

@pytest.fixture
def event_log(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    yield log
    log.close()

@pytest.fixture
def app_core(fake_llm, event_log):
    return AppCore(llm_service=fake_llm, event_log=event_log)
```

## LLM Prompt

```
You are implementing Step 5 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Add shared fixtures to tests/icoder/conftest.py (fake_llm, event_log, app_core)
2. Implement core/app_core.py with AppCore class
3. Write tests in tests/icoder/test_app_core.py
4. Run pylint, mypy, pytest to verify all checks pass

Key details:
- AppCore takes injected LLMService, EventLog, and optional CommandRegistry
- handle_input() returns Response — never blocks on LLM
- stream_llm() is a separate method called by UI when send_to_llm=True
- Empty input returns Response() without emitting events
- All slash commands emit "input_received" + "command_matched" events
- Free text emits "input_received" only (LLM events come from stream_llm)
- Tests use FakeLLMService — no real LLM calls

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
