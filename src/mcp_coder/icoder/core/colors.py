"""Color validation for iCoder prompt border."""

from __future__ import annotations

import re

from textual.color import Color, ColorParseError

NAMED_COLORS: dict[str, str] = {
    "red": "#ef4444",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "yellow": "#eab308",
    "purple": "#a855f7",
    "orange": "#f97316",
    "pink": "#ec4899",
    "cyan": "#06b6d4",
    "default": "#666666",
}

DEFAULT_PROMPT_COLOR: str = "#666666"

_HEX6_RE = re.compile(r"^[0-9a-f]{6}$")


def validate_color(value: str) -> tuple[str | None, str | None]:
    """Validate a color string and return its hex representation.

    Args:
        value: Named color, 6-char hex (with/without #), 3-digit hex, or CSS color name.

    Returns:
        (hex_color, None) on success, (None, error_msg) on failure.
    """
    original = value
    value = value.strip().lower()

    # Named color lookup
    if value in NAMED_COLORS:
        return NAMED_COLORS[value], None

    # 6-digit hex (with or without #)
    bare = value.lstrip("#")
    if _HEX6_RE.match(bare):
        return f"#{bare}", None

    # Fallback to Textual Color.parse
    try:
        color = Color.parse(value)
        return color.hex6, None
    except ColorParseError:
        return None, f"Unknown color '{original}'. Use /color for options."
