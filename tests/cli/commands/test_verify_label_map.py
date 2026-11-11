"""Tests for verify label names: fixed labels fit the default label width."""

from __future__ import annotations

from mcp_coder.cli.commands.verify_formatting import (
    _LABEL_MAP,
    _LABEL_WIDTH,
    STATUS_SYMBOLS,
    Row,
    _format_tools_exposed_section,
)


def test_fixed_labels_fit_default_width() -> None:
    """Every fixed label fits the default label width at indent 2."""
    too_long = {k: v for k, v in _LABEL_MAP.items() if len(v) > _LABEL_WIDTH}
    assert not too_long, f"labels wider than {_LABEL_WIDTH}: {too_long}"


def test_renamed_labels() -> None:
    """Shortened labels replace the ones that overran the default width."""
    assert _LABEL_MAP["signing_consistency"] == "Signing consistency"
    assert _LABEL_MAP["ollama_tools_capability"] == "Tool-call capability"
    lines, _ = _format_tools_exposed_section(None, STATUS_SYMBOLS)
    assert isinstance(lines[0], Row)
    assert lines[0].label == "Tools exposed to model"
