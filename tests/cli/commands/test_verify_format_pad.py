"""Tests for _pad header padding and _format_row / _format_row_prefix helpers."""

import pytest

from mcp_coder.cli.commands.verify_formatting import (
    _LABEL_WIDTH,
    _MARKER_SLOT_WIDTH,
    Line,
    Row,
    _format_row,
    _format_row_prefix,
    _hint,
    _pad,
    _section_label_width,
)


class TestPadHeader:
    """Tests for the _pad(title) header padding helper."""

    def test_short_title_padded_to_75(self) -> None:
        out = _pad("CONFIG")
        assert out == "\n=== CONFIG " + "=" * (75 - len("=== CONFIG "))
        assert len(out.lstrip("\n")) == 75

    def test_exact_75_title_no_extra_padding(self) -> None:
        title = "X" * (75 - len("===  "))  # prefix "=== X...X " == 75
        out = _pad(title)
        assert len(out.lstrip("\n")) == 75

    def test_long_title_not_truncated(self) -> None:
        long = "MCP SERVERS (via langchain-mcp-adapters \u2014 for completeness)"
        out = _pad(long)
        assert long in out
        assert out.lstrip("\n").startswith(f"=== {long} ")


class TestFormatRowHelpers:
    """Tests for the _format_row / _format_row_prefix helpers (Step 1)."""

    def _expected_prefix(
        self, label: str, marker: str, indent: int, label_width: int = _LABEL_WIDTH
    ) -> str:
        return (
            f"{' ' * indent}"
            f"{label.ljust(label_width - (indent - 2))} "
            f"{marker.ljust(_MARKER_SLOT_WIDTH)} "
        )

    def test_labeled_row_with_ok_marker(self) -> None:
        """Labeled row with [OK] marker aligns value at column 32."""
        out = _format_row("api_key", "[OK]", "configured", indent=2)
        expected = (
            self._expected_prefix("api_key", "[OK]", indent=2) + "configured"
        ).rstrip()
        assert out == expected
        # Value substring starts at the value column index
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("configured") == expected_col

    def test_labeled_row_no_marker_aligns_with_marker_row(self) -> None:
        """Empty marker is padded so value column matches marker rows."""
        with_ok = _format_row("api_key", "[OK]", "configured", indent=2)
        no_marker = _format_row("base_url", "", "not configured", indent=2)
        assert with_ok.index("configured") == no_marker.index("not configured")

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_value_column_identical_across_markers(self, marker: str) -> None:
        """All markers produce the same value column position."""
        out = _format_row("label", marker, "value", indent=2)
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("value") == expected_col

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_label_less_row_aligns_at_value_column(self, marker: str) -> None:
        """Label-less rows align at the same value column as labeled rows."""
        out = _format_row("", marker, "value", indent=2)
        expected_col = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("value") == expected_col

    @pytest.mark.parametrize("marker", ["[OK]", "[WARN]", "[ERR]"])
    def test_prefix_length_invariant(self, marker: str) -> None:
        """All markers produce equal-length prefixes derived from constants."""
        prefix = _format_row_prefix("x", marker, indent=2)
        expected_len = 2 + _LABEL_WIDTH + 1 + _MARKER_SLOT_WIDTH + 1
        assert len(prefix) == expected_len == 32

    def test_prefix_lengths_match_across_markers(self) -> None:
        """Prefix lengths are identical for [OK], [WARN], [ERR]."""
        lens = {
            len(_format_row_prefix("x", marker, indent=2))
            for marker in ("[OK]", "[WARN]", "[ERR]")
        }
        assert len(lens) == 1

    def test_format_row_is_prefix_plus_value_rstripped(self) -> None:
        """Composition contract: _format_row == (prefix + value).rstrip()."""
        prefix = _format_row_prefix("label", "[OK]", indent=2)
        out = _format_row("label", "[OK]", "value", indent=2)
        assert out == (prefix + "value").rstrip()

    def test_custom_label_width_prefix_length(self) -> None:
        """Custom label_width shifts the value column by the diff."""
        prefix = _format_row_prefix("x", "[OK]", indent=2, label_width=30)
        assert len(prefix) == 2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1

    def test_custom_label_width_value_column(self) -> None:
        """_format_row honours label_width when computing the value column."""
        out = _format_row("longish label", "[OK]", "Z", indent=2, label_width=30)
        expected_col = 2 + 30 + 1 + _MARKER_SLOT_WIDTH + 1
        assert out.index("Z") == expected_col


class TestPerSectionColumnRule:
    """Tests for the indent-independent column rule and the Row model."""

    @pytest.mark.parametrize("indent", [2, 4, 6])
    def test_short_label_value_at_column_32_for_any_indent(self, indent: int) -> None:
        """Nested rows share the default value column with indent-2 rows."""
        out = _format_row("label", "[OK]", "value", indent=indent)
        assert out.index("value") == 32
        assert out.startswith(" " * indent + "label")

    @pytest.mark.parametrize("indent", [2, 4, 6])
    def test_prefix_length_is_label_width_plus_10(self, indent: int) -> None:
        """Prefix length does not depend on indent."""
        for label_width in (_LABEL_WIDTH, 30):
            prefix = _format_row_prefix(
                "x", "[OK]", indent=indent, label_width=label_width
            )
            assert len(prefix) == label_width + 10

    def test_long_label_widens_instead_of_overrunning_indent_2(self) -> None:
        """A label longer than the field widens the row's own column."""
        out = _format_row("x" * 30, "[OK]", "v", indent=2)
        assert out.index("v") == 2 + 30 + 1 + 6 + 1
        assert out[2 + 30 + 1 :].startswith("[OK]")

    def test_long_label_widens_instead_of_overrunning_indent_4(self) -> None:
        """At indent 4 a 21-char label needs label width 23 → value column 33."""
        out = _format_row("a" * 21, "[OK]", "v", indent=4)
        assert out.index("v") == 33

    def test_section_label_width_empty(self) -> None:
        assert _section_label_width([]) == _LABEL_WIDTH == 22

    def test_section_label_width_ignores_str_items(self) -> None:
        assert _section_label_width(["x" * 60, "", "  [Python]"]) == _LABEL_WIDTH

    def test_section_label_width_counts_indent(self) -> None:
        assert _section_label_width([Row("a" * 21, "", "", 4)]) == 23

    def test_section_label_width_takes_max(self) -> None:
        lines: list[Line] = [Row("short", "[OK]", "v"), "free", Row("b" * 25, "", "v")]
        assert _section_label_width(lines) == 25

    def test_row_defaults(self) -> None:
        row = Row("label", "[OK]", "value")
        assert row.indent == 2
        assert row.wrap is False

    def test_hint_is_empty_label_and_marker_row(self) -> None:
        assert _hint("-> x") == Row("", "", "-> x")

    def test_hint_text_starts_at_value_column(self) -> None:
        out = _format_row(*_hint("-> x")[:3], indent=2)
        assert out.index("-> x") == 32
