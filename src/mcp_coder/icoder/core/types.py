"""Core type definitions for the iCoder TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Quit:
    """Exit the application."""


@dataclass(frozen=True)
class ClearOutput:
    """Clear the output log display."""


@dataclass(frozen=True)
class OpenPicker:
    """Open the SessionPickerScreen for /load."""


@dataclass(frozen=True)
class ResetSession:
    """Reset the LLM session (start a new conversation).

    The actual reset (rotate event log, emit session_start) is performed
    inside ``AppCore.handle_input``; the UI treats this as a marker.
    """


@dataclass(frozen=True)
class SendToLLM:
    """Forward ``text`` to the LLM for streaming."""

    text: str


@dataclass(frozen=True)
class OutputText:
    """Append literal ``text`` to the output log."""

    text: str


@dataclass(frozen=True)
class RebuildOutput:
    """Re-render the output log from the new global tool-display tier.

    Dispatched by ``/display``; the UI applies it via
    ``OutputLog.set_tool_display_default`` (which both updates the default
    and wipes per-unit overrides — the "hard reset").
    """


Action = (
    Quit
    | ClearOutput
    | OpenPicker
    | ResetSession
    | SendToLLM
    | OutputText
    | RebuildOutput
)


@dataclass(frozen=True)
class Response:
    """Result of handle_input(). Rendered by UI layer.

    ``actions`` is a tuple of typed :data:`Action` instances dispatched in
    tuple order by the UI. An empty tuple (the default) means "do nothing".
    """

    actions: tuple[Action, ...] = ()


@dataclass(frozen=True)
class Command:
    """Registered slash command definition."""

    name: str  # e.g. "/help"
    description: str  # Short help text
    handler: Callable[[list[str]], Response]  # handler(args) → Response
    show_in_help: bool = True  # False hides from /help, still in autocomplete


@dataclass(frozen=True)
class LogSummary:
    """Inventory entry summarising one icoder JSONL log file."""

    path: Path
    timestamp: datetime
    provider: str | None
    n_turns: int
    first_prompt: str


@dataclass
class EventEntry:
    """Single structured event for the event log."""

    t: float  # Seconds since session start
    event: str  # Event type name
    data: dict[str, object] = field(default_factory=dict)  # Arbitrary extra fields


def format_token_count(n: int) -> str:
    """Format token count with compact suffix (k/M).

    Returns:
        Formatted string with compact suffix.
    """
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        k = n / 1000
        if k < 9.95:
            return f"{k:.1f}k"
        return f"{round(k)}k"
    if n < 1_000_000_000:
        m = n / 1_000_000
        if m < 9.95:
            return f"{m:.1f}M"
        return f"{round(m)}M"
    return f"{n // 1_000_000_000}B"


@dataclass
class TokenUsage:
    """Mutable dataclass tracking last-request and cumulative token counts."""

    last_input: int = 0
    last_output: int = 0
    total_input: int = 0
    total_output: int = 0
    last_cache_read: int = 0
    total_cache_read: int = 0
    _ever_updated: bool = field(default=False, repr=False)

    def update(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_read_input_tokens: int = 0,
    ) -> None:
        """Update with new token counts from a request."""
        self.last_input = input_tokens
        self.last_output = output_tokens
        self.total_input += input_tokens
        self.total_output += output_tokens
        self.last_cache_read = cache_read_input_tokens
        self.total_cache_read += cache_read_input_tokens
        self._ever_updated = True

    def display_text(self) -> str:
        """Build formatted display string for the status bar.

        Returns:
            Formatted string showing last and total token usage.
        """
        last = f"\u2193{format_token_count(self.last_input)} \u2191{format_token_count(self.last_output)}"
        if self.last_input > 0 and self.last_cache_read > 0:
            pct = round(self.last_cache_read / self.last_input * 100)
            last += f" cache:{pct}%"
        total = f"\u2193{format_token_count(self.total_input)} \u2191{format_token_count(self.total_output)}"
        if self.total_input > 0 and self.total_cache_read > 0:
            pct = round(self.total_cache_read / self.total_input * 100)
            total += f" cache:{pct}%"
        return f"{last} | total: {total}"

    @property
    def has_data(self) -> bool:
        """True if update() was called with non-zero totals."""
        return self._ever_updated and (self.total_input > 0 or self.total_output > 0)
