"""Unit tests for tools/jenkins_builds.py (JenkinsClient mocked)."""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsError
from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_builds = importlib.import_module("jenkins_builds")

_FULL_CONFIG: dict[str, str | None] = {
    "server_url": "https://jenkins.example.com",
    "username": "user",
    "api_token": "token",
}


def _build(job_path: str, number: int, status: str, ts: datetime) -> BuildInfo:
    folder, _, job_name = job_path.rpartition("/")
    return BuildInfo(
        job_path=job_path,
        folder=folder,
        job_name=job_name,
        number=number,
        status=status,
        timestamp=ts,
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    jenkins_builds.add_selection_args(parser, default_status=None)
    return parser


def test_parse_defaults() -> None:
    args = _parser().parse_args([])
    assert args.limit == 100
    assert args.folder is None
    assert args.status is None


def test_parse_status_list_lowercased() -> None:
    args = _parser().parse_args(["--status", "failure,ABORTED"])
    assert args.status == ["failure", "aborted"]


def test_parse_invalid_status_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        _parser().parse_args(["--status", "failed"])
    assert exc_info.value.code == 2
    err = capsys.readouterr().err
    for status in VALID_STATUSES:
        assert status in err


@pytest.mark.parametrize("limit", ["0", "-5"])
def test_parse_limit_below_one_exits_2(
    limit: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        _parser().parse_args(["--limit", limit])
    assert exc_info.value.code == 2
    assert "--limit" in capsys.readouterr().err


def test_help_lists_statuses_and_slow_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        jenkins_builds.main(["--help"])
    out = " ".join(capsys.readouterr().out.split())
    for status in VALID_STATUSES:
        assert status in out
    assert "may be slow" in out


def test_main_passes_arguments(client: MagicMock) -> None:
    rc = jenkins_builds.main(
        ["--limit", "5", "--folder", "A/B", "--status", "failure,unstable"]
    )
    assert rc == 0
    client.get_recent_builds.assert_called_once_with(
        limit=5, folder="A/B", statuses=["failure", "unstable"]
    )


def test_main_prints_table(
    client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    ts1 = datetime(2026, 10, 1, 12, 30, tzinfo=UTC)
    ts2 = datetime(2026, 9, 30, 8, 5, tzinfo=UTC)
    client.get_recent_builds.return_value = [
        _build("Windows-Agents/CD/Rebuild", 42, "failure", ts1),
        _build("top-job", 7, "success", ts2),
    ]
    rc = jenkins_builds.main([])
    assert rc == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 3
    assert lines[0].split() == ["TIME", "STATUS", "FOLDER", "JOB", "BUILD"]
    assert lines[1].startswith(ts1.astimezone().strftime("%Y-%m-%d %H:%M"))
    assert "failure" in lines[1]
    assert "Windows-Agents/CD" in lines[1]
    assert "Rebuild" in lines[1]
    assert lines[1].endswith("42")
    assert lines[2].startswith(ts2.astimezone().strftime("%Y-%m-%d %H:%M"))
    assert "top-job" in lines[2]
    assert lines[2].endswith("7")


def test_main_no_builds(client: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    client.get_recent_builds.return_value = []
    assert jenkins_builds.main([]) == 0
    assert capsys.readouterr().out.strip() == "No builds found."


def test_main_jenkins_error(
    client: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    client.get_recent_builds.side_effect = JenkinsError("folder not found")
    assert jenkins_builds.main([]) == 1
    assert "folder not found" in capsys.readouterr().err


def test_main_missing_token(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        jenkins_builds,
        "get_jenkins_config",
        lambda: {**_FULL_CONFIG, "api_token": None},
    )
    client_cls = MagicMock()
    monkeypatch.setattr(jenkins_builds, "JenkinsClient", client_cls)
    assert jenkins_builds.main([]) == 1
    err = capsys.readouterr().err
    assert "JENKINS_TOKEN" in err
    assert "JENKINS_URL" not in err
    client_cls.assert_not_called()
