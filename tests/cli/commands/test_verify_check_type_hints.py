"""Tests for the retired check_type_hints row (``verify_toolkit_rows``)."""

from pathlib import Path

import pytest

from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_toolkit_rows import check_type_hints_row

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

_TOOLKIT = '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n'
_SKIP_BINDINGS = (
    "[tool.mcp-coder.toolkit.bindings]\n"
    'implement_task = []\nimplement_final = ["test@quick"]\n'
)


def _run(
    tmp_path: Path, content: str, capsys: pytest.CaptureFixture[str]
) -> tuple[bool, list[str]]:
    """Write *content* to pyproject.toml, add the row, return result and lines."""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    ok = check_type_hints_row(tmp_path, _SYMBOLS, SectionBuilder())
    return ok, capsys.readouterr().out.splitlines()


def _implement(value: str) -> str:
    """Return a [tool.mcp-coder.implement] table setting check_type_hints."""
    return f"[tool.mcp-coder.implement]\ncheck_type_hints = {value}\n"


def test_no_key_no_row(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Without the key nothing is shown."""
    ok, lines = _run(tmp_path, _TOOLKIT, capsys)
    assert ok is True
    assert not lines


@pytest.mark.parametrize("value", ["true", '"no"'])
def test_non_false_value_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    """true or a non-bool value → [WARN] retired; remove it."""
    ok, lines = _run(tmp_path, _TOOLKIT + _implement(value), capsys)
    assert ok is True
    assert len(lines) == 1
    assert lines[0].startswith("    check_type_hints")
    assert "[WARN]" in lines[0]
    assert "retired; remove it" in lines[0]


def test_false_with_default_bindings_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """false while the bindings still request checks → [ERR] naming the fix."""
    ok, lines = _run(tmp_path, _TOOLKIT + _implement("false"), capsys)
    assert ok is False
    assert len(lines) == 1
    assert "[ERR]" in lines[0]
    assert "false is retired and checks now run" in lines[0]
    assert "[tool.mcp-coder.toolkit.bindings]" in lines[0]
    assert "implement_task = []" in lines[0]
    assert 'implement_final = ["test@quick"]' in lines[0]


def test_false_names_only_entries_with_checks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An implement entry without check@* is not named in the fix."""
    bindings = '[tool.mcp-coder.toolkit.bindings]\nimplement_final = ["test@quick"]\n'
    ok, lines = _run(tmp_path, _TOOLKIT + bindings + _implement("false"), capsys)
    assert ok is False
    assert "implement_task = []" in lines[0]
    assert "implement_final" not in lines[0]


def test_false_with_skipping_bindings_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """false with bindings that already skip checks → [WARN]."""
    ok, lines = _run(tmp_path, _TOOLKIT + _SKIP_BINDINGS + _implement("false"), capsys)
    assert ok is True
    assert len(lines) == 1
    assert "[WARN]" in lines[0]
    assert "retired; remove it" in lines[0]


def test_false_with_broken_toolkit_table_no_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A broken toolkit table is left to the Toolkit row."""
    ok, lines = _run(tmp_path, _TOOLKIT + "bogus = 1\n" + _implement("false"), capsys)
    assert ok is True
    assert not lines
