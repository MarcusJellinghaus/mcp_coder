"""Tests for the autocomplete state module — pure unit tests, no Textual."""

from __future__ import annotations

import dataclasses

from mcp_coder.icoder.core.autocomplete_state import (
    AutocompleteState,
    compute_next_state,
)
from mcp_coder.icoder.core.command_registry import create_default_registry


def test_hidden_when_text_does_not_start_with_slash() -> None:
    """Empty string and non-slash text → visible=False, no matches."""
    registry = create_default_registry()
    for text in ["", "hello", "help", "h"]:
        state = compute_next_state(text, registry)
        assert state.visible is False
        assert state.matches == ()
        assert state.highlighted_index == -1


def test_visible_with_all_commands_when_text_is_slash() -> None:
    """'/' → visible=True, matches contains all 4 commands, highlighted_index=0."""
    registry = create_default_registry()
    state = compute_next_state("/", registry)
    assert state.visible is True
    names = {c.name for c in state.matches}
    assert names == {"/help", "/clear", "/quit", "/exit"}
    assert state.highlighted_index == 0


def test_visible_with_filtered_matches_on_he_prefix() -> None:
    """'/he' → visible=True, matches=(/help,), highlighted_index=0."""
    registry = create_default_registry()
    state = compute_next_state("/he", registry)
    assert state.visible is True
    assert len(state.matches) == 1
    assert state.matches[0].name == "/help"
    assert state.highlighted_index == 0


def test_visible_with_empty_matches_on_unknown_prefix() -> None:
    """'/xyz' → visible=True, matches=(), highlighted_index=-1."""
    registry = create_default_registry()
    state = compute_next_state("/xyz", registry)
    assert state.visible is True
    assert state.matches == ()
    assert state.highlighted_index == -1


def test_highlighted_index_zero_when_matches_present() -> None:
    """Any state with non-empty matches has highlighted_index == 0."""
    registry = create_default_registry()
    for text in ["/", "/he", "/cl", "/qu", "/ex"]:
        state = compute_next_state(text, registry)
        if state.matches:
            assert state.highlighted_index == 0


def test_highlighted_index_minus_one_when_no_matches() -> None:
    """Any state with empty matches has highlighted_index == -1."""
    registry = create_default_registry()
    for text in ["", "hello", "/xyz", "/zzz"]:
        state = compute_next_state(text, registry)
        if not state.matches:
            assert state.highlighted_index == -1


def test_state_is_frozen_and_replaced_not_mutated() -> None:
    """AutocompleteState is frozen — replacement is via new instance, not mutation."""
    registry = create_default_registry()
    state = compute_next_state("/", registry)
    # Frozen dataclass should raise on attribute assignment
    try:
        state.visible = False  # type: ignore[misc]
        raised = False
    except dataclasses.FrozenInstanceError:
        raised = True
    assert raised, "AutocompleteState should be frozen"
