# Step 1: Dependencies + Package Skeleton + Types

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup

## Goal
Add Textual dependencies, create the `icoder` package skeleton with all `__init__.py` files, and implement the core type definitions.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/__init__.py`
- `src/mcp_coder/icoder/core/__init__.py`
- `src/mcp_coder/icoder/core/types.py`
- `src/mcp_coder/icoder/core/commands/__init__.py`
- `src/mcp_coder/icoder/services/__init__.py`
- `src/mcp_coder/icoder/ui/__init__.py`
- `src/mcp_coder/icoder/ui/widgets/__init__.py`
- `tests/icoder/__init__.py`
- `tests/icoder/conftest.py`
- `tests/icoder/test_types.py`

### Modified files
- `pyproject.toml` — add dependencies

## WHAT — Main Functions and Signatures

### `core/types.py`

```python
@dataclass(frozen=True)
class Response:
    """Result of handle_input(). Rendered by UI layer."""
    text: str = ""
    clear_output: bool = False
    quit: bool = False
    send_to_llm: bool = False  # True = forward original input to LLM

@dataclass(frozen=True)
class Command:
    """Registered slash command definition."""
    name: str          # e.g. "/help"
    description: str   # Short help text
    handler: Callable[[list[str]], Response]  # handler(args) → Response

@dataclass
class EventEntry:
    """Single structured event for the event log."""
    t: float           # Seconds since session start
    event: str         # Event type name
    data: dict[str, object] = field(default_factory=dict)  # Arbitrary extra fields
```

### `pyproject.toml` changes

```toml
# In [project] dependencies:
"textual>=1.0.0",

# In dev dependencies:
"textual-dev>=1.0.0",
"pytest-textual-snapshot>=1.0.0",
```

## HOW — Integration Points

- `__init__.py` files are empty (package markers only)
- `conftest.py` is empty initially (fixtures added in later steps)
- Types use `from __future__ import annotations` for forward references
- `Response` and `EventEntry` are frozen/simple dataclasses — no methods beyond `__init__`

## DATA — Return Values

- `Response`: immutable dataclass, used by AppCore → UI
- `Command`: immutable dataclass, stored in registry
- `EventEntry`: mutable dataclass (for flexibility), serialized to JSONL

## Tests — `tests/icoder/test_types.py`

```python
# Test Response defaults
def test_response_defaults():
    r = Response()
    assert r.text == ""
    assert r.clear_output is False
    assert r.quit is False
    assert r.send_to_llm is False

# Test Response with text
def test_response_with_text():
    r = Response(text="hello")
    assert r.text == "hello"

# Test Response is frozen (immutable)
def test_response_frozen():
    r = Response()
    with pytest.raises(FrozenInstanceError):
        r.text = "modified"

# Test Command creation
def test_command_creation():
    cmd = Command(name="/help", description="Show help", handler=lambda args: Response())
    assert cmd.name == "/help"

# Test EventEntry creation and data field
def test_event_entry():
    e = EventEntry(t=0.01, event="input_received", data={"text": "/help"})
    assert e.event == "input_received"
    assert e.data["text"] == "/help"

# Test EventEntry default data is empty dict
def test_event_entry_default_data():
    e = EventEntry(t=0.0, event="test")
    assert e.data == {}
```

## LLM Prompt

```
You are implementing Step 1 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Add `textual>=1.0.0` to pyproject.toml dependencies
2. Add `textual-dev>=1.0.0` and `pytest-textual-snapshot>=1.0.0` to dev dependencies
3. Create the icoder package skeleton (all __init__.py files as listed)
4. Implement core/types.py with Response, Command, EventEntry dataclasses
5. Write tests in tests/icoder/test_types.py
6. Run pylint, mypy, pytest to verify all checks pass

Follow KISS — minimal dataclasses, no methods beyond defaults.
Use MCP tools for all file operations. Run all three code quality checks after changes.
```
