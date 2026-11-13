"""Tests for the PROJECT section's Setup row (``verify_setup.setup_rows``)."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify_formatting import _format_row
from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_sections import _print_project_section
from mcp_coder.cli.commands.verify_setup import setup_rows
from mcp_coder.utils.executable import venv_search_path

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
_MODULE = "mcp_coder.cli.commands.verify_setup"

_NPM_CI = '[tool.mcp-coder.setup]\nsteps = [{ argv = ["npm", "ci"] }]\n'
_PYTHON_THEN_LINT = (
    "[tool.mcp-coder.setup]\n"
    'steps = [{ builtin = "python" }, { argv = ["pre-commit", "install"] }]\n'
)


@pytest.fixture
def resolver() -> Generator[MagicMock, None, None]:
    """Patch resolve_executable in the module; resolves everything by default."""
    with patch(f"{_MODULE}.resolve_executable", return_value="/bin/x") as mock:
        yield mock


@pytest.fixture
def no_venv() -> Generator[None, None, None]:
    """The project has no venv interpreter."""
    with patch(f"{_MODULE}.venv_python", return_value=None):
        yield


@pytest.fixture
def with_venv(tmp_path: Path) -> Generator[None, None, None]:
    """The project has a venv interpreter."""
    with patch(f"{_MODULE}.venv_python", return_value=tmp_path / "python"):
        yield


def _run(
    tmp_path: Path,
    content: str | None,
    capsys: pytest.CaptureFixture[str],
    file_name: str = "mcp-coder.toml",
    indent: int = 4,
) -> tuple[bool, list[str]]:
    """Write *content* to *file_name* (if given), add the rows, return result."""
    if content is not None:
        (tmp_path / file_name).write_text(content, encoding="utf-8")
    ok = setup_rows(tmp_path, _SYMBOLS, SectionBuilder(), indent=indent)
    return ok, capsys.readouterr().out.splitlines()


@pytest.mark.usefixtures("no_venv")
class TestSetupRow:
    """Summary row and config errors."""

    def test_valid_npm_config_is_ok(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ok, lines = _run(tmp_path, _NPM_CI, capsys)
        assert ok is True
        assert lines == [
            _format_row("Setup", "[OK]", "1 step(s) from mcp-coder.toml", indent=4)
        ]
        resolver.assert_called_once_with("npm", tmp_path, path=None)

    def test_broken_config_is_error(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ok, lines = _run(tmp_path, "[tool.mcp-coder.setup]\nbogus = 1\n", capsys)
        assert ok is False
        assert len(lines) == 1
        assert lines[0].startswith("    Setup ")
        assert "[ERR]" in lines[0]
        assert "Unknown [tool.mcp-coder.setup] key 'bogus'" in lines[0]
        resolver.assert_not_called()

    def test_no_table_no_pyproject_nothing_to_do(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ok, lines = _run(tmp_path, None, capsys, indent=2)
        assert ok is True
        assert lines == [_format_row("Setup", "[OK]", "nothing to do", indent=2)]
        resolver.assert_not_called()

    def test_pyproject_without_table_is_default(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ok, lines = _run(tmp_path, "[project]\n", capsys, file_name="pyproject.toml")
        assert ok is True
        assert lines == [
            _format_row("Setup", "[OK]", "default: python built-in", indent=4)
        ]
        resolver.assert_not_called()


@pytest.mark.usefixtures("no_venv")
class TestUnresolvedBeforePython:
    """An unresolvable argv[0] not preceded by the python built-in is an error."""

    def test_without_builtin_is_error(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resolver.return_value = None
        ok, lines = _run(tmp_path, _NPM_CI, capsys)
        assert ok is False
        assert lines == [
            _format_row("Setup", "[ERR]", "1 step(s) from mcp-coder.toml", indent=4),
            _format_row("", "[ERR]", "npm ci: 'npm' not found", indent=6),
        ]

    def test_before_builtin_is_error(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resolver.return_value = None
        content = (
            "[tool.mcp-coder.setup]\n"
            'steps = [{ argv = ["npm", "ci"], name = "deps" }, '
            '{ builtin = "python" }]\n'
        )
        ok, lines = _run(tmp_path, content, capsys)
        assert ok is False
        assert lines[1] == _format_row("", "[ERR]", "deps: 'npm' not found", indent=6)
        resolver.assert_called_once_with("npm", tmp_path, path=None)


class TestUnresolvedAfterPython:
    """After the python built-in, argv[0] is looked up venv-first."""

    @pytest.mark.usefixtures("no_venv")
    def test_no_venv_interpreter_is_warning(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resolver.return_value = None
        ok, lines = _run(tmp_path, _PYTHON_THEN_LINT, capsys)
        assert ok is True
        assert lines == [
            _format_row("Setup", "[WARN]", "2 step(s) from mcp-coder.toml", indent=4),
            _format_row(
                "", "[WARN]", "pre-commit install: 'pre-commit' not found", indent=6
            ),
        ]
        resolver.assert_called_once_with(
            "pre-commit", tmp_path, path=venv_search_path(tmp_path)
        )

    @pytest.mark.usefixtures("with_venv")
    def test_with_venv_interpreter_is_error(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        resolver.return_value = None
        ok, lines = _run(tmp_path, _PYTHON_THEN_LINT, capsys)
        assert ok is False
        assert "[ERR]" in lines[0]
        assert lines[1] == _format_row(
            "", "[ERR]", "pre-commit install: 'pre-commit' not found", indent=6
        )
        resolver.assert_called_once_with(
            "pre-commit", tmp_path, path=venv_search_path(tmp_path)
        )

    @pytest.mark.usefixtures("with_venv")
    def test_resolved_is_ok(
        self,
        tmp_path: Path,
        resolver: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ok, lines = _run(tmp_path, _PYTHON_THEN_LINT, capsys)
        assert ok is True
        assert lines == [
            _format_row("Setup", "[OK]", "2 step(s) from mcp-coder.toml", indent=4)
        ]


@pytest.mark.usefixtures("no_venv")
class TestProjectSectionWiring:
    """The PROJECT section shows the Setup row in both branches."""

    @pytest.fixture(autouse=True)
    def _no_toolkit_verify(self) -> Generator[None, None, None]:
        with patch(
            "mcp_coder.cli.commands.verify_sections.verify_toolkit",
            lambda _l, _p, _a: [],
        ):
            yield

    @pytest.mark.parametrize(
        ("pyproject", "indent", "summary"),
        [(False, 2, "nothing to do"), (True, 4, "default: python built-in")],
    )
    def test_setup_row_present(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        pyproject: bool,
        indent: int,
        summary: str,
    ) -> None:
        if pyproject:
            (tmp_path / "pyproject.toml").write_text("[tool.black]\n", encoding="utf-8")
        _print_project_section(tmp_path, _SYMBOLS, SectionBuilder())
        rows = [
            line
            for line in capsys.readouterr().out.splitlines()
            if line.strip().startswith("Setup ")
        ]
        assert len(rows) == 1
        assert rows[0].startswith(" " * indent + "Setup ")
        assert rows[0].split() == ["Setup", "[OK]", *summary.split()]

    def test_setup_error_fails_section(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[tool.black]\n[tool.mcp-coder.setup]\nbogus = 1\n", encoding="utf-8"
        )
        assert _print_project_section(tmp_path, _SYMBOLS, SectionBuilder()) is False
        assert "bogus" in capsys.readouterr().out
