"""Tests for validate_target_repo's gate on the ``python`` setup built-in."""

import logging
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.session_launch import validate_target_repo

_LOGGER_NAME = "mcp_coder.workflows.vscodeclaude.session_launch"

_NPM_SETUP = '[tool.mcp-coder.setup]\nsteps = [{ argv = ["npm", "ci"] }]\n'


@pytest.fixture(autouse=True)
def _windows_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the platform so the expected MCP config filename is deterministic."""
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
        lambda: "Windows",
    )


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the messages logged at WARNING or above."""
    return [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING
    ]


def _write_mcp_json(folder_path: Path) -> None:
    """Create the platform MCP config so the fatal row passes."""
    (folder_path / ".mcp.json").write_text("{}", encoding="utf-8")


class TestNonPythonSetup:
    """Setup steps without the python built-in skip every Python row."""

    def test_npm_setup_in_mcp_coder_toml_without_pyproject(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An npm repo configured in mcp-coder.toml gets no Python warnings."""
        _write_mcp_json(tmp_path)
        (tmp_path / "mcp-coder.toml").write_text(_NPM_SETUP, encoding="utf-8")
        (tmp_path / "venv").mkdir()

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        assert _warnings(caplog) == []

    def test_npm_setup_in_pyproject(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A pyproject.toml whose setup steps skip python gets no Python warnings."""
        _write_mcp_json(tmp_path)
        (tmp_path / "pyproject.toml").write_text(_NPM_SETUP, encoding="utf-8")

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        assert _warnings(caplog) == []


class TestDefaultPythonSetup:
    """A pyproject.toml without the setup table keeps the Python rows."""

    def test_missing_extras_still_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The default python built-in keeps the extras warning."""
        _write_mcp_json(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install-from-github]\npackages = ["mcp-tools-py"]\n',
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "extras" in messages[0]


class TestBrokenSetupConfig:
    """A broken setup table warns once and the launch continues."""

    def test_invalid_setup_table_warns_once(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unknown builtin is named in one warning; nothing raises."""
        _write_mcp_json(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.setup]\nsteps = [{ builtin = "rust" }]\n',
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "[tool.mcp-coder.setup]" in messages[0]
        assert "mcp-coder setup" in messages[0]
        assert "steps[0].builtin" in messages[0]

    def test_malformed_pyproject_is_not_blamed_on_setup_table(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unparseable pyproject.toml is reported as unreadable, once."""
        _write_mcp_json(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "this is not valid toml {{{", encoding="utf-8"
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert f"{tmp_path / 'pyproject.toml'} cannot be read" in messages[0]
        assert "TOML parse error" in messages[0]
        assert "[tool.mcp-coder.setup]" not in messages[0]

    def test_missing_mcp_json_still_raises(self, tmp_path: Path) -> None:
        """A broken setup table does not mask the fatal MCP config row."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.setup]\nsteps = [{ builtin = "rust" }]\n',
            encoding="utf-8",
        )

        with pytest.raises(FileNotFoundError, match=r"\.mcp\.json"):
            validate_target_repo(tmp_path)
