"""Tests for validate_target_repo, the launch-time target-repo contract."""

import logging
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.session_launch import validate_target_repo

_LOGGER_NAME = "mcp_coder.workflows.vscodeclaude.session_launch"

_COMPLIANT_PYPROJECT = """\
[tool.mcp-coder.install]
extras = "dev"

[tool.mcp-coder.install-from-github]
packages = ["mcp-tools-py"]
"""


@pytest.fixture(autouse=True)
def _windows_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the platform so the expected MCP config filename is deterministic."""
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
        lambda: "Windows",
    )


def _make_compliant_repo(folder_path: Path) -> None:
    """Create a target repo satisfying every row of the contract."""
    (folder_path / ".mcp.json").write_text("{}", encoding="utf-8")
    (folder_path / "pyproject.toml").write_text(_COMPLIANT_PYPROJECT, encoding="utf-8")
    venv = folder_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr\n", encoding="utf-8")


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return the messages logged at WARNING or above."""
    return [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING
    ]


class TestFatalRow:
    """The .mcp.json row stays fatal and unchanged."""

    def test_missing_mcp_json_raises(self, tmp_path: Path) -> None:
        """A repo without the platform MCP config aborts the launch."""
        with pytest.raises(FileNotFoundError, match=r"\.mcp\.json"):
            validate_target_repo(tmp_path)


class TestCompliantRepo:
    """A fully compliant repo passes silently."""

    def test_no_warnings(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Every row satisfied means no warning is logged."""
        _make_compliant_repo(tmp_path)

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        assert _warnings(caplog) == []

    def test_empty_extras_counts_as_declared(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """``extras = ""`` is a declaration, not an absence."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install]\nextras = ""\n\n'
            '[tool.mcp-coder.install-from-github]\npackages = ["mcp-tools-py"]\n',
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        assert _warnings(caplog) == []


class TestWarnOnlyRows:
    """Each warn-only row logs exactly one warning and never raises."""

    def test_no_extras_declared(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing extras key warns about the 'dev' fallback."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install-from-github]\npackages = ["mcp-tools-py"]\n',
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "extras" in messages[0]
        assert "dev" in messages[0]

    def test_no_github_install_section(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing install-from-github section warns about sibling pinning."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install]\nextras = "dev"\n', encoding="utf-8"
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "install-from-github" in messages[0]

    def test_venv_without_pyvenv_cfg(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An empty or broken .venv warns."""
        _make_compliant_repo(tmp_path)
        (tmp_path / ".venv" / "pyvenv.cfg").unlink()

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "pyvenv.cfg" in messages[0]

    def test_second_venv_directory(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A venv/ directory alongside .venv warns."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "venv").mkdir()

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert ".venv" in messages[0]

    def test_missing_venv_is_not_a_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No .venv at all is fine - the installer creates it."""
        _make_compliant_repo(tmp_path)
        (tmp_path / ".venv" / "pyvenv.cfg").unlink()
        (tmp_path / ".venv").rmdir()

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        assert _warnings(caplog) == []


class TestMissingPyproject:
    """A repo without pyproject.toml warns twice but launches."""

    def test_warns_both_toml_rows(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Both TOML-declared rows warn; nothing raises."""
        (tmp_path / ".mcp.json").write_text("{}", encoding="utf-8")

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 2
        assert any("extras" in message for message in messages)
        assert any("install-from-github" in message for message in messages)


class TestUnreadablePyproject:
    """An unreadable pyproject.toml is named, not reported as absent policy."""

    def test_malformed_toml_warns_about_the_parse_error(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """One warning naming the file and the parse error, not two 'no ...' rows."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "this is not valid toml {{{", encoding="utf-8"
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "pyproject.toml" in messages[0]
        assert "TOML parse error" in messages[0]
        assert "declares no" not in messages[0]

    def test_non_list_packages_warns_about_the_type(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A string where a list of specs belongs is reported at launch."""
        _make_compliant_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            '[tool.mcp-coder.install]\nextras = "dev"\n\n'
            "[tool.mcp-coder.install-from-github]\n"
            'packages = "mcp-tools-py @ git+https://host/pkg.git"\n',
            encoding="utf-8",
        )

        with caplog.at_level(logging.WARNING, logger=_LOGGER_NAME):
            validate_target_repo(tmp_path)

        messages = _warnings(caplog)
        assert len(messages) == 1
        assert "install-from-github" in messages[0]
        assert "packages" in messages[0]
