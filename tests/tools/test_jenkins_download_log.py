"""Unit tests for tools/jenkins_download_log.py (JenkinsClient mocked)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.jenkins_operations import JenkinsError
from tests.tools.conftest import _FULL_CONFIG

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_builds = importlib.import_module("jenkins_builds")
jenkins_download_log = importlib.import_module("jenkins_download_log")


def test_writes_log_and_prints_path(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "log.txt"
    client.get_console_output.return_value = "log ✓"
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 0
    client.get_console_output.assert_called_once_with("A/B/job", 5)
    assert target.read_text(encoding="utf-8") == "log ✓"
    assert capsys.readouterr().out.strip() == str(target)


def test_creates_missing_parent_dirs(client: MagicMock, tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "log.txt"
    client.get_console_output.return_value = "log text"
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == "log text"


def test_overwrites_existing_file(client: MagicMock, tmp_path: Path) -> None:
    target = tmp_path / "log.txt"
    target.write_text("old content that is longer", encoding="utf-8")
    client.get_console_output.return_value = "new"
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == "new"


def test_jenkins_error_returns_1_and_writes_nothing(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "a" / "b" / "log.txt"
    client.get_console_output.side_effect = JenkinsError("build not found")
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 1
    assert "build not found" in capsys.readouterr().err
    assert not (tmp_path / "a").exists()


def test_output_file_is_directory_returns_1(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "existing_dir"
    target.mkdir()
    client.get_console_output.return_value = "log text"
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 1
    assert "existing_dir" in capsys.readouterr().err


def test_missing_config_returns_1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        jenkins_builds,
        "get_jenkins_config",
        lambda: {**_FULL_CONFIG, "username": None},
    )
    client_cls = MagicMock()
    monkeypatch.setattr(jenkins_builds, "JenkinsClient", client_cls)
    target = tmp_path / "log.txt"
    assert jenkins_download_log.main(["A/B/job", "5", str(target)]) == 1
    assert "JENKINS_USER" in capsys.readouterr().err
    client_cls.assert_not_called()


@pytest.mark.parametrize("number", ["0", "abc"])
def test_invalid_number_exits_2(number: str, tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        jenkins_download_log.main(["A/B/job", number, str(tmp_path / "log.txt")])
    assert exc_info.value.code == 2
