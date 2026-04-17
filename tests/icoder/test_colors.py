"""Tests for color validation module."""

from __future__ import annotations

import pytest

from mcp_coder.icoder.core.colors import NAMED_COLORS, validate_color


@pytest.mark.parametrize("name,expected_hex", list(NAMED_COLORS.items()))
def test_validate_color_named(name: str, expected_hex: str) -> None:
    """Named colors resolve to their mapped hex values."""
    hex_color, error = validate_color(name)
    assert error is None
    assert hex_color == expected_hex


def test_validate_color_case_insensitive() -> None:
    """Named color lookup is case-insensitive."""
    hex_color, error = validate_color("Red")
    assert error is None
    assert hex_color == "#ef4444"


def test_validate_color_hex_with_hash() -> None:
    """6-digit hex with # prefix is accepted."""
    hex_color, error = validate_color("#f59e0b")
    assert error is None
    assert hex_color == "#f59e0b"


def test_validate_color_hex_without_hash() -> None:
    """6-digit hex without # prefix is accepted."""
    hex_color, error = validate_color("f59e0b")
    assert error is None
    assert hex_color == "#f59e0b"


def test_validate_color_3digit_hex() -> None:
    """3-digit hex falls through to Color.parse() fallback."""
    hex_color, error = validate_color("#f00")
    assert error is None
    assert hex_color is not None


def test_validate_color_css_fallback() -> None:
    """CSS color names are handled by Color.parse() fallback."""
    hex_color, error = validate_color("cornflowerblue")
    assert error is None
    assert hex_color is not None


def test_validate_color_invalid() -> None:
    """Invalid color string returns error tuple."""
    hex_color, error = validate_color("notacolor")
    assert hex_color is None
    assert error is not None
    assert "Unknown color" in error
    assert "notacolor" in error


def test_validate_color_default() -> None:
    """'default' maps to the grey default color."""
    hex_color, error = validate_color("default")
    assert error is None
    assert hex_color == "#666666"
