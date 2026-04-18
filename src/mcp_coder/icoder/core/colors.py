"""Color validation for iCoder prompt border."""

from __future__ import annotations

import re

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
_HEX3_RE = re.compile(r"^[0-9a-f]{3}$")


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

    # 3-digit hex shorthand (expand #f00 -> #ff0000)
    if _HEX3_RE.match(bare):
        expanded = "".join(c * 2 for c in bare)
        return f"#{expanded}", None

    return None, f"Unknown color '{original}'. Use /color for options."
