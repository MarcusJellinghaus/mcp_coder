"""Pure autocomplete state module — no Textual dependency."""

from __future__ import annotations

from dataclasses import dataclass

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.types import Command


@dataclass(frozen=True)
class AutocompleteState:
    """Snapshot of autocomplete state for a given input text."""

    visible: bool
    matches: tuple[Command, ...]
    highlighted_index: int  # 0 when matches non-empty, -1 when empty


def compute_next_state(
    input_text: str,
    registry: CommandRegistry,
) -> AutocompleteState:
    """Compute the autocomplete state for the given input text.

    Pure function — no I/O, no Textual dependency.

    Returns:
        AutocompleteState with matches and visibility based on input text.
    """
    if not input_text.startswith("/"):
        return AutocompleteState(visible=False, matches=(), highlighted_index=-1)
    matches = tuple(registry.filter_by_input(input_text))
    return AutocompleteState(
        visible=True,
        matches=matches,
        highlighted_index=0 if matches else -1,
    )
