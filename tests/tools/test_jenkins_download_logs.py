"""Tests for tools/jenkins_download_logs.py (unit tests mock JenkinsClient)."""

from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsClient, JenkinsError
from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_builds = importlib.import_module("jenkins_builds")
jenkins_download_logs = importlib.import_module("jenkins_download_logs")

_FULL_CONFIG: dict[str, str | None] = {
    "server_url": "https://jenkins.example.com",
    "username": "user",
    "api_token": "token",
}


def _build(job_path: str, number: int) -> BuildInfo:
    folder, _, job_name = job_path.rpartition("/")
    return BuildInfo(
        job_path=job_path,
        folder=folder,
        job_name=job_name,
        number=number,
        status="failure",
        timestamp=datetime(2026, 10, 1, 12, 0, tzinfo=UTC),
        duration_ms=1000,
        url=f"https://jenkins.example.com/job/{job_path}/{number}/",
    )


@pytest.fixture(name="client")
def fixture_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch config and JenkinsClient; return the client instance mock."""
    monkeypatch.setattr(jenkins_builds, "get_jenkins_config", lambda: _FULL_CONFIG)
    client_cls = MagicMock()
    instance: MagicMock = client_cls.return_value
    instance.get_recent_builds.return_value = []
    monkeypatch.setattr(jenkins_builds, "JenkinsClient", client_cls)
    return instance


def test_default_status(client: MagicMock, tmp_path: Path) -> None:
    assert jenkins_download_logs.main(["--outdir", str(tmp_path)]) == 0
    client.get_recent_builds.assert_called_once_with(
        limit=100, folder=None, statuses=["failure", "aborted", "unstable"]
    )


def test_invalid_status_exits_2(client: MagicMock) -> None:
    with pytest.raises(SystemExit) as exc_info:
        jenkins_download_logs.main(["--status", "failed"])
    assert exc_info.value.code == 2
    client.get_recent_builds.assert_not_called()


def test_writes_one_file_per_build(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client.get_recent_builds.return_value = [_build("A/B/job", 5), _build("top", 7)]
    client.get_console_output.side_effect = lambda job_path, number: (
        f"log {job_path} #{number}"
    )
    assert jenkins_download_logs.main(["--outdir", str(tmp_path)]) == 0
    first = tmp_path / "A_B_job_5.txt"
    second = tmp_path / "top_7.txt"
    assert first.read_text(encoding="utf-8") == "log A/B/job #5"
    assert second.read_text(encoding="utf-8") == "log top #7"
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == [str(first), str(second)]


def test_overwrites_existing_file(client: MagicMock, tmp_path: Path) -> None:
    target = tmp_path / "A_B_job_5.txt"
    target.write_text("old content that is longer", encoding="utf-8")
    client.get_recent_builds.return_value = [_build("A/B/job", 5)]
    client.get_console_output.return_value = "new"
    assert jenkins_download_logs.main(["--outdir", str(tmp_path)]) == 0
    assert target.read_text(encoding="utf-8") == "new"


def test_creates_missing_nested_outdir(client: MagicMock, tmp_path: Path) -> None:
    outdir = tmp_path / "a" / "b"
    client.get_recent_builds.return_value = [_build("A/B/job", 5)]
    client.get_console_output.return_value = "log"
    assert jenkins_download_logs.main(["--outdir", str(outdir)]) == 0
    assert (outdir / "A_B_job_5.txt").read_text(encoding="utf-8") == "log"


def test_console_output_error_returns_1(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client.get_recent_builds.return_value = [_build("A/B/job", 5)]
    client.get_console_output.side_effect = JenkinsError("build not found")
    assert jenkins_download_logs.main(["--outdir", str(tmp_path)]) == 1
    assert "build not found" in capsys.readouterr().err


def test_outdir_is_existing_file_returns_1(
    client: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outdir = tmp_path / "not_a_dir"
    outdir.write_text("x", encoding="utf-8")
    client.get_recent_builds.return_value = [_build("A/B/job", 5)]
    client.get_console_output.return_value = "log"
    assert jenkins_download_logs.main(["--outdir", str(outdir)]) == 1
    assert "not_a_dir" in capsys.readouterr().err


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
    assert jenkins_download_logs.main(["--outdir", str(tmp_path)]) == 1
    assert "JENKINS_USER" in capsys.readouterr().err
    client_cls.assert_not_called()


@pytest.mark.jenkins_integration
def test_end_to_end_downloads_log(
    jenkins_client: JenkinsClient,
    jenkins_test_setup: dict[str, str],
    tmp_path: Path,
) -> None:
    test_job = jenkins_test_setup["test_job"]
    parent = test_job.rpartition("/")[0] or None
    if not jenkins_client.get_recent_builds(limit=1, folder=parent):
        pytest.skip("no builds in test_job's folder")
    argv = [
        "--limit",
        "1",
        "--status",
        ",".join(VALID_STATUSES),
        "--outdir",
        str(tmp_path),
    ] + (["--folder", parent] if parent else [])
    assert jenkins_download_logs.main(argv) == 0
    files = list(tmp_path.glob("*.txt"))
    assert len(files) == 1
    assert files[0].stat().st_size > 0
