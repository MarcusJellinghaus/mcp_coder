"""Tests for AppCore — central input routing."""

from __future__ import annotations

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.event_log import EventLog


def test_handle_help(app_core: AppCore) -> None:
    """Test /help returns help text."""
    response = app_core.handle_input("/help")
    assert "/help" in response.text
    assert not response.send_to_llm


def test_handle_unknown_command(app_core: AppCore) -> None:
    """Test /unknown returns error."""
    response = app_core.handle_input("/unknown")
    assert "Unknown command" in response.text


def test_handle_free_text(app_core: AppCore) -> None:
    """Test free text returns send_to_llm=True."""
    response = app_core.handle_input("hello world")
    assert response.send_to_llm is True


def test_handle_clear(app_core: AppCore) -> None:
    """Test /clear returns clear_output=True."""
    response = app_core.handle_input("/clear")
    assert response.clear_output is True


def test_handle_quit(app_core: AppCore) -> None:
    """Test /quit returns quit=True."""
    response = app_core.handle_input("/quit")
    assert response.quit is True


def test_handle_empty_input(app_core: AppCore) -> None:
    """Test empty input returns empty Response."""
    response = app_core.handle_input("")
    assert response.text == ""
    assert not response.send_to_llm


def test_handle_whitespace_input(app_core: AppCore) -> None:
    """Test whitespace-only input returns empty Response."""
    response = app_core.handle_input("   ")
    assert response.text == ""


def test_stream_llm(app_core: AppCore) -> None:
    """Test stream_llm yields events from LLM service."""
    events = list(app_core.stream_llm("hello"))
    assert any(e["type"] == "text_delta" for e in events)
    assert events[-1]["type"] == "done"


def test_event_log_command(app_core: AppCore, event_log: EventLog) -> None:
    """Test event log records input_received for commands."""
    app_core.handle_input("/help")
    events = event_log.entries
    assert any(e.event == "input_received" for e in events)
    assert any(e.event == "command_matched" for e in events)


def test_event_log_free_text(app_core: AppCore, event_log: EventLog) -> None:
    """Test event log records input_received for free text."""
    app_core.handle_input("hello")
    events = event_log.entries
    assert any(e.event == "input_received" for e in events)


def test_event_log_llm_stream(app_core: AppCore, event_log: EventLog) -> None:
    """Test event log records llm_request events during streaming."""
    list(app_core.stream_llm("hello"))
    events = event_log.entries
    assert any(e.event == "llm_request_start" for e in events)
    assert any(e.event == "llm_request_end" for e in events)


def test_empty_input_no_events(app_core: AppCore, event_log: EventLog) -> None:
    """Test empty input does not emit events."""
    app_core.handle_input("")
    assert len(event_log.entries) == 0


def test_session_id(app_core: AppCore) -> None:
    """Test session_id delegates to LLM service."""
    assert app_core.session_id is None


def test_multiple_inputs(app_core: AppCore, event_log: EventLog) -> None:
    """Test state consistency across multiple inputs."""
    app_core.handle_input("/help")
    app_core.handle_input("question")
    list(app_core.stream_llm("question"))
    app_core.handle_input("/clear")
    assert len(event_log.entries) >= 4
