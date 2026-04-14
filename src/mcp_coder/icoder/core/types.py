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
    _ever_updated: bool = field(default=False, repr=False)

    def update(self, input_tokens: int, output_tokens: int) -> None:
        """Update with new token counts from a request."""
        self.last_input = input_tokens
        self.last_output = output_tokens
        self.total_input += input_tokens
        self.total_output += output_tokens
        self._ever_updated = True

    def display_text(self) -> str:
        """Build formatted display string for the status bar.

        Returns:
            Formatted string showing last and total token usage.
        """
        last = f"\u2193{format_token_count(self.last_input)} \u2191{format_token_count(self.last_output)}"
        total = f"\u2193{format_token_count(self.total_input)} \u2191{format_token_count(self.total_output)}"
        return f"{last} | total: {total}"

    @property
    def has_data(self) -> bool:
        """True if update() was called with non-zero totals."""
        return self._ever_updated and (self.total_input > 0 or self.total_output > 0)
