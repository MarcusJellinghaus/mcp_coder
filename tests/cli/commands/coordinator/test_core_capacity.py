"""Tests for find_waiting_build, the executor capacity signal."""

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from mcp_coder.cli.commands.coordinator.core import find_waiting_build
from mcp_coder.utils.jenkins_operations.client import JenkinsError
from mcp_coder.utils.jenkins_operations.models import BuildInfo

JOB_PATH = "Windows-Agents/Executor"
LOGGER_NAME = "mcp_coder.cli.commands.coordinator.core"


def _build(number: int, display_name: str, minutes_ago: float) -> BuildInfo:
    return BuildInfo(
        job_path=JOB_PATH,
        folder="Windows-Agents",
        job_name="Executor",
        number=number,
        status="running",
        timestamp=datetime.now(UTC) - timedelta(minutes=minutes_ago),
        duration_ms=None,
        url=f"https://jenkins.example.com/job/Windows-Agents/job/Executor/{number}/",
        display_name=display_name,
    )


def _client(builds: list[BuildInfo]) -> MagicMock:
    client = MagicMock()
    client.get_recent_builds.return_value = builds
    return client


def _records(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == LOGGER_NAME and r.levelno == level]


def test_no_running_builds_returns_none() -> None:
    client = _client([])

    assert find_waiting_build(client, JOB_PATH) is None
    client.get_recent_builds.assert_called_once_with(
        path=JOB_PATH, statuses=["running"]
    )


def test_all_renamed_returns_none_without_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _client(
        [
            _build(12, "mcp_coder - #12 - implement", 5),
            _build(11, "mcp_coder - #11 - create-plan", 10),
        ]
    )

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        assert find_waiting_build(client, JOB_PATH) is None

    assert not _records(caplog, logging.INFO)


def test_unnamed_build_is_returned_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    waiting = _build(42, "#42", 2)
    client = _client([_build(43, "mcp_coder - #7 - implement", 1), waiting])

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        assert find_waiting_build(client, JOB_PATH) == waiting

    infos = _records(caplog, logging.INFO)
    assert len(infos) == 1
    assert "#42" in infos[0].getMessage()
    assert JOB_PATH in infos[0].getMessage()


def test_empty_display_name_counts_as_waiting() -> None:
    waiting = _build(42, "", 2)
    client = _client([waiting])

    assert find_waiting_build(client, JOB_PATH) == waiting


def test_oldest_waiting_build_is_returned() -> None:
    newer = _build(45, "#45", 1)
    older = _build(44, "#44", 3)
    client = _client([newer, older])

    assert find_waiting_build(client, JOB_PATH) == older


def test_warning_for_build_unnamed_over_60_minutes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _client([_build(42, "#42", 61)])

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        find_waiting_build(client, JOB_PATH)

    warnings = _records(caplog, logging.WARNING)
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "still unnamed after" in message
    assert "manual build without LABEL" in message
    assert not _records(caplog, logging.ERROR)


def test_no_warning_for_build_unnamed_under_60_minutes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _client([_build(42, "#42", 59)])

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        find_waiting_build(client, JOB_PATH)

    assert not _records(caplog, logging.WARNING)
    assert not _records(caplog, logging.ERROR)


def test_jenkins_error_propagates() -> None:
    client = MagicMock()
    error = JenkinsError("boom")
    client.get_recent_builds.side_effect = error

    with pytest.raises(JenkinsError) as exc_info:
        find_waiting_build(client, JOB_PATH)

    assert exc_info.value is error
