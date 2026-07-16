"""Tests for LLM service protocol and implementations."""

from __future__ import annotations

from typing import Iterator

import pytest

from mcp_coder.icoder.services.llm_service import (
    ICODER_LLM_TIMEOUT_SECONDS,
    FakeLLMService,
    LLMService,
    RealLLMService,
)
from mcp_coder.llm.types import StreamEvent


def test_fake_default_response() -> None:
    """FakeLLMService yields default response when no canned responses provided."""
    service = FakeLLMService()
    events = list(service.stream("hello"))
    assert any(e["type"] == "text_delta" for e in events)
    assert events[-1]["type"] == "done"


def test_fake_canned_responses() -> None:
    """FakeLLMService yields canned responses in order."""
    responses: list[list[StreamEvent]] = [
        [{"type": "text_delta", "text": "first"}, {"type": "done"}],
        [{"type": "text_delta", "text": "second"}, {"type": "done"}],
    ]
    service = FakeLLMService(responses=responses)
    first = list(service.stream("q1"))
    second = list(service.stream("q2"))
    assert first[0]["text"] == "first"
    assert second[0]["text"] == "second"


def test_fake_error_response() -> None:
    """FakeLLMService can yield error events."""
    responses: list[list[StreamEvent]] = [
        [{"type": "error", "message": "boom"}, {"type": "done"}],
    ]
    service = FakeLLMService(responses=responses)
    events = list(service.stream("q"))
    assert events[0]["type"] == "error"
    assert events[0]["message"] == "boom"


def test_fake_session_id_initially_none() -> None:
    """FakeLLMService session_id is initially None."""
    service = FakeLLMService()
    assert service.session_id is None


def test_fake_session_id_from_done() -> None:
    """FakeLLMService updates session_id from done event."""
    responses: list[list[StreamEvent]] = [
        [{"type": "done", "session_id": "abc-123"}],
    ]
    service = FakeLLMService(responses=responses)
    list(service.stream("q"))
    assert service.session_id == "abc-123"


def test_real_service_satisfies_protocol() -> None:
    """Verify RealLLMService is structurally compatible with LLMService."""
    service = RealLLMService(provider="claude")
    assert hasattr(service, "stream")
    assert hasattr(service, "session_id")
    assert isinstance(service, LLMService)


def test_real_service_delegates_to_prompt_llm_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch prompt_llm_stream and verify RealLLMService.stream() calls it correctly."""
    fake_events: list[StreamEvent] = [
        {"type": "text_delta", "text": "hi"},
        {"type": "done"},
    ]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        assert question == "hello"
        assert kwargs["provider"] == "claude"
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude")
    events = list(service.stream("hello"))
    assert events == fake_events


def test_fake_service_satisfies_protocol() -> None:
    """FakeLLMService satisfies LLMService protocol."""
    service = FakeLLMService()
    assert hasattr(service, "stream")
    assert hasattr(service, "session_id")
    assert isinstance(service, LLMService)


def test_real_service_updates_session_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService updates session_id from done events."""
    fake_events: list[StreamEvent] = [
        {"type": "done", "session_id": "new-session-42"},
    ]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude")
    assert service.session_id is None
    list(service.stream("hello"))
    assert service.session_id == "new-session-42"


def test_icoder_timeout_constant_value() -> None:
    """ICODER_LLM_TIMEOUT_SECONDS is 300 (5 minutes)."""
    assert ICODER_LLM_TIMEOUT_SECONDS == 300


def test_real_llm_service_passes_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService.stream() passes timeout=ICODER_LLM_TIMEOUT_SECONDS to prompt_llm_stream."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude")
    list(service.stream("hello"))
    assert captured_kwargs["timeout"] == ICODER_LLM_TIMEOUT_SECONDS


def test_fake_reset_session() -> None:
    """FakeLLMService.reset_session() clears session_id to None."""
    responses: list[list[StreamEvent]] = [
        [{"type": "done", "session_id": "session-1"}],
    ]
    service = FakeLLMService(responses=responses)
    list(service.stream("q"))
    assert service.session_id == "session-1"
    service.reset_session()
    assert service.session_id is None


def test_real_reset_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService.reset_session() clears session_id to None."""
    fake_events: list[StreamEvent] = [
        {"type": "done", "session_id": "real-session-99"},
    ]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude")
    list(service.stream("hello"))
    assert service.session_id == "real-session-99"
    service.reset_session()
    assert service.session_id is None


def test_protocol_has_reset_session() -> None:
    """Both implementations still satisfy LLMService protocol after adding reset_session."""
    assert isinstance(FakeLLMService(), LLMService)
    assert isinstance(RealLLMService(provider="claude"), LLMService)


def test_real_set_session_id_replaces_existing() -> None:
    """RealLLMService.set_session_id() replaces an existing session_id."""
    service = RealLLMService(provider="claude", session_id="abc")
    service.set_session_id("xyz")
    assert service.session_id == "xyz"


def test_fake_set_session_id_sets_value() -> None:
    """FakeLLMService.set_session_id() sets session_id."""
    service = FakeLLMService()
    service.set_session_id("abc")
    assert service.session_id == "abc"


def test_real_set_session_id_to_none() -> None:
    """RealLLMService.set_session_id(None) clears session_id."""
    service = RealLLMService(provider="claude", session_id="abc")
    service.set_session_id(None)
    assert service.session_id is None


def test_fake_set_session_id_to_none() -> None:
    """FakeLLMService.set_session_id(None) clears session_id."""
    service = FakeLLMService()
    service.set_session_id("abc")
    service.set_session_id(None)
    assert service.session_id is None


def test_protocol_has_set_session_id() -> None:
    """Both implementations satisfy LLMService protocol after adding set_session_id."""
    assert isinstance(FakeLLMService(), LLMService)
    assert isinstance(RealLLMService(provider="claude"), LLMService)


def test_fake_provider_property_default() -> None:
    """FakeLLMService.provider defaults to 'claude'."""
    service = FakeLLMService()
    assert service.provider == "claude"


def test_fake_provider_property_custom() -> None:
    """FakeLLMService.provider returns custom value."""
    service = FakeLLMService(provider="langchain")
    assert service.provider == "langchain"


def test_real_provider_property() -> None:
    """RealLLMService.provider returns the configured provider."""
    service = RealLLMService(provider="langchain")
    assert service.provider == "langchain"


def test_real_llm_service_custom_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService passes custom timeout to prompt_llm_stream."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude", timeout=600)
    list(service.stream("hello"))
    assert captured_kwargs["timeout"] == 600


def test_real_llm_service_passes_tools_from_mcp_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService passes tools from mcp_manager to prompt_llm_stream."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]
    fake_tools = ["tool_a", "tool_b"]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )

    class FakeMCPManager:
        def tools(self) -> list[str]:
            return fake_tools

    service = RealLLMService(provider="langchain", mcp_manager=FakeMCPManager())  # type: ignore[arg-type]
    list(service.stream("hello"))
    assert captured_kwargs["tools"] is fake_tools


def test_real_llm_service_no_manager_passes_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService passes tools=None when no mcp_manager is set."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="langchain")
    list(service.stream("hello"))
    assert captured_kwargs["tools"] is None


def test_real_llm_service_passes_project_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService passes project_dir to prompt_llm_stream."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude", project_dir="/tmp/my-project")
    list(service.stream("hello"))
    assert captured_kwargs["project_dir"] == "/tmp/my-project"


def test_real_llm_service_project_dir_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RealLLMService passes project_dir=None when not provided (backward compat)."""
    captured_kwargs: dict[str, object] = {}
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured_kwargs.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )
    service = RealLLMService(provider="claude")
    list(service.stream("hello"))
    assert captured_kwargs["project_dir"] is None


def test_fake_falls_back_to_default_after_canned_exhausted() -> None:
    """FakeLLMService falls back to default after canned responses are exhausted."""
    responses: list[list[StreamEvent]] = [
        [{"type": "text_delta", "text": "canned"}, {"type": "done"}],
    ]
    service = FakeLLMService(responses=responses)
    first = list(service.stream("q1"))
    assert first[0]["text"] == "canned"
    # Second call should use default
    second = list(service.stream("q2"))
    assert second[0]["text"] == "fake response"


class _FakeMCPManager:
    """Minimal MCP manager stand-in: tools are their own canonical names."""

    def __init__(self, tool_names: list[str]) -> None:
        self._tools = list(tool_names)

    def tools(self) -> list[str]:
        return self._tools

    def canonical_name(self, tool: str) -> str | None:
        return tool


def _capture_tools_stream(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, object]
) -> None:
    """Monkeypatch prompt_llm_stream to record kwargs['tools']."""
    fake_events: list[StreamEvent] = [{"type": "done"}]

    def mock_stream(question: str, **kwargs: object) -> Iterator[StreamEvent]:
        captured.update(kwargs)
        yield from fake_events

    monkeypatch.setattr(
        "mcp_coder.icoder.services.llm_service.prompt_llm_stream",
        mock_stream,
    )


def test_enforce_subset_declaration_narrows_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enforce=True + subset declaration -> only declared tool passed; excluded absent."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__keep", "mcp__srv__drop"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=True,
    )
    list(service.stream("hello", allowed_tools=("mcp__srv__keep",)))
    assert captured["tools"] == ["mcp__srv__keep"]
    assert "mcp__srv__drop" not in captured["tools"]


def test_enforce_all_non_mcp_declaration_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enforce=True + all-non-MCP declaration -> zero tools (fail-closed)."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__keep", "mcp__srv__drop"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=True,
    )
    list(service.stream("hello", allowed_tools=("Bash", "Read")))
    assert captured["tools"] == []


def test_enforce_without_allowed_tools_passes_full_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enforce=True + no allowed_tools -> full tool list (no narrowing)."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__a", "mcp__srv__b"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=True,
    )
    list(service.stream("hello"))
    assert captured["tools"] == ["mcp__srv__a", "mcp__srv__b"]


def test_enforce_disabled_passes_full_list_despite_declaration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enforce=False + declaration present -> full list (no narrowing)."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__a", "mcp__srv__b"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=False,
    )
    list(service.stream("hello", allowed_tools=("mcp__srv__a",)))
    assert captured["tools"] == ["mcp__srv__a", "mcp__srv__b"]


def test_enforce_wildcard_token_yields_warning_and_restricts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enforce=True + wildcard token -> permission_warning yielded; tools restricted."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__a", "mcp__srv__b"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=True,
    )
    events = list(service.stream("hello", allowed_tools=("mcp__srv__a", "mcp__srv__*")))
    warnings = [e for e in events if e["type"] == "permission_warning"]
    assert len(warnings) == 1
    assert isinstance(warnings[0]["message"], str)
    # Restricted to the exact-matched tool, not the full list.
    assert captured["tools"] == ["mcp__srv__a"]


def test_enforce_does_not_mutate_manager_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After enforced stream, manager.tools() still returns the full list."""
    captured: dict[str, object] = {}
    _capture_tools_stream(monkeypatch, captured)
    manager = _FakeMCPManager(["mcp__srv__a", "mcp__srv__b"])
    service = RealLLMService(
        provider="langchain",
        mcp_manager=manager,  # type: ignore[arg-type]
        enforce_skill_tools=True,
    )
    list(service.stream("hello", allowed_tools=("mcp__srv__a",)))
    assert manager.tools() == ["mcp__srv__a", "mcp__srv__b"]


def test_fake_service_records_last_allowed_tools() -> None:
    """FakeLLMService(enforce_skill_tools=True) records allowed_tools; never filters."""
    service = FakeLLMService(enforce_skill_tools=True)
    list(service.stream("q", allowed_tools=("x",)))
    assert service.last_allowed_tools == ("x",)


def test_fake_service_last_allowed_tools_initially_none() -> None:
    """FakeLLMService.last_allowed_tools defaults to None before any stream."""
    service = FakeLLMService()
    assert service.last_allowed_tools is None


def test_fake_service_stream_ignores_allowed_tools_content() -> None:
    """FakeLLMService.stream still yields canned responses regardless of allowed_tools."""
    responses: list[list[StreamEvent]] = [
        [{"type": "text_delta", "text": "first"}, {"type": "done"}],
    ]
    service = FakeLLMService(responses=responses)
    events = list(service.stream("q", allowed_tools=("mcp__srv__a",)))
    assert events[0]["text"] == "first"
    assert service.last_allowed_tools == ("mcp__srv__a",)


def test_services_satisfy_protocol_after_widening() -> None:
    """Both implementations still satisfy LLMService protocol after stream widening."""
    assert isinstance(FakeLLMService(enforce_skill_tools=True), LLMService)
    assert isinstance(
        RealLLMService(provider="claude", enforce_skill_tools=True), LLMService
    )


@pytest.mark.claude_cli_integration
def test_real_llm_service_stream_smoke() -> None:
    """Smoke test: RealLLMService.stream() works end-to-end with the live Claude CLI."""
    service = RealLLMService(provider="claude", timeout=60)
    events = list(service.stream("Reply 'ok'."))
    assert any(e["type"] == "text_delta" for e in events)
    assert any(e["type"] == "done" for e in events)
    assert service.session_id
