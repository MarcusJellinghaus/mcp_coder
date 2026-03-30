"""Core type definitions for the iCoder TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Response:
    """Result of handle_input(). Rendered by UI layer."""

    text: str = ""
    clear_output: bool = False
    quit: bool = False
    send_to_llm: bool = False  # True = forward original input to LLM


@dataclass(frozen=True)
class Command:
    """Registered slash command definition."""

    name: str  # e.g. "/help"
    description: str  # Short help text
    handler: Callable[[list[str]], Response]  # handler(args) → Response


@dataclass
class EventEntry:
    """Single structured event for the event log."""

    t: float  # Seconds since session start
    event: str  # Event type name
    data: dict[str, object] = field(default_factory=dict)  # Arbitrary extra fields
