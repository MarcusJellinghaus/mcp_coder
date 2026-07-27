"""Tests for the iCoder permission loader (Step 2, TDD).

Step 2 covers only the JSONC preprocessor
``mcp_coder.icoder.permissions.loader._strip_jsonc`` — a stdlib,
string/escape-aware comment stripper that also tolerates trailing commas.
Comment-like sequences inside string literals (URLs, ``"a // b"``, escaped
quotes) must survive intact; the result must be valid JSON for ``json.loads``.
"""

from __future__ import annotations

import json

from mcp_coder.icoder.permissions.loader import _strip_jsonc

# --- comment removal ---


def test_line_comment_removed() -> None:
    """A ``//`` line comment is stripped and the JSON still parses."""
    text = '{"a": 1 // trailing note\n}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


def test_block_comment_removed() -> None:
    """A ``/* */`` block comment is stripped and the JSON still parses."""
    text = '{/* header */ "a": 1}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


# --- comment markers inside strings are preserved ---


def test_url_double_slash_preserved() -> None:
    """A ``//`` inside a string literal (URL) is left untouched."""
    text = '{"url": "https://example.com"}'
    assert json.loads(_strip_jsonc(text)) == {"url": "https://example.com"}


def test_line_marker_inside_string_preserved() -> None:
    """``"a // b"`` keeps its inner ``//``."""
    text = '{"v": "a // b"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a // b"}


def test_block_marker_inside_string_preserved() -> None:
    """``"a /* b */ c"`` keeps its inner block markers."""
    text = '{"v": "a /* b */ c"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a /* b */ c"}


def test_escaped_quote_then_comment() -> None:
    """An escaped quote survives; a ``//`` after the string closes is stripped."""
    text = '{"v": "he said \\"hi\\" //x"} // gone'
    assert json.loads(_strip_jsonc(text)) == {"v": 'he said "hi" //x'}


# --- trailing commas ---


def test_trailing_comma_before_brace_removed() -> None:
    """A trailing comma before ``}`` is dropped."""
    text = '{"a": 1,}'
    assert json.loads(_strip_jsonc(text)) == {"a": 1}


def test_trailing_comma_before_bracket_removed() -> None:
    """A trailing comma before ``]`` is dropped."""
    text = '{"a": [1, 2,]}'
    assert json.loads(_strip_jsonc(text)) == {"a": [1, 2]}


def test_comma_inside_string_preserved() -> None:
    """A comma-then-bracket inside a string (``"a,]"``) is preserved."""
    text = '{"v": "a,]"}'
    assert json.loads(_strip_jsonc(text)) == {"v": "a,]"}


# --- no-op round trip ---


def test_plain_json_roundtrips() -> None:
    """Comment-free input round-trips unchanged through json.loads."""
    obj = {"a": 1, "b": ["x", "y"], "c": {"d": True}}
    text = json.dumps(obj)
    assert json.loads(_strip_jsonc(text)) == obj
