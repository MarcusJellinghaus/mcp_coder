"""Tests for iCoder core type definitions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from mcp_coder.icoder.core.types import (
    ClearOutput,
    Command,
    EventEntry,
    OpenPicker,
    OutputText,
    Quit,
    ResetSession,
    Response,
    SendToLLM,
    TokenUsage,
    format_token_count,
)


def test_response_default_empty_actions() -> None:
    """Response() defaults to an empty actions tuple."""
    r = Response()
    assert r.actions == ()


def test_response_with_actions() -> None:
    """Response stores the provided typed actions in order."""
    r = Response(actions=(ClearOutput(), ResetSession()))
    assert r.actions == (ClearOutput(), ResetSession())


def test_response_with_actions_frozen() -> None:
    """Response and its action instances are immutable and hashable."""
    r = Response(actions=(SendToLLM(text="hi"),))
    with pytest.raises(FrozenInstanceError):
        r.actions = ()  # type: ignore[misc]
    # Frozen action dataclasses are hashable
    assert hash(SendToLLM(text="hi")) == hash(SendToLLM(text="hi"))
    assert hash(Quit()) == hash(Quit())


def test_action_value_equality() -> None:
    """Same-valued frozen actions compare equal."""
    assert OutputText(text="x") == OutputText(text="x")
    assert SendToLLM(text="a") != SendToLLM(text="b")
    assert OpenPicker() == OpenPicker()


def test_send_to_llm_allowed_tools_defaults_none() -> None:
    """SendToLLM.allowed_tools defaults to None (no declaration)."""
    assert SendToLLM(text="x").allowed_tools is None


def test_send_to_llm_allowed_tools_round_trip() -> None:
    """SendToLLM stores the provided allowed_tools tuple verbatim."""
    action = SendToLLM(text="x", allowed_tools=("mcp__srv__a",))
    assert action.allowed_tools == ("mcp__srv__a",)


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


def test_token_usage_update_with_cache() -> None:
    usage = TokenUsage()
    usage.update(1000, 500, cache_read_input_tokens=450)
    assert usage.last_cache_read == 450
    assert usage.total_cache_read == 450


def test_token_usage_cumulative_cache() -> None:
    usage = TokenUsage()
    usage.update(1000, 500, cache_read_input_tokens=450)
    usage.update(2000, 800, cache_read_input_tokens=900)
    assert usage.last_cache_read == 900
    assert usage.total_cache_read == 1350


def test_token_usage_display_text_with_cache() -> None:
    usage = TokenUsage()
    usage.update(1200, 800, cache_read_input_tokens=540)
    text = usage.display_text()
    # last section: 540/1200 = 45%, total section: same numbers → 45%
    assert "cache:45%" in text
    # Ensure both last and total carry cache info
    last_part, total_part = text.split(" | total: ")
    assert "cache:45%" in last_part
    assert "cache:45%" in total_part


def test_token_usage_display_text_without_cache() -> None:
    usage = TokenUsage()
    usage.update(1200, 800)
    assert "cache:" not in usage.display_text()


def test_token_usage_display_text_mixed_cache() -> None:
    usage = TokenUsage()
    usage.update(1000, 500)  # no cache
    usage.update(2000, 800, cache_read_input_tokens=1000)
    text = usage.display_text()
    last_part, total_part = text.split(" | total: ")
    # last: 1000/2000 = 50%
    assert "cache:50%" in last_part
    # total: 1000/3000 = 33%
    assert "cache:33%" in total_part


def test_token_usage_cache_percentage_rounding() -> None:
    usage = TokenUsage()
    usage.update(1000, 500, cache_read_input_tokens=333)
    # 333/1000 = 33.3% → rounds to 33%
    assert "cache:33%" in usage.display_text()


def test_token_usage_display_text_zero_input_with_cache() -> None:
    usage = TokenUsage()
    usage.update(0, 0, cache_read_input_tokens=100)
    text = usage.display_text()
    assert "cache:" not in text
