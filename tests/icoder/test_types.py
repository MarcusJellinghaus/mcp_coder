"""Tests for iCoder core type definitions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from mcp_coder.icoder.core.types import (
    Command,
    EventEntry,
    Response,
    TokenUsage,
    format_token_count,
)


def test_response_defaults() -> None:
    r = Response()
    assert r.text == ""
    assert r.clear_output is False
    assert r.quit is False
    assert r.send_to_llm is False
    assert r.reset_session is False


def test_response_with_text() -> None:
    r = Response(text="hello")
    assert r.text == "hello"


def test_response_frozen() -> None:
    r = Response()
    with pytest.raises(FrozenInstanceError):
        r.text = "modified"  # type: ignore[misc]


def test_command_creation() -> None:
    cmd = Command(
        name="/help", description="Show help", handler=lambda args: Response()
    )
    assert cmd.name == "/help"
    assert cmd.description == "Show help"


def test_event_entry() -> None:
    e = EventEntry(t=0.01, event="input_received", data={"text": "/help"})
    assert e.event == "input_received"
    assert e.data["text"] == "/help"


def test_event_entry_default_data() -> None:
    e = EventEntry(t=0.0, event="test")
    assert e.data == {}


def test_response_reset_session_default() -> None:
    r = Response()
    assert r.reset_session is False


def test_response_reset_session_explicit() -> None:
    r = Response(reset_session=True)
    assert r.reset_session is True


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, None),
        ({"llm_text": "override"}, "override"),
    ],
)
def test_response_llm_text(kwargs: dict[str, Any], expected: str | None) -> None:
    """Response.llm_text defaults to None, can be set."""
    r = Response(**kwargs)
    assert r.llm_text == expected


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, True),
        ({"show_in_help": False}, False),
    ],
)
def test_command_show_in_help(kwargs: dict[str, Any], expected: bool) -> None:
    """Command.show_in_help defaults to True, can be set to False."""
    cmd = Command(
        name="/test", description="Test", handler=lambda args: Response(), **kwargs
    )
    assert cmd.show_in_help == expected


# --- format_token_count tests ---


def test_format_token_count_zero() -> None:
    assert format_token_count(0) == "0"


def test_format_token_count_small() -> None:
    assert format_token_count(999) == "999"


@pytest.mark.parametrize(
    "n, expected",
    [
        (1200, "1.2k"),
        (5400, "5.4k"),
        (9949, "9.9k"),
        (9999, "10k"),
        (10000, "10k"),
        (123456, "123k"),
    ],
)
def test_format_token_count_k_range(n: int, expected: str) -> None:
    assert format_token_count(n) == expected


@pytest.mark.parametrize(
    "n, expected",
    [
        (1_000_000, "1.0M"),
        (1_200_000, "1.2M"),
        (9_949_999, "9.9M"),
        (9_999_999, "10M"),
        (12_000_000, "12M"),
    ],
)
def test_format_token_count_m_range(n: int, expected: str) -> None:
    assert format_token_count(n) == expected


# --- TokenUsage tests ---


def test_token_usage_initial_state() -> None:
    usage = TokenUsage()
    assert usage.last_input == 0
    assert usage.last_output == 0
    assert usage.total_input == 0
    assert usage.total_output == 0
    assert usage.has_data is False
    assert usage.display_text() == "\u21930 \u21910 | total: \u21930 \u21910"


def test_token_usage_single_update() -> None:
    usage = TokenUsage()
    usage.update(100, 50)
    assert usage.last_input == 100
    assert usage.last_output == 50
    assert usage.total_input == 100
    assert usage.total_output == 50
    assert usage.has_data is True


def test_token_usage_cumulative() -> None:
    usage = TokenUsage()
    usage.update(100, 50)
    usage.update(200, 80)
    assert usage.last_input == 200
    assert usage.last_output == 80
    assert usage.total_input == 300
    assert usage.total_output == 130


def test_token_usage_has_data_false_after_zero_update() -> None:
    usage = TokenUsage()
    usage.update(0, 0)
    assert usage._ever_updated is True  # noqa: SLF001
    assert usage.has_data is False


def test_token_usage_display_text() -> None:
    usage = TokenUsage()
    usage.update(1200, 800)
    assert usage.display_text() == "\u21931.2k \u2191800 | total: \u21931.2k \u2191800"
