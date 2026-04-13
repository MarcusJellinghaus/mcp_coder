# Step 1: Add cancel infrastructure (constant + event)

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 1: Add the `STYLE_CANCELLED` constant and `_cancel_event` threading.Event to `ICoderApp`. Follow TDD — write tests first, then implement. Run all three code quality checks after changes.

## WHERE

- `src/mcp_coder/icoder/ui/app.py` — add constant and `__init__` change
- `tests/icoder/test_app_pilot.py` — add tests

## WHAT

### Constants

```python
STYLE_CANCELLED = "dim #e8a838"  # dim orange — visible but not alarming
```

Add near existing `STYLE_USER_INPUT` and `STYLE_TOOL_OUTPUT` constants.

### `ICoderApp.__init__` change

```python
import threading

def __init__(self, app_core: AppCore, *, format_tools: bool = True, **kwargs):
    ...
    self._cancel_event = threading.Event()
```

## HOW

- `import threading` at top of `app.py`
- Add `STYLE_CANCELLED` constant after existing style constants
- Add `self._cancel_event = threading.Event()` in `__init__` after `self._text_buffer`

## TESTS

### Test: `STYLE_CANCELLED` constant exists and is a string

```python
def test_style_cancelled_constant():
    from mcp_coder.icoder.ui.app import STYLE_CANCELLED
    assert isinstance(STYLE_CANCELLED, str)
    assert STYLE_CANCELLED  # not empty
```

### Test: `ICoderApp` has `_cancel_event` attribute

```python
async def test_cancel_event_exists(icoder_app):
    async with icoder_app.run_test():
        assert hasattr(icoder_app, '_cancel_event')
        assert isinstance(icoder_app._cancel_event, threading.Event)
        assert not icoder_app._cancel_event.is_set()
```

## DATA

- `STYLE_CANCELLED`: `str` — Rich style string for dim orange text
- `_cancel_event`: `threading.Event` — initially unset
