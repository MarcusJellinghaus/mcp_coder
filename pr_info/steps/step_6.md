# Step 6: Pilot Integration Tests for Autocomplete Behavior

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Write Textual pilot tests that verify the full autocomplete behavior end-to-end: visibility, filtering, key routing, event emission, and no regression on existing behavior.

## WHERE

| Action | File |
|--------|------|
| Create | `tests/icoder/test_autocomplete_pilot.py` |

## WHAT

Full pilot integration tests using `ICoderApp` with `FakeLLMService`. These tests exercise the complete stack: typing in `InputArea` → `CommandRegistry.filter_by_input` → `CommandAutocomplete` show/hide → event log emissions.

## Tests

```python
pytestmark = pytest.mark.textual_integration

# --- Visibility tests ---

async def test_typing_slash_shows_dropdown():
    """Type '/' → CommandAutocomplete becomes visible with all commands."""

async def test_typing_slash_cl_filters_to_clear():
    """Type '/cl' → dropdown shows only /clear."""

async def test_typing_slash_xyz_shows_no_matching():
    """Type '/xyz' → dropdown visible with '(no matching commands)' row."""

async def test_backspace_past_slash_hides_dropdown():
    """Type '/' then backspace → dropdown hidden."""

async def test_backspace_within_slash_emits_filtered():  # I4
    """Type '/help' then backspace → text='/he', emits autocomplete_filtered (NOT re-shown)."""

async def test_typing_clearx_keeps_dropdown_visible_no_matches():  # I5
    """Type '/clearx' → dropdown stays visible with empty matches ('(no matching commands)')."""

async def test_empty_input_no_dropdown():
    """Empty input → dropdown not visible."""

async def test_non_slash_input_no_dropdown():
    """Type 'hello' → dropdown not visible."""

# --- Key routing tests ---

async def test_tab_selects_and_inserts_command():
    """Type '/cl', press Tab → input contains '/clear ', dropdown hidden."""

async def test_escape_hides_dropdown_preserves_input():
    """Type '/he', press Escape → dropdown hidden, input still '/he'."""

async def test_enter_submits_with_slash_input():
    """Type '/help', press Enter → command executes (existing behavior), dropdown hidden."""

async def test_up_down_navigate_dropdown_when_visible():
    """With dropdown visible, Up/Down navigate highlight (not command history)."""

async def test_up_down_navigate_history_when_hidden():
    """With dropdown hidden, Up/Down still navigate command history (no regression)."""

async def test_tab_does_nothing_when_dropdown_hidden():
    """With no leading '/', Tab does not intercept (no regression)."""

# --- Event log tests ---

async def test_event_sequence_type_and_tab_select():
    """Type '/', '/h', '/he', Tab → events: shown, filtered(×2), selected, hidden(reason=selected)."""

async def test_event_sequence_type_and_escape():
    """Type '/', Escape → events: shown, hidden(reason=escape)."""

async def test_event_sequence_type_and_enter():
    """Type '/help', Enter → events: shown, filtered(×N), hidden(reason=submit)."""

async def test_event_sequence_backspace_past_slash():
    """Type '/', backspace → events: shown, hidden(reason=prefix_removed)."""
```

## HOW

Each test:
1. Creates `ICoderApp` with `FakeLLMService` + `EventLog(tmp_path)`
2. Uses `async with app.run_test() as pilot`
3. Inserts text into `InputArea` and presses keys via `pilot.press()`
4. Asserts on `CommandAutocomplete.is_visible`, option list contents, `InputArea.text`, and `EventLog.entries`

### Fixture pattern (same as existing `test_app_pilot.py`):

```python
@pytest.fixture
def icoder_app(fake_llm, event_log):
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)
```

Use the shared `fake_llm` and `event_log` fixtures from `tests/icoder/conftest.py`.

### Event log assertion helper:

```python
def event_names(event_log: EventLog) -> list[str]:
    return [e.event for e in event_log.entries]

def ac_events(event_log: EventLog) -> list[EventEntry]:
    return [e for e in event_log.entries if e.event.startswith("autocomplete_")]
```

## Commit

`test(icoder): add autocomplete pilot integration tests`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md for full context, then implement Step 6.

1. Create tests/icoder/test_autocomplete_pilot.py with all the pilot tests listed in step_6.md (including I4 and I5).
2. Use the existing conftest fixtures (fake_llm, event_log) and create an icoder_app fixture
3. Each test should use async with app.run_test() as pilot
4. Verify dropdown visibility via CommandAutocomplete.is_visible property
5. Verify event emissions via event_log.entries
6. Wiring lives in Steps 4 and 5 (InputArea + ICoderApp). If a wiring bug surfaces, fix it in those steps, not here.
7. Run all five quality checks — all must pass
8. Commit: "test(icoder): add autocomplete pilot integration tests"
```
