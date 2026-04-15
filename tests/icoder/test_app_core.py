"""Tests for AppCore — central input routing."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_coder.icoder.core.app_core import AppCore
from mcp_coder.icoder.core.command_history import CommandHistory
from mcp_coder.icoder.core.event_log import EventLog
from mcp_coder.icoder.core.types import TokenUsage
from mcp_coder.icoder.env_setup import RuntimeInfo
from mcp_coder.icoder.services.llm_service import FakeLLMService
from mcp_coder.utils.mcp_verification import MCPServerInfo


def test_handle_help(app_core: AppCore) -> None:
    """Test /help returns help text."""
    response = app_core.handle_input("/help")
    assert "/help" in response.text
    assert not response.send_to_llm


def test_help_includes_keyboard_shortcuts(app_core: AppCore) -> None:
    """Test /help output contains keyboard shortcuts section."""
    response = app_core.handle_input("/help")
    assert "Keyboard shortcuts:" in response.text
    assert "Insert newline" in response.text


def test_handle_unknown_command(app_core: AppCore) -> None:
    """Test /unknown returns error."""
    response = app_core.handle_input("/unknown")
    assert "Unknown command" in response.text


def test_handle_free_text(app_core: AppCore) -> None:
    """Test free text returns send_to_llm=True."""
    response = app_core.handle_input("hello world")
    assert response.send_to_llm is True


def test_handle_clear(app_core: AppCore) -> None:
    """Test /clear returns clear_output=True and reset_session=True."""
    response = app_core.handle_input("/clear")
    assert response.clear_output is True
    assert response.reset_session is True


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


def test_runtime_info_none_by_default(app_core: AppCore) -> None:
    """Verify runtime_info is None when not provided."""
    assert app_core.runtime_info is None


def test_runtime_info_injected(fake_llm: FakeLLMService, event_log: EventLog) -> None:
    """Create AppCore with a RuntimeInfo instance, verify property returns it."""
    info = RuntimeInfo(
        mcp_coder_version="1.0.0",
        python_version="3.12.0",
        claude_code_version="1.2.3",
        tool_env_path="/tool",
        project_venv_path="/proj/.venv",
        project_dir="/proj",
        env_vars={"MCP_CODER_VENV_PATH": "/tool/bin"},
        mcp_servers=[
            MCPServerInfo(name="srv", path=Path("/fake/srv"), version="1.0"),
        ],
    )
    core = AppCore(llm_service=fake_llm, event_log=event_log, runtime_info=info)
    assert core.runtime_info is info
    assert core.runtime_info.mcp_coder_version == "1.0.0"


def test_command_history_survives_clear(app_core: AppCore) -> None:
    """command_history persists across /clear — entries are not lost."""
    app_core.command_history.add("first")
    app_core.command_history.add("second")
    app_core.handle_input("/clear")
    # History should still recall entries added before /clear
    assert app_core.command_history.up("") == "second"
    assert app_core.command_history.up("second") == "first"


def test_command_history_property(app_core: AppCore) -> None:
    """AppCore exposes a CommandHistory instance."""
    assert isinstance(app_core.command_history, CommandHistory)


def test_clear_resets_session(
    event_log: EventLog,
) -> None:
    """Test /clear resets the LLM session (session_id becomes None)."""
    fake_llm = FakeLLMService(
        responses=[
            [
                {"type": "text_delta", "text": "hello"},
                {"type": "done", "session_id": "sess-123"},
            ]
        ]
    )
    core = AppCore(llm_service=fake_llm, event_log=event_log)
    # Stream to populate session_id
    list(core.stream_llm("hi"))
    assert fake_llm.session_id == "sess-123"

    # /clear should reset session
    core.handle_input("/clear")
    assert fake_llm.session_id is None


def test_clear_emits_session_reset_event(
    app_core: AppCore, event_log: EventLog
) -> None:
    """Test /clear emits a session_reset event."""
    app_core.handle_input("/clear")
    assert any(e.event == "session_reset" for e in event_log.entries)


def test_stream_llm_stores_response(
    app_core: AppCore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """stream_llm() auto-stores response via store_session."""
    stored_calls: list[tuple[object, str]] = []

    def fake_store(response_data: object, prompt: str, **kwargs: object) -> str:
        stored_calls.append((response_data, prompt))
        return "/fake/path.json"

    monkeypatch.setattr(
        "mcp_coder.icoder.core.app_core.store_session",
        fake_store,
    )
    events = list(app_core.stream_llm("hello"))
    assert len(events) > 0
    assert len(stored_calls) == 1
    response_data, prompt = stored_calls[0]
    assert prompt == "hello"
    assert isinstance(response_data, dict)
    assert response_data["provider"] == "claude"


def test_token_usage_initial_state(app_core: AppCore) -> None:
    """token_usage property exists and starts at zero."""
    usage = app_core.token_usage
    assert isinstance(usage, TokenUsage)
    assert usage.last_input == 0
    assert usage.last_output == 0
    assert usage.total_input == 0
    assert usage.total_output == 0
    assert usage.has_data is False


def test_stream_llm_updates_token_usage(event_log: EventLog) -> None:
    """stream_llm() extracts usage from done event and updates token_usage."""
    fake_llm = FakeLLMService(
        responses=[
            [
                {"type": "text_delta", "text": "hi"},
                {
                    "type": "done",
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                },
            ]
        ]
    )
    core = AppCore(llm_service=fake_llm, event_log=event_log)
    list(core.stream_llm("hello"))
    assert core.token_usage.last_input == 100
    assert core.token_usage.last_output == 50
    assert core.token_usage.total_input == 100
    assert core.token_usage.total_output == 50
    assert core.token_usage.has_data is True


def test_stream_llm_cumulative_tokens(event_log: EventLog) -> None:
    """Two streams with usage data accumulate totals."""
    fake_llm = FakeLLMService(
        responses=[
            [
                {"type": "text_delta", "text": "a"},
                {
                    "type": "done",
                    "usage": {"input_tokens": 100, "output_tokens": 50},
                },
            ],
            [
                {"type": "text_delta", "text": "b"},
                {
                    "type": "done",
                    "usage": {"input_tokens": 200, "output_tokens": 80},
                },
            ],
        ]
    )
    core = AppCore(llm_service=fake_llm, event_log=event_log)
    list(core.stream_llm("q1"))
    list(core.stream_llm("q2"))
    assert core.token_usage.last_input == 200
    assert core.token_usage.last_output == 80
    assert core.token_usage.total_input == 300
    assert core.token_usage.total_output == 130


def test_stream_llm_no_usage_data(app_core: AppCore) -> None:
    """Stream with done event but no usage key leaves token_usage unchanged."""
    list(app_core.stream_llm("hello"))
    assert app_core.token_usage.has_data is False
    assert app_core.token_usage.total_input == 0


def test_handle_input_returns_llm_text(app_core: AppCore) -> None:
    """When a command sets llm_text, it's available on the response."""
    from mcp_coder.icoder.core.types import Command, Response

    app_core.registry.add_command(
        Command(
            name="/skill_test",
            description="test skill",
            handler=lambda args: Response(send_to_llm=True, llm_text="override"),
        )
    )
    response = app_core.handle_input("/skill_test")
    assert response.send_to_llm is True
    assert response.llm_text == "override"
