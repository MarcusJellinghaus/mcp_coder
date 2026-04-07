"""Pilot integration tests for autocomplete behavior."""

from __future__ import annotations

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import EventEntry
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.icoder.ui.app import ICoderApp
from mcp_coder.icoder.ui.widgets.command_autocomplete import CommandAutocomplete
from mcp_coder.icoder.ui.widgets.input_area import InputArea

pytestmark = pytest.mark.textual_integration


@pytest.fixture
def icoder_app(fake_llm: FakeLLMService, event_log: EventLog) -> ICoderApp:
    """Create ICoderApp with fake dependencies."""
    app_core = AppCore(llm_service=fake_llm, event_log=event_log)
    return ICoderApp(app_core)


def ac_events(event_log: EventLog) -> list[EventEntry]:
    """Return only autocomplete-related events."""
    return [e for e in event_log.entries if e.event.startswith("autocomplete_")]


def ac_event_names(event_log: EventLog) -> list[str]:
    """Return names of autocomplete-related events."""
    return [e.event for e in event_log.entries if e.event.startswith("autocomplete_")]


# --- Visibility tests ---


async def test_typing_slash_shows_dropdown(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/' -> CommandAutocomplete becomes visible with all commands."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        assert dropdown.option_count >= 3  # /clear, /help, /quit


async def test_typing_slash_cl_filters_to_clear(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/cl' -> dropdown shows only /clear."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/cl")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        assert dropdown.option_count == 1
        option = dropdown.get_option_at_index(0)
        assert option.id == "/clear"


async def test_typing_slash_xyz_shows_no_matching(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/xyz' -> dropdown visible with '(no matching commands)' row."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/xyz")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        assert dropdown.option_count == 1
        option = dropdown.get_option_at_index(0)
        assert option.disabled


async def test_backspace_past_slash_hides_dropdown(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/' then backspace -> dropdown hidden."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        await pilot.press("backspace")
        await pilot.pause()
        assert not dropdown.is_visible


async def test_backspace_within_slash_emits_filtered(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/cl' then backspace -> text='/', emits autocomplete_filtered."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/cl")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        await pilot.press("backspace")
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        assert dropdown.is_visible
        assert input_area.text == "/"
        names = ac_event_names(event_log)
        assert "autocomplete_filtered" in names


async def test_typing_clearx_keeps_dropdown_visible_no_matches(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/clearx' -> dropdown stays visible with empty matches."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/clearx")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        assert dropdown.option_count == 1
        option = dropdown.get_option_at_index(0)
        assert option.disabled


async def test_empty_input_no_dropdown(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Empty input -> dropdown not visible."""
    async with icoder_app.run_test() as pilot:
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert not dropdown.is_visible


async def test_non_slash_input_no_dropdown(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type 'hello' -> dropdown not visible."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert not dropdown.is_visible


# --- Key routing tests ---


async def test_tab_selects_and_inserts_command(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/cl', press Tab -> input contains '/clear ', dropdown hidden."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/cl")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        await pilot.press("tab")
        await pilot.pause()
        assert not dropdown.is_visible
        assert input_area.text == "/clear "


async def test_escape_hides_dropdown_preserves_input(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/he', press Escape -> dropdown hidden, input still '/he'."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/he")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        await pilot.press("escape")
        await pilot.pause()
        assert not dropdown.is_visible
        assert input_area.text == "/he"


async def test_enter_submits_with_slash_input(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/help', press Enter -> command executes, dropdown hidden."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/help")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        await pilot.press("enter")
        await pilot.pause()
        assert not dropdown.is_visible
        assert input_area.text == ""


async def test_up_down_navigate_dropdown_when_visible(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """With dropdown visible, Up/Down navigate highlight (not command history)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        dropdown = icoder_app.query_one(CommandAutocomplete)
        assert dropdown.is_visible
        initial_highlighted = dropdown.highlighted
        await pilot.press("down")
        await pilot.pause()
        assert dropdown.highlighted != initial_highlighted or dropdown.option_count == 1
        key_events = [
            e for e in event_log.entries if e.event == "autocomplete_key_routed"
        ]
        assert any(e.data.get("key") == "down" for e in key_events)


async def test_up_down_navigate_history_when_hidden(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """With dropdown hidden, Up/Down still navigate command history."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        # Submit something to history first
        input_area.insert("hello")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        # Now Up should recall from history, not route to dropdown
        await pilot.press("up")
        await pilot.pause()
        assert input_area.text == "hello"


async def test_tab_does_nothing_when_dropdown_hidden(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """With no leading '/', Tab does not intercept (no regression)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("hello")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        # Tab should not have inserted a command
        ac_selected = [
            e for e in event_log.entries if e.event == "autocomplete_selected"
        ]
        assert len(ac_selected) == 0


# --- Event log tests ---


async def test_event_sequence_type_and_tab_select(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/', '/h', '/he', Tab -> events: shown, filtered(x2), selected, hidden."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        input_area.insert("h")
        await pilot.pause()
        input_area.insert("e")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        names = ac_event_names(event_log)
        assert names[0] == "autocomplete_shown"
        assert "autocomplete_filtered" in names
        assert "autocomplete_selected" in names
        assert "autocomplete_hidden" in names
        # Hidden reason should be "selected"
        hidden_events = [
            e for e in ac_events(event_log) if e.event == "autocomplete_hidden"
        ]
        assert any(e.data.get("reason") == "selected" for e in hidden_events)


async def test_event_sequence_type_and_escape(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/', Escape -> events: shown, hidden(reason=escape)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        names = ac_event_names(event_log)
        assert "autocomplete_shown" in names
        assert "autocomplete_hidden" in names
        hidden_events = [
            e for e in ac_events(event_log) if e.event == "autocomplete_hidden"
        ]
        assert any(e.data.get("reason") == "escape" for e in hidden_events)


async def test_event_sequence_type_and_enter(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/help', Enter -> events: shown, filtered(xN), hidden(reason=submit)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/help")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        names = ac_event_names(event_log)
        assert "autocomplete_shown" in names
        assert "autocomplete_hidden" in names
        hidden_events = [
            e for e in ac_events(event_log) if e.event == "autocomplete_hidden"
        ]
        assert any(e.data.get("reason") == "submit" for e in hidden_events)


async def test_event_sequence_backspace_past_slash(
    icoder_app: ICoderApp, event_log: EventLog
) -> None:
    """Type '/', backspace -> events: shown, hidden(reason=prefix_removed)."""
    async with icoder_app.run_test() as pilot:
        input_area = icoder_app.query_one(InputArea)
        input_area.focus()
        await pilot.pause()
        input_area.insert("/")
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        names = ac_event_names(event_log)
        assert "autocomplete_shown" in names
        assert "autocomplete_hidden" in names
        hidden_events = [
            e for e in ac_events(event_log) if e.event == "autocomplete_hidden"
        ]
        assert any(e.data.get("reason") == "prefix_removed" for e in hidden_events)
