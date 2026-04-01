"""Tests for CommandHistory — in-session command history with Up/Down navigation."""

from __future__ import annotations

import pytest

from mcp_coder.icoder.core.command_history import CommandHistory


def test_up_empty_history_returns_none() -> None:
    """up() on fresh instance returns None."""
    h = CommandHistory()
    assert h.up("anything") is None


def test_down_empty_history_returns_none() -> None:
    """down() on fresh instance returns None."""
    h = CommandHistory()
    assert h.down() is None


def test_add_and_up_returns_entry() -> None:
    """Add one entry, up() returns it."""
    h = CommandHistory()
    h.add("hello")
    assert h.up("") == "hello"


def test_up_multiple_entries() -> None:
    """Add A, B, C; up() returns C, B, A in order."""
    h = CommandHistory()
    h.add("A")
    h.add("B")
    h.add("C")
    assert h.up("") == "C"
    assert h.up("") == "B"
    assert h.up("") == "A"


def test_up_at_oldest_returns_none() -> None:
    """After navigating to oldest, next up() returns None."""
    h = CommandHistory()
    h.add("A")
    h.add("B")
    assert h.up("") == "B"
    assert h.up("") == "A"
    assert h.up("") is None


def test_down_restores_entries_then_draft() -> None:
    """Navigate up fully, then down() walks forward, final down() returns draft."""
    h = CommandHistory()
    h.add("A")
    h.add("B")
    # Navigate up to oldest
    h.up("draft")
    h.up("draft")
    # Navigate down
    assert h.down() == "B"
    assert h.down() == "draft"


def test_down_at_newest_returns_none() -> None:
    """Without navigating up, down() returns None."""
    h = CommandHistory()
    h.add("A")
    assert h.down() is None


def test_draft_preservation() -> None:
    """Type 'draft text', up, then down past newest restores 'draft text'."""
    h = CommandHistory()
    h.add("old command")
    assert h.up("draft text") == "old command"
    assert h.down() == "draft text"


@pytest.mark.parametrize(
    "label, inputs, expected_count",
    [
        ("consecutive", ["A", "A"], 1),
        ("non_consecutive", ["A", "B", "A"], 3),
    ],
)
def test_duplicate_handling(label: str, inputs: list[str], expected_count: int) -> None:
    """Consecutive duplicates are suppressed; non-consecutive are kept."""
    h = CommandHistory()
    for text in inputs:
        h.add(text)
    # Count entries by navigating up
    count = 0
    while h.up("") is not None:
        count += 1
    assert (
        count == expected_count
    ), f"Case '{label}': expected {expected_count}, got {count}"


@pytest.mark.parametrize("blank_input", ["  ", "\t", "\n", ""])
def test_blank_input_rejected(blank_input: str) -> None:
    """Whitespace-only and empty inputs are rejected by add()."""
    h = CommandHistory()
    h.add(blank_input)
    assert h.up("") is None


def test_multiline_entry() -> None:
    """Multi-line string stored and returned intact."""
    h = CommandHistory()
    multiline = "line 1\nline 2\nline 3"
    h.add(multiline)
    assert h.up("") == multiline


def test_reset_cursor() -> None:
    """After navigating up, reset_cursor() puts cursor back at end."""
    h = CommandHistory()
    h.add("A")
    h.add("B")
    h.up("")
    h.reset_cursor()
    # Now down should return None (cursor at end)
    assert h.down() is None
    # And up should return the newest entry
    assert h.up("") == "B"


def test_add_resets_cursor() -> None:
    """Navigating up then adding new entry resets position."""
    h = CommandHistory()
    h.add("A")
    h.add("B")
    h.up("")  # cursor at B
    h.up("")  # cursor at A
    h.add("C")
    # After add, cursor should be at end; up returns newest
    assert h.up("") == "C"
