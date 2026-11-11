"""Tests for the per-section renderer and SectionBuilder (verify_render)."""

from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify_formatting import (
    STATUS_SYMBOLS,
    Row,
    _format_row,
    _format_section,
    _hint,
    _pad,
)
from mcp_coder.cli.commands.verify_render import SectionBuilder

from .conftest import (
    _assert_section_aligned,
    _assert_sections_aligned,
    _assert_value_at_column,
    _expected_value_column,
    _render,
)

_DEFAULT_COL = _expected_value_column()  # 32
_WIDE_COL = _expected_value_column(label_width=30)  # 40


class TestRenderRows:
    """``_render_rows`` computes one label width per section."""

    def test_long_label_widens_every_row(self) -> None:
        text = _render(
            [
                Row("a" * 30, "[OK]", "long"),
                Row("short", "[ERR]", "x"),
                Row("child", "[WARN]", "y", 4),
            ]
        )
        assert _WIDE_COL == 40
        for line in text.splitlines():
            _assert_value_at_column(line, _WIDE_COL)

    def test_indents_share_marker_and_value_columns(self) -> None:
        text = _render(
            [
                Row("two", "[OK]", "a", 2),
                Row("four", "[OK]", "b", 4),
                Row("six", "[OK]", "c", 6),
            ]
        )
        lines = text.splitlines()
        assert len({line.index("[OK]") for line in lines}) == 1
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)
        assert _assert_section_aligned(text) == 3

    @pytest.mark.parametrize(
        ("label", "expected_col"),
        [("short", _DEFAULT_COL), ("b" * 30, _WIDE_COL)],
    )
    def test_hint_starts_at_value_column(self, label: str, expected_col: int) -> None:
        lines = _render([Row(label, "[OK]", "v"), _hint("-> do x")]).splitlines()
        assert lines[1].lstrip() == "-> do x"
        assert len(lines[1]) - len(lines[1].lstrip()) == expected_col

    def test_empty_marker_and_label_less_rows_align(self) -> None:
        lines = _render(
            [
                Row("marked", "[OK]", "a"),
                Row("unmarked", "", "b"),
                Row("", "[WARN]", "c"),
            ]
        ).splitlines()
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)

    def test_wrap_row_wraps_against_value_column(self) -> None:
        value = ", ".join(f"tool_number_{i}" for i in range(20))
        lines = _render([Row("server", "[OK]", value, wrap=True)]).splitlines()
        assert len(lines) > 1
        assert all(len(line) <= 80 for line in lines)
        for line in lines:
            _assert_value_at_column(line, _DEFAULT_COL)
        for line in lines[1:]:
            assert not line[:_DEFAULT_COL].strip()
        joined = " ".join(line[_DEFAULT_COL:] for line in lines)
        assert joined == value

    def test_str_items_pass_through_and_do_not_widen(self) -> None:
        items = ["", "  [Python]", "  pip install x" + "y" * 40]
        lines = _render([*items, Row("label", "[OK]", "v")]).splitlines()
        assert lines[:3] == items
        _assert_value_at_column(lines[3], _DEFAULT_COL)


def test_assert_section_aligned_rejects_misaligned_values() -> None:
    text = "\n".join(
        [
            _format_row("a", "[OK]", "x", indent=2),
            _format_row("b" * 30, "[OK]", "y", indent=2),
        ]
    )
    with pytest.raises(AssertionError):
        _assert_section_aligned(text)


class TestSectionBuilder:
    """``SectionBuilder`` streams section by section."""

    def test_open_prints_header_rows_after_close(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        assert capsys.readouterr().out == _pad("A") + "\n"
        out.add(Row("a", "[OK]", "x"))
        assert capsys.readouterr().out == ""
        out.close()
        assert capsys.readouterr().out == _render([Row("a", "[OK]", "x")]) + "\n"

    def test_open_second_section_closes_first(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add(Row("a", "[OK]", "x"))
        out.open("B")
        assert capsys.readouterr().out.splitlines() == [
            *_pad("A").splitlines(),
            _render([Row("a", "[OK]", "x")]),
            *_pad("B").splitlines(),
        ]

    def test_section_without_rows_uses_default_width(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add("  [Python]", "  " + "z" * 50, _hint("-> do x"))
        out.close()
        hint_line = capsys.readouterr().out.splitlines()[-1]
        assert hint_line.lstrip() == "-> do x"
        assert len(hint_line) - len(hint_line.lstrip()) == _DEFAULT_COL

    def test_add_without_open_section_prints_immediately(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out = SectionBuilder()
        out.add(Row("label", "[OK]", "value", 4))
        assert capsys.readouterr().out == (
            _format_row("label", "[OK]", "value", indent=4) + "\n"
        )
        out.add("text")
        assert capsys.readouterr().out == "text\n"

    def test_close_twice_is_noop(self, capsys: pytest.CaptureFixture[str]) -> None:
        out = SectionBuilder()
        out.open("A")
        out.add(Row("a", "[OK]", "x"))
        out.close()
        capsys.readouterr()
        out.close()
        assert capsys.readouterr().out == ""

    def test_exception_flushes_open_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(RuntimeError):
            with SectionBuilder() as out:
                out.open("A")
                out.add(Row("a", "[OK]", "flushed"))
                raise RuntimeError("boom")
        assert "flushed" in capsys.readouterr().out

    def test_flush_failure_does_not_mask_exception(self) -> None:
        with patch(
            "mcp_coder.cli.commands.verify_render._render_rows",
            side_effect=ValueError("render failed"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                with SectionBuilder() as out:
                    out.open("A")
                    out.add(Row("a", "[OK]", "x"))
                    raise RuntimeError("boom")

    def test_normal_exit_closes_open_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with SectionBuilder() as out:
            out.open("A")
            out.add(Row("a", "[OK]", "closed on exit"))
        assert "closed on exit" in capsys.readouterr().out

    def test_sections_get_independent_widths(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with SectionBuilder() as out:
            out.section("A", [Row("a", "[OK]", "x")])
            out.section("B", [Row("b" * 30, "[OK]", "y"), Row("c", "[WARN]", "z", 4)])
        output = capsys.readouterr().out
        lines = output.splitlines()
        a_idx = lines.index(_pad("A").strip("\n"))
        b_idx = lines.index(_pad("B").strip("\n"))
        _assert_value_at_column(lines[a_idx + 1], _DEFAULT_COL)
        _assert_value_at_column(lines[b_idx + 1], _WIDE_COL)
        _assert_value_at_column(lines[b_idx + 2], _WIDE_COL)
        _assert_sections_aligned(output)


def test_github_permissions_section_aligned_with_token_hint() -> None:
    """GITHUB widens to fit "Commit statuses: Read" at indent 4; hint follows."""
    granted = {"ok": True, "value": "granted"}
    result: dict[str, Any] = {
        "token_configured": {"ok": True, "value": "YES", "token_source": "env"},
        "repo_accessible": {"ok": True, "value": "owner/repo"},
        **{f"perm_{k}_read": dict(granted) for k in ("contents", "statuses")},
        "overall_ok": True,
    }
    text = _render(_format_section(result, STATUS_SYMBOLS))
    col = _expected_value_column(label_width=23)
    assert col == 33
    assert _assert_section_aligned(text) == 4
    for line in text.splitlines():
        if "[OK]" in line:
            _assert_value_at_column(line, col)
    hint = next(line for line in text.splitlines() if "GITHUB_TOKEN" in line)
    assert hint == " " * col + "from GITHUB_TOKEN env var"
