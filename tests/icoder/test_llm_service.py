"""Tests for LLM service protocol and implementations."""

from __future__ import annotations

from typing import Iterator

import pytest

from mcp_coder.icoder.services.llm_service import (
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
