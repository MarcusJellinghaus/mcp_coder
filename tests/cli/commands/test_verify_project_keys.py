"""Tests for the unknown / misplaced [tool.mcp-coder] key warnings of verify."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS
from mcp_coder.cli.commands.verify_project_keys import (
    KeyWarning,
    key_warning_rows,
    scan_project_keys,
)
from mcp_coder.cli.commands.verify_render import SectionBuilder
from mcp_coder.cli.commands.verify_sections import _print_project_section
from mcp_coder.utils.toolkit import VerifyItem

from .conftest import _make_args, _make_verify_mocks

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}


def _write(project_dir: Path, file_name: str, content: str) -> None:
    (project_dir / file_name).write_text(content, encoding="utf-8")


def _squash(text: str) -> str:
    """Remove all whitespace, so wrapped rows compare like single lines."""
    return "".join(text.split())


class TestScanProjectKeys:
    """scan_project_keys reports one warning per problem, labelled by file."""

    @pytest.mark.parametrize("file_name", ["pyproject.toml", "mcp-coder.toml"])
    def test_unknown_top_level_table_gets_hint(
        self, tmp_path: Path, file_name: str
    ) -> None:
        _write(tmp_path, file_name, "[tool.mcp-coder.setpu]\nx = 1\n")

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        warning = warnings[0]
        assert warning.section == "PROJECT"
        assert warning.file == file_name
        assert "setpu" in warning.message
        assert "did you mean setup?" in warning.message

    def test_unknown_prompts_key_is_a_prompts_warning(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "pyproject.toml",
            '[tool.mcp-coder.prompts]\nproject_prompt = "p.md"\n',
        )

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].section == "PROMPTS"
        assert warnings[0].file == "pyproject.toml"
        assert "project_prompt" in warnings[0].message
        assert "did you mean project-prompt?" in warnings[0].message

    def test_retired_implement_key_in_pyproject(self, tmp_path: Path) -> None:
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder.implement]\nfoo = 1\n")

        warnings = scan_project_keys(tmp_path)

        assert warnings == [
            KeyWarning(
                "PROJECT",
                "pyproject.toml",
                "[tool.mcp-coder.implement] foo is retired and ignored",
            )
        ]

    def test_legacy_implement_keys_have_their_own_rows(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.implement]\nformat_code = true\ncheck_type_hints = true\n",
        )

        assert not scan_project_keys(tmp_path)

    def test_implement_table_in_mcp_coder_toml_is_retired(self, tmp_path: Path) -> None:
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder.implement]\n")

        warnings = scan_project_keys(tmp_path)

        assert warnings == [
            KeyWarning(
                "PROJECT",
                "mcp-coder.toml",
                "[tool.mcp-coder.implement] is retired and ignored",
            )
        ]

    def test_install_in_mcp_coder_toml_is_python_only(self, tmp_path: Path) -> None:
        _write(tmp_path, "mcp-coder.toml", '[tool.mcp-coder.install]\nextra = "x"\n')

        warnings = scan_project_keys(tmp_path)

        assert warnings == [
            KeyWarning(
                "PROJECT",
                "mcp-coder.toml",
                "[tool.mcp-coder.install] is Python-only; ignored in mcp-coder.toml",
            )
        ]

    def test_unknown_install_key_in_pyproject(self, tmp_path: Path) -> None:
        _write(tmp_path, "pyproject.toml", '[tool.mcp-coder.install]\nextra = "x"\n')

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].section == "PROJECT"
        assert "unknown key [tool.mcp-coder.install] extra" in warnings[0].message
        assert "did you mean extras?" in warnings[0].message

    def test_malformed_mcp_coder_toml(self, tmp_path: Path) -> None:
        _write(tmp_path, "mcp-coder.toml", "[tool.mcp-coder\n")

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].section == "PROJECT"
        assert warnings[0].file == "mcp-coder.toml"
        assert "cannot be parsed" in warnings[0].message

    def test_non_table_mcp_coder_is_reported_as_unparseable(
        self, tmp_path: Path
    ) -> None:
        _write(tmp_path, "pyproject.toml", '[tool]\nmcp-coder = "x"\n')

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].file == "pyproject.toml"
        assert "cannot be parsed" in warnings[0].message

    @pytest.mark.parametrize(
        "value", ["1", '"format_code"', '["format_code"]'], ids=["int", "str", "list"]
    )
    def test_non_table_implement_in_pyproject_is_retired(
        self, tmp_path: Path, value: str
    ) -> None:
        _write(tmp_path, "pyproject.toml", f"[tool.mcp-coder]\nimplement = {value}\n")

        warnings = scan_project_keys(tmp_path)

        assert warnings == [
            KeyWarning(
                "PROJECT",
                "pyproject.toml",
                "[tool.mcp-coder.implement] is retired and ignored",
            )
        ]

    @pytest.mark.parametrize("key", ["install", "install-from-github"])
    def test_non_table_python_only_key_in_pyproject_is_not_a_table(
        self, tmp_path: Path, key: str
    ) -> None:
        _write(tmp_path, "pyproject.toml", f"[tool.mcp-coder]\n{key} = 1\n")

        warnings = scan_project_keys(tmp_path)

        assert warnings == [
            KeyWarning(
                "PROJECT", "pyproject.toml", f"[tool.mcp-coder.{key}] is not a table"
            )
        ]

    def test_non_table_prompts_has_no_project_warning(self, tmp_path: Path) -> None:
        _write(tmp_path, "pyproject.toml", "[tool.mcp-coder]\nprompts = 1\n")

        warnings = scan_project_keys(tmp_path)

        assert not [w for w in warnings if w.section == "PROJECT"]

    def test_format_code_in_both_files_conflicts(self, tmp_path: Path) -> None:
        for file_name in ("pyproject.toml", "mcp-coder.toml"):
            _write(tmp_path, file_name, "[tool.mcp-coder]\nformat_code = true\n")

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].section == "PROJECT"
        assert warnings[0].file == "mcp-coder.toml"
        assert "format_code is defined in both" in warnings[0].message

    def test_prompts_in_both_files_conflicts(self, tmp_path: Path) -> None:
        for file_name in ("pyproject.toml", "mcp-coder.toml"):
            _write(
                tmp_path,
                file_name,
                '[tool.mcp-coder.prompts]\nclaude-system-prompt-mode = "append"\n',
            )

        warnings = scan_project_keys(tmp_path)

        assert len(warnings) == 1
        assert warnings[0].section == "PROMPTS"
        assert "prompts is defined in both" in warnings[0].message

    def test_valid_config_has_no_warnings(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder]\n"
            "format_code = true\n"
            '[tool.mcp-coder.prompts]\nsystem-prompt = "s.md"\n'
            'project-prompt = "p.md"\nclaude-system-prompt-mode = "append"\n'
            '[tool.mcp-coder.install]\nextras = ["dev"]\n'
            'post_install_checks = [["mcp-coder", "--version"]]\n'
            '[tool.mcp-coder.install-from-github]\npackages = ["a"]\n'
            'packages-no-deps = ["b"]\n',
        )
        _write(
            tmp_path,
            "mcp-coder.toml",
            "[tool.mcp-coder]\n"
            'labels-config = "labels.json"\n'
            '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n'
            "[tool.mcp-coder.setup]\n",
        )

        assert not scan_project_keys(tmp_path)

    def test_no_files_no_warnings(self, tmp_path: Path) -> None:
        assert not scan_project_keys(tmp_path)


class TestKeyWarningRows:
    """key_warning_rows keeps only the rows of the requested section."""

    def test_rows_filtered_by_section(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "pyproject.toml",
            "[tool.mcp-coder.setpu]\n[tool.mcp-coder.prompts]\nproject_prompt = 1\n",
        )

        rows = key_warning_rows(tmp_path, "PROMPTS", _SYMBOLS)

        assert len(rows) == 1
        assert rows[0].label == "pyproject.toml"
        assert rows[0].marker == "[WARN]"
        assert "project_prompt" in rows[0].value
        assert rows[0].wrap


@pytest.fixture
def _stub_toolkit() -> Generator[None, None, None]:
    """Stub the toolkit registry and verify so only the formatter item reports."""
    from mcp_tools_py.toolkit import PythonToolkit

    with (
        patch(
            "mcp_coder.utils.toolkit_runner._toolkit_class",
            lambda _name: PythonToolkit,
        ),
        patch(
            "mcp_coder.cli.commands.verify_toolkit_rows.verify_toolkit",
            lambda _l, _p, a: [VerifyItem("formatter", "ok")] if a == "format" else [],
        ),
    ):
        yield


@pytest.mark.usefixtures("_stub_toolkit")
class TestProjectSectionWarnings:
    """PROJECT shows the warnings; they never change the section result."""

    @pytest.mark.parametrize("file_name", ["pyproject.toml", "mcp-coder.toml"])
    def test_unknown_table_warns_without_changing_result(
        self,
        tmp_path: Path,
        file_name: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        good, bad = tmp_path / "good", tmp_path / "bad"
        good.mkdir()
        bad.mkdir()
        _write(good, file_name, "[tool.mcp-coder]\nformat_code = true\n")
        _write(
            bad,
            file_name,
            "[tool.mcp-coder]\nformat_code = true\n[tool.mcp-coder.setpu]\n",
        )

        ok_good = _print_project_section(good, _SYMBOLS, SectionBuilder())
        good_out = capsys.readouterr().out
        ok_bad = _print_project_section(bad, _SYMBOLS, SectionBuilder())
        bad_out = capsys.readouterr().out

        assert ok_bad == ok_good
        assert "setpu" not in good_out
        warn_rows = [line for line in bad_out.splitlines() if "setpu" in line]
        assert len(warn_rows) == 1
        assert "[WARN]" in warn_rows[0]
        assert file_name in warn_rows[0]
        assert "didyoumeansetup?" in _squash(bad_out)


def _prompts_section(output: str) -> list[str]:
    """Return the PROMPTS section lines, section header excluded."""
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("=== PROMPTS "))
    section: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("=== "):
            break
        section.append(line)
    return section


def _run_verify(
    project_dir: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[int, list[str]]:
    """Run execute_verify on *project_dir*; return exit code and PROMPTS lines."""
    with _make_verify_mocks():
        exit_code = execute_verify(_make_args(project_dir=str(project_dir)))
    return exit_code, _prompts_section(capsys.readouterr().out)


class TestPromptsSectionWarnings:
    """PROMPTS shows its warnings; the exit code stays unchanged."""

    def test_unknown_prompts_key_warns_with_same_exit_code(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        good, bad = tmp_path / "good", tmp_path / "bad"
        good.mkdir()
        bad.mkdir()
        _write(
            good,
            "pyproject.toml",
            '[tool.mcp-coder.prompts]\nclaude-system-prompt-mode = "append"\n',
        )
        _write(
            bad,
            "pyproject.toml",
            '[tool.mcp-coder.prompts]\nclaude-system-prompt-mode = "append"\n'
            'project_prompt = "p.md"\n',
        )

        good_code, good_section = _run_verify(good, capsys)
        bad_code, bad_section = _run_verify(bad, capsys)

        assert bad_code == good_code
        assert not any("project_prompt" in line for line in good_section)
        warn_rows = [
            line
            for line in bad_section
            if line.strip().startswith("pyproject.toml")
            and STATUS_SYMBOLS["warning"] in line
        ]
        assert len(warn_rows) == 1
        squashed = _squash("\n".join(bad_section))
        assert "unknownkey[tool.mcp-coder.prompts]project_prompt" in squashed
        assert "didyoumeanproject-prompt?" in squashed
