"""Tests for the PROJECT section's .mcp-file-access, format_code, Toolkit, leftover-key rows."""

from collections.abc import Generator
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import _format_row
from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_sections import _print_project_section
from mcp_coder.cli.commands.verify_toolkit_rows import toolkit_rows
from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.toolkit import VerifyItem
from mcp_coder.utils.toolkit_runner import verify_toolkit
from tests.cli.commands.conftest import (
    _assert_section_aligned,
    _make_args,
    _make_verify_mocks,
)

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
_VERIFY_TOOLKIT = "mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit"


@pytest.fixture(autouse=True)
def _stub_toolkit() -> Generator[None, None, None]:
    """Stub the toolkit registry and verify so only the formatter item reports."""
    from mcp_tools_py.toolkit import PythonToolkit

    with (
        patch(
            "mcp_coder.utils.toolkit_runner._toolkit_class",
            lambda _name: PythonToolkit,
        ),
        _items(VerifyItem("formatter", "ok")),
    ):
        yield


def _run(
    tmp_path: Path, content: str | None, capsys: pytest.CaptureFixture[str]
) -> tuple[bool, list[str]]:
    """Write *content* as pyproject.toml (if given), run the section, return result."""
    if content is not None:
        (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    ok = _print_project_section(tmp_path, _SYMBOLS, SectionBuilder())
    return ok, capsys.readouterr().out.splitlines()


def _row(lines: list[str], label: str) -> str:
    """Return the single row whose label field is *label*."""
    matches = [line for line in lines if line.strip().startswith(label + " ")]
    assert len(matches) == 1, f"expected exactly one {label!r} row, got {matches!r}"
    return matches[0]


def _squash(text: str) -> str:
    """Remove all whitespace, so wrapped rows compare like single lines."""
    return "".join(text.split())


_NOT_PRESENT = ".mcp-file-access [OK] not present (gitignore defaults)"
_INVALID_WRITABLE = (
    ".mcp-file-access [ERR] invalid (",
    "unknown level 'writable'",
)
_NOT_CHECKED = (
    ".mcp-file-access [WARN] not checked (mcp-workspace in this environment"
    " does not support .mcp-file-access)"
)


class TestFileAccessRow:
    """.mcp-file-access row reports the rules file right after Language."""

    @pytest.mark.parametrize("with_pyproject", [True, False])
    @pytest.mark.parametrize(
        ("rules", "supported", "expected", "expected_ok"),
        [
            (None, True, (_NOT_PRESENT,), True),
            (None, False, (_NOT_PRESENT,), True),
            ("read-write /.scratch/\n", True, (".mcp-file-access [OK] valid",), True),
            ("writable /.scratch/\n", True, _INVALID_WRITABLE, False),
            (
                "<dir>",
                True,
                (".mcp-file-access [ERR] invalid (is a directory)",),
                False,
            ),
            ("writable /.scratch/\n", False, (_NOT_CHECKED,), True),
        ],
        ids=[
            "absent",
            "absent-unsupported",
            "valid",
            "invalid",
            "directory",
            "unsupported",
        ],
    )
    def test_row(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        with_pyproject: bool,
        rules: str | None,
        supported: bool,
        expected: tuple[str, ...],
        expected_ok: bool,
    ) -> None:
        rules_path = tmp_path / ".mcp-file-access"
        if rules == "<dir>":
            rules_path.mkdir()
        elif rules is not None:
            rules_path.write_text(rules, encoding="utf-8")
        with patch(
            "mcp_coder.cli.commands.verify_sections.FILE_ACCESS_SUPPORTED",
            supported,
        ):
            ok, lines = _run(
                tmp_path, "[tool.black]\n" if with_pyproject else None, capsys
            )

        language = next(
            i for i, line in enumerate(lines) if line.strip().startswith("Language ")
        )
        assert lines[language + 1].startswith("  .mcp-file-access ")
        output = _squash("\n".join(lines))
        for fragment in expected:
            assert _squash(fragment) in output
        assert ok is expected_ok


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
            "format_code", "[OK]", "enabled (pyproject.toml)", indent=4
        )

    def test_non_bool_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(
            tmp_path, '[tool.mcp-coder]\nformat_code = "false"\n[tool.black]\n', capsys
        )
        assert ok is False
        assert "[ERR]" in _row(lines, "format_code")

    def test_false_is_disabled(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.mcp-coder]\nformat_code = false\n", capsys)
        assert ok is True
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "disabled (pyproject.toml)", indent=4
        )

    def test_mcp_coder_toml_only_names_source(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "mcp-coder.toml").write_text(
            "[tool.mcp-coder]\nformat_code = false\n"
            '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n',
            encoding="utf-8",
        )
        ok, lines = _run(tmp_path, None, capsys)
        assert ok is True
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "disabled (mcp-coder.toml)", indent=2
        )

    def test_no_files_is_enabled_default(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, lines = _run(tmp_path, None, capsys)
        assert _row(lines, "format_code") == _format_row(
            "format_code", "[OK]", "enabled (default)", indent=2
        )

    def test_non_bool_in_mcp_coder_toml_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "mcp-coder.toml").write_text(
            '[tool.mcp-coder]\nformat_code = "no"\n'
            '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n',
            encoding="utf-8",
        )
        ok, lines = _run(tmp_path, None, capsys)
        assert ok is False
        row = _row(lines, "format_code")
        assert row.startswith("  format_code ")
        assert "[ERR]" in row


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


def _items(*items: VerifyItem, action: str = "format") -> AbstractContextManager[Any]:
    """Patch verify_toolkit to return *items* for *action*, nothing for the rest."""
    return patch(_VERIFY_TOOLKIT, lambda _l, _p, a: list(items) if a == action else [])


class TestToolkitRows:
    """Toolkit row and the toolkit's own verify items."""

    def test_default_toolkit_row(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is True
        assert _row(lines, "Toolkit") == _format_row(
            "Toolkit", "[OK]", "mcp-tools-py", indent=4
        )

    def test_formatter_item_shown(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with _items(VerifyItem("ruff", "ok"), VerifyItem("formatter", "error", "x")):
            ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is False
        assert "      format" in lines
        assert _row(lines, "ruff") == _format_row("ruff", "[OK]", "ok", indent=8)
        assert _row(lines, "formatter") == _format_row(
            "formatter", "[ERR]", "x", indent=8
        )

    def test_error_item_fails_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with _items(VerifyItem("ruff", "error", "ruff not available")):
            ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is False
        assert _row(lines, "ruff") == _format_row(
            "ruff", "[ERR]", "ruff not available", indent=8
        )

    def test_warning_item_does_not_fail(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with _items(VerifyItem("mypy", "warning", "old"), action="check"):
            ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is True
        assert "      check" in lines
        assert _row(lines, "mypy") == _format_row("mypy", "[WARN]", "old", indent=8)

    def test_invalid_config_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok, lines = _run(
            tmp_path, "[tool.black]\n[tool.mcp-coder.toolkit]\nbogus = 1\n", capsys
        )
        assert ok is False
        row = _row(lines, "Toolkit")
        assert "[ERR]" in row
        assert "bogus" in row

    def test_verify_raising_is_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        def _raise(_l: object, _p: object, action: str) -> list[VerifyItem]:
            if action == "format":
                raise ValueError("verify failed: boom")
            return []

        with patch(_VERIFY_TOOLKIT, _raise):
            ok, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert ok is False
        assert "[OK]" in _row(lines, "Toolkit")
        format_at = lines.index("      format")
        row = _row(lines, "verify")
        assert lines.index(row) == format_at + 1
        assert "[ERR]" in row
        assert "boom" in row

    @pytest.mark.usefixtures("toolkit_with_ruff")
    def test_toolkit_item_row_aligns_with_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, lines = _run(tmp_path, "[tool.black]\n", capsys)
        assert _row(lines, "ruff").startswith("        ruff ")
        assert _row(lines, "format_code").startswith("    format_code ")
        assert _row(lines, "pyproject.toml").startswith("  pyproject.toml ")
        assert _assert_section_aligned("\n".join(lines)) >= 3

    def test_mcp_coder_toml_without_pyproject(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "mcp-coder.toml").write_text(
            '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n', encoding="utf-8"
        )
        _, lines = _run(tmp_path, None, capsys)
        assert _row(lines, "Toolkit") == _format_row(
            "Toolkit", "[OK]", "mcp-tools-py", indent=2
        )


_COMMAND_TOML = (
    '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n'
    "[tool.mcp-coder.toolkit.command.format]\n"
    'apply = [{argv = ["fakenpm", "fmt"]}]\n'
    "[tool.mcp-coder.toolkit.command.check]\n"
    'quick = [{argv = ["fakenpm", "lint"]}]\n'
    'standard = [{argv = ["fakenpm", "lint"]}]\n'
    "[tool.mcp-coder.toolkit.command.test]\n"
    'quick = [{argv = ["fakenpm", "test"]}]\n'
    'standard = [{argv = ["fakenpm", "test"]}]\n'
    'unattended = [{argv = ["fakenpm", "test"]}]\n'
)


@pytest.fixture
def command_project(tmp_path: Path, fake_npm: Path) -> Generator[Path, None, None]:
    """A ``command`` toolkit project with only ``mcp-coder.toml``, real verify.

    Declares every depth the default bindings request.
    """
    for name in ("fmt", "lint", "test"):
        (fake_npm / f"{name}.py").write_text("", encoding="utf-8")
    (tmp_path / "mcp-coder.toml").write_text(_COMMAND_TOML, encoding="utf-8")
    with (
        patch(
            "mcp_coder.utils.toolkit_runner._toolkit_class",
            lambda _name: CommandToolkit,
        ),
        patch(_VERIFY_TOOLKIT, verify_toolkit),
    ):
        yield tmp_path


class TestCommandToolkitGating:
    """Format verify only where it applies; no Formatter row."""

    def test_command_project_has_no_formatter_row(
        self, command_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ok = _print_project_section(command_project, _SYMBOLS, SectionBuilder())
        lines = capsys.readouterr().out.splitlines()
        assert ok is True
        assert not any(line.strip().startswith("Formatter ") for line in lines)
        assert not any("[ERR]" in line for line in lines)
        assert _row(lines, "Toolkit") == _format_row(
            "Toolkit", "[OK]", "command", indent=2
        )

    def test_empty_commit_binding_skips_verify(
        self, command_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (command_project / "mcp-coder.toml").write_text(
            _COMMAND_TOML.replace(
                "[tool.mcp-coder.toolkit.command",
                "[tool.mcp-coder.toolkit.bindings]\ncommit = []\n"
                "[tool.mcp-coder.toolkit.command",
                1,
            ),
            encoding="utf-8",
        )
        mock_verify = MagicMock(return_value=[])
        with patch(_VERIFY_TOOLKIT, mock_verify):
            assert toolkit_rows(command_project, _SYMBOLS, SectionBuilder()) is True
        assert [c.args[2] for c in mock_verify.call_args_list] == ["check", "test"]
        assert "command" in _row(capsys.readouterr().out.splitlines(), "Toolkit")

    def test_format_code_false_skips_verify(self, command_project: Path) -> None:
        (command_project / "pyproject.toml").write_text(
            "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
        )
        mock_verify = MagicMock(return_value=[])
        with patch(_VERIFY_TOOLKIT, mock_verify):
            assert toolkit_rows(command_project, _SYMBOLS, SectionBuilder()) is True
        assert [c.args[2] for c in mock_verify.call_args_list] == ["check", "test"]

    def test_broken_command_config_is_error(
        self, command_project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (command_project / "mcp-coder.toml").write_text(
            _COMMAND_TOML.replace(
                "[tool.mcp-coder.toolkit.command.format]",
                "[tool.mcp-coder.toolkit.command]\nbogus = 1\n"
                "[tool.mcp-coder.toolkit.command.format]",
            ),
            encoding="utf-8",
        )
        assert toolkit_rows(command_project, _SYMBOLS, SectionBuilder()) is False
        errors = [
            line for line in capsys.readouterr().out.splitlines() if "[ERR]" in line
        ]
        assert any("unknown top-level key 'bogus'" in line for line in errors)
        assert (
            _print_project_section(command_project, _SYMBOLS, SectionBuilder()) is False
        )


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

    @pytest.mark.real_toolkit_config
    def test_no_toolkit_configured_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            _make_verify_mocks(),
            patch(
                "mcp_coder.cli.commands.verify._print_project_section",
                _print_project_section,
            ),
        ):
            assert execute_verify(_make_args(project_dir=str(tmp_path))) == 1
        toolkit = _row(capsys.readouterr().out.splitlines(), "Toolkit")
        assert "[ERR]" in toolkit
        assert "No [tool.mcp-coder.toolkit] table" in toolkit
