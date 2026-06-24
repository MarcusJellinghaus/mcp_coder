"""Typed dataclasses representing renderer output actions.

Each dataclass corresponds to one kind of stream event that the
``StreamEventRenderer`` can produce.  Consumers do ``isinstance``
dispatch to decide how to display each action.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A fragment of assistant text."""

    text: str


@dataclass(frozen=True)
class ToolStart:
    """A tool invocation has begun."""

    display_name: str  # e.g. "workspace > read_file"
    raw_name: str  # e.g. "mcp__mcp-workspace__read_file"
    args: dict[str, object]  # raw args from stream event


@dataclass(frozen=True)
class ToolResult:
    """A tool invocation has completed."""

    name: str  # display name of the tool
    raw_name: str  # raw tool name (matches ToolStart raw key for FIFO lookup)
    output_lines: list[str]  # possibly truncated output
    total_lines: int  # original line count
    truncated: bool  # whether output was truncated
    is_error: bool = False  # whether the tool reported an error
    duration_ms: int | None = None  # elapsed time in ms, or None if unpaired


@dataclass(frozen=True)
class ErrorMessage:
    """An error occurred during streaming."""

    message: str


@dataclass(frozen=True)
class StreamDone:
    """The stream has finished."""


RenderAction = TextChunk | ToolStart | ToolResult | ErrorMessage | StreamDone
