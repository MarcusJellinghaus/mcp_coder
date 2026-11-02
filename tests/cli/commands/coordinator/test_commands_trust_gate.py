"""Tests for the issue body-trust gate in execute_coordinator_run."""

import argparse
import logging
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import execute_coordinator_run
from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    GitHubRateLimitError,
    IssueData,
)
from tests.github_factories import make_issue_data

_COMMANDS = "mcp_coder.cli.commands.coordinator.commands"

TRUSTED = BodyTrustResult(status=BodyTrust.TRUSTED, reason="")
UNTRUSTED = BodyTrustResult(status=BodyTrust.UNTRUSTED, reason="author not trusted")
LOOKUP_FAILED = BodyTrustResult(
    status=BodyTrust.LOOKUP_FAILED, reason="ConnectionError"
)


def _issue(number: int, label: str = "status-05:plan-ready") -> IssueData:
    return make_issue_data(number=number, labels=[label])


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        command="coordinator",
        repo="mcp_coder",
        all=False,
        log_level="INFO",
        force_refresh=False,
    )


def _dispatched_numbers(dispatch: MagicMock) -> list[int]:
    return [c.kwargs["issue"]["number"] for c in dispatch.call_args_list]


def _summary_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.INFO and "untrusted body" in r.getMessage()
    ]


@pytest.fixture
def mocks(_trusted_issue_bodies: MagicMock) -> Iterator[dict[str, MagicMock]]:
    """Patch everything around execute_coordinator_run for one repo.

    Yields:
        The patched callables keyed by name.
    """
    repo_config = {
        "repo_url": "https://github.com/user/mcp_coder.git",
        "executor_job_path": "MCP_Coder/executor-test",
        "github_credentials_id": "github-pat-123",
        "executor_os": "linux",
    }
    with (
        patch(f"{_COMMANDS}.create_default_config", return_value=False),
        patch(
            f"{_COMMANDS}.get_jenkins_credentials",
            return_value=("https://jenkins.example.com", "u", "t"),
        ),
        patch(f"{_COMMANDS}.JenkinsClient"),
        patch(f"{_COMMANDS}.load_repo_config", return_value=repo_config),
        patch(f"{_COMMANDS}.IssueManager") as issue_mgr_cls,
        patch(f"{_COMMANDS}.IssueBranchManager"),
        patch(f"{_COMMANDS}.get_cached_eligible_issues") as get_cached,
        patch(f"{_COMMANDS}.get_eligible_issues") as get_eligible,
        patch(f"{_COMMANDS}.dispatch_workflow", return_value=True) as dispatch,
        patch(f"{_COMMANDS}.update_issue_labels_in_cache") as update_cache,
    ):
        yield {
            "trust": _trusted_issue_bodies,
            "issue_mgr": issue_mgr_cls.return_value,
            "get_cached": get_cached,
            "get_eligible": get_eligible,
            "dispatch": dispatch,
            "update_cache": update_cache,
        }


class TestCoordinatorTrustGate:
    """Only issues with a trusted body are dispatched."""

    def test_trusted_dispatched_untrusted_skipped(
        self, mocks: dict[str, MagicMock]
    ) -> None:
        mocks["get_cached"].return_value = [_issue(1), _issue(2)]
        mocks["trust"].side_effect = [TRUSTED, UNTRUSTED]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert _dispatched_numbers(mocks["dispatch"]) == [1]
        assert mocks["update_cache"].call_count == 1
        assert mocks["update_cache"].call_args.kwargs["issue_number"] == 1
        issue_mgr = mocks["issue_mgr"]
        issue_mgr.add_labels.assert_not_called()
        issue_mgr.remove_labels.assert_not_called()
        issue_mgr.set_labels.assert_not_called()
        issue_mgr.add_comment.assert_not_called()

    def test_lookup_failed_not_dispatched(self, mocks: dict[str, MagicMock]) -> None:
        mocks["get_cached"].return_value = [_issue(7)]
        mocks["trust"].return_value = LOOKUP_FAILED

        result = execute_coordinator_run(_args())

        assert result == 0
        mocks["dispatch"].assert_not_called()
        mocks["update_cache"].assert_not_called()

    def test_summary_names_numbers_reasons_and_count(
        self, mocks: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks["get_cached"].return_value = [_issue(12), _issue(13), _issue(15)]
        mocks["trust"].side_effect = [UNTRUSTED, TRUSTED, LOOKUP_FAILED]

        with caplog.at_level(logging.DEBUG):
            execute_coordinator_run(_args())

        assert _summary_lines(caplog) == [
            "Skipped 2 issue(s) in mcp_coder with untrusted body: "
            "#12 (untrusted: author not trusted), "
            "#15 (lookup_failed: ConnectionError)"
        ]

    def test_no_summary_when_nothing_skipped(
        self, mocks: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks["get_cached"].return_value = [_issue(1), _issue(2)]

        with caplog.at_level(logging.DEBUG):
            execute_coordinator_run(_args())

        assert not _summary_lines(caplog)
        assert _dispatched_numbers(mocks["dispatch"]) == [1, 2]

    def test_issue_without_workflow_label_not_looked_up(
        self, mocks: dict[str, MagicMock]
    ) -> None:
        mocks["get_cached"].return_value = [
            _issue(1),
            _issue(2, label="bug"),
            _issue(3),
        ]

        execute_coordinator_run(_args())

        assert mocks["trust"].call_count == 2
        looked_up = [c.args[1]["number"] for c in mocks["trust"].call_args_list]
        assert looked_up == [1, 3]

    def test_rate_limit_mid_loop_stops_run(
        self, mocks: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks["get_cached"].return_value = [_issue(1), _issue(2), _issue(3)]
        mocks["trust"].side_effect = [
            UNTRUSTED,
            TRUSTED,
            GitHubRateLimitError("limited"),
        ]

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert _dispatched_numbers(mocks["dispatch"]) == [2]
        summary = _summary_lines(caplog)
        assert len(summary) == 1
        assert "#1 (untrusted" in summary[0]

    def test_summary_logged_on_early_return(
        self, mocks: dict[str, MagicMock], caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks["get_cached"].return_value = [_issue(1), _issue(2)]
        mocks["trust"].side_effect = [UNTRUSTED, TRUSTED]
        mocks["dispatch"].side_effect = RuntimeError("jenkins down")

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 1
        summary = _summary_lines(caplog)
        assert len(summary) == 1
        assert "#1 (untrusted" in summary[0]

    def test_fallback_fetch_is_gated(self, mocks: dict[str, MagicMock]) -> None:
        fallback_issue = _issue(9)
        mocks["get_cached"].side_effect = RuntimeError("cache broken")
        mocks["get_eligible"].return_value = [fallback_issue]
        mocks["trust"].return_value = UNTRUSTED

        result = execute_coordinator_run(_args())

        assert result == 0
        mocks["trust"].assert_called_once_with(mocks["issue_mgr"], fallback_issue)
        mocks["dispatch"].assert_not_called()
