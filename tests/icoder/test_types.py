"""Tests for iCoder core type definitions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from mcp_coder.icoder.core.types import Command, EventEntry, Response


def test_response_defaults() -> None:
    r = Response()
    assert r.text == ""
    assert r.clear_output is False
    assert r.quit is False
    assert r.send_to_llm is False


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
