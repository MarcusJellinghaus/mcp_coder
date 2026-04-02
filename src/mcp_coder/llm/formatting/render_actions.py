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
    raw_name: str  # e.g. "mcp__workspace__read_file"
    inline_args: str | None  # formatted args when ≤2 keys, else None
    block_args: list[tuple[str, str]]  # [(key, json_value), ...] when >2 keys


@dataclass(frozen=True)
class ToolResult:
    """A tool invocation has completed."""

    name: str  # display name of the tool
    output_lines: list[str]  # possibly truncated output
    total_lines: int  # original line count
    truncated: bool  # whether output was truncated


@dataclass(frozen=True)
class ErrorMessage:
    """An error occurred during streaming."""

    message: str


@dataclass(frozen=True)
class StreamDone:
    """The stream has finished."""


RenderAction = TextChunk | ToolStart | ToolResult | ErrorMessage | StreamDone
