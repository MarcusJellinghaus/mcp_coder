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
    llm_text: str | None = None  # When set and send_to_llm=True, send this instead
    reset_session: bool = False  # True = reset LLM session (new conversation)


@dataclass(frozen=True)
class Command:
    """Registered slash command definition."""

    name: str  # e.g. "/help"
    description: str  # Short help text
    handler: Callable[[list[str]], Response]  # handler(args) → Response
    show_in_help: bool = True  # False hides from /help, still in autocomplete


@dataclass
class EventEntry:
    """Single structured event for the event log."""

    t: float  # Seconds since session start
    event: str  # Event type name
    data: dict[str, object] = field(default_factory=dict)  # Arbitrary extra fields
