"""Tests for the error raised when no toolkit is configured."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_coder.cli.commands.verify_sections import _print_project_section
from mcp_coder.utils import toolkit_runner
from mcp_coder.utils.mcp_verification import required_mcp_servers
from mcp_coder.utils.toolkit_runner import (
    _CONFIGURE_URL,
    llm_permissions,
    load_toolkit,
    load_toolkit_config,
)
from mcp_coder.utils.verify_render import SectionBuilder
from mcp_coder.workflow_steps.commit import check_formatter_config

pytestmark = pytest.mark.real_toolkit_config

_SYMBOLS = {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}
_PYTHON_SNIPPET = '[tool.mcp-coder.toolkit] toolkit = "mcp-tools-py"'
_COMMAND_SNIPPET = '[tool.mcp-coder.toolkit] toolkit = "command"'
_NO_TABLE = "No [tool.mcp-coder.toolkit] table in pyproject.toml or mcp-coder.toml."


def _write(directory: Path, name: str, content: str) -> None:
    (directory / name).write_text(content, encoding="utf-8")


def _assert_help(message: str) -> None:
    """The message carries both snippets, the command pointer and the link."""
    assert _PYTHON_SNIPPET in message
    assert _COMMAND_SNIPPET in message
    assert "[tool.mcp-coder.toolkit.command] step tables" in message
    assert _CONFIGURE_URL in message
    assert "\n" not in message


class TestLoadToolkitConfig:
    """load_toolkit_config raises instead of falling back to a default."""

    def test_no_table(self, tmp_path: Path) -> None:
        """No config file → the no-table error."""
        with pytest.raises(ValueError) as excinfo:
            load_toolkit_config(tmp_path)
        message = str(excinfo.value)
        assert message.startswith(_NO_TABLE)
        _assert_help(message)

    def test_bindings_only(self, tmp_path: Path) -> None:
        """A table with only bindings → the no-key error, not "Unknown key"."""
        _write(
            tmp_path,
            "pyproject.toml",
            '[tool.mcp-coder.toolkit.bindings]\nrebase = ["check@full"]\n',
        )
        with pytest.raises(ValueError) as excinfo:
            load_toolkit_config(tmp_path)
        message = str(excinfo.value)
        assert message.startswith(
            "[tool.mcp-coder.toolkit] in pyproject.toml has no toolkit key."
        )
        assert "Unknown" not in message
        _assert_help(message)

    def test_bindings_with_command_subtable(self, tmp_path: Path) -> None:
        """A command subtable without the key → the no-key error, not "Unknown key 'command'"."""
        _write(
            tmp_path,
            "mcp-coder.toml",
            '[tool.mcp-coder.toolkit.bindings]\nrebase = ["check@full"]\n'
            '[tool.mcp-coder.toolkit.command.format]\napply = ["fmt"]\n',
        )
        with pytest.raises(ValueError) as excinfo:
            load_toolkit_config(tmp_path)
        message = str(excinfo.value)
        assert message.startswith(
            "[tool.mcp-coder.toolkit] in mcp-coder.toml has no toolkit key."
        )
        assert "Unknown" not in message
        _assert_help(message)


def test_verify_project_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """verify's PROJECT section shows an [ERR] Toolkit row and fails."""
    assert _print_project_section(tmp_path, _SYMBOLS, SectionBuilder()) is False
    lines = capsys.readouterr().out.splitlines()
    toolkit = [line for line in lines if line.strip().startswith("Toolkit ")]
    assert len(toolkit) == 1
    assert "[ERR]" in toolkit[0]
    assert _NO_TABLE in toolkit[0]


def test_format_preflight(tmp_path: Path) -> None:
    """The format pre-flight reports the error."""
    message = check_formatter_config(tmp_path)
    assert message is not None
    assert message.startswith(_NO_TABLE)


def test_llm_permissions_and_required_servers(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """No grants (with a warning); only mcp-workspace is required."""
    assert llm_permissions(tmp_path, "claude") == []
    assert _NO_TABLE in caplog.text
    assert required_mcp_servers(tmp_path) == ["mcp-workspace"]


def test_python_toolkit_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """toolkit = "mcp-tools-py" without the extra → the python-extra hint."""
    _write(
        tmp_path,
        "pyproject.toml",
        '[tool.mcp-coder.toolkit]\ntoolkit = "mcp-tools-py"\n',
    )
    command = SimpleNamespace(name="command")
    monkeypatch.setattr(toolkit_runner, "entry_points", lambda **_: [command])
    with pytest.raises(ValueError, match=r"mcp-coder\[python\]"):
        load_toolkit(tmp_path)
