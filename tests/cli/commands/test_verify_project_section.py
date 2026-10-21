"""Tests for the PROJECT section's format_code, Formatter and leftover-key rows."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import _format_row
from mcp_coder.cli.commands.verify_sections import _print_project_section
from tests.cli.commands.conftest import _make_args, _make_verify_mocks

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}


def _run(
    tmp_path: Path, content: str | None, capsys: pytest.CaptureFixture[str]
) -> tuple[bool, list[str]]:
    """Write *content* as pyproject.toml (if given), run the section, return result."""
    if content is not None:
        (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    ok = _print_project_section(tmp_path, _SYMBOLS)
    return ok, capsys.readouterr().out.splitlines()


def _row(lines: list[str], label: str) -> str:
    """Return the single row whose label field is *label*."""
    matches = [line for line in lines if line.strip().startswith(label + " ")]
    assert len(matches) == 1, f"expected exactly one {label!r} row, got {matches!r}"
    return matches[0]


class TestFormatterRow:
    """Formatter row reflects mcp-tools-py's resolve_steps."""

    def test_black_only(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.black]\nline-length = 88\n", capsys)
        assert ok is True
        assert _row(lines, "Formatter") == _format_row(
            "Formatter", "[OK]", "isort → black", indent=4
        )

    def test_ruff_format_only(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.ruff.format]\n", capsys)
        assert ok is True
        assert _row(lines, "Formatter") == _format_row(
            "Formatter", "[OK]", "ruff_imports → ruff_format", indent=4
        )

    def test_both_declared_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.black]\n[tool.ruff.format]\n", capsys)
        assert ok is False
        row = _row(lines, "Formatter")
        assert "[ERR]" in row
        assert "declares both" in row

    def test_neither_declared_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[project]\nname = 'demo'\n", capsys)
        assert ok is False
        row = _row(lines, "Formatter")
        assert "[ERR]" in row
        assert "No formatter declared" in row

    def test_no_pyproject_is_error_without_format_code_row(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, None, capsys)
        assert ok is False
        assert "[ERR]" in _row(lines, "Formatter")
        assert not any("format_code" in line for line in lines)


class TestFormatCodeRow:
    """format_code row reflects [tool.mcp-coder] format_code."""

    def test_absent_is_enabled_default(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is True
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "enabled (default)", indent=4
        )

    def test_true_is_enabled(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(
            tmp_path, "[tool.mcp-coder]\nformat_code = true\n[tool.black]\n", capsys
        )
        assert ok is True
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "enabled", indent=4
        )

    def test_false_is_disabled_formatter_still_evaluated(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.mcp-coder]\nformat_code = false\n", capsys)
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "disabled", indent=4
        )
        assert "[ERR]" in _row(lines, "Formatter")
        assert ok is False

    def test_non_bool_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(
            tmp_path, '[tool.mcp-coder]\nformat_code = "false"\n[tool.black]\n', capsys
        )
        assert ok is False
        assert "[ERR]" in _row(lines, "format_code")
        assert "[OK]" in _row(lines, "Formatter")


class TestLegacyKeyRow:
    """Leftover [tool.mcp-coder.implement] format_code is an [ERR]."""

    def test_leftover_key_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(
            tmp_path,
            "[tool.mcp-coder.implement]\nformat_code = true\n[tool.black]\n",
            capsys,
        )
        assert ok is False
        row = _row(lines, "legacy format_code")
        assert "[ERR]" in row
        assert "[tool.mcp-coder] format_code" in row

    def test_no_leftover_key_no_row(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert not any("legacy format_code" in line for line in lines)


class TestExecuteVerifyProjectExit:
    """execute_verify feeds the PROJECT result into the exit code."""

    @pytest.mark.parametrize(("project_ok", "expected"), [(True, 0), (False, 1)])
    def test_project_result_drives_exit_code(
        self, tmp_path: Path, project_ok: bool, expected: int
    ) -> None:
        with (
            _make_verify_mocks(),
            patch(
                "mcp_coder.cli.commands.verify._print_project_section",
                return_value=project_ok,
            ),
        ):
            assert execute_verify(_make_args(project_dir=str(tmp_path))) == expected
