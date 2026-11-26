"""PR-health in the coordinator run: per repo with capacity and a working cache."""

import argparse
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_coder.cli.commands.coordinator import DispatchResult, execute_coordinator_run
from mcp_coder.mcp_workspace_github import (
    GitHubRateLimitError,
    IssueData,
    RepoIdentifier,
)
from mcp_coder.utils.jenkins_operations.models import BuildInfo
from tests.github_factories import make_issue_data

_COMMANDS = "mcp_coder.cli.commands.coordinator.commands"

PLAN_READY = "status-05:plan-ready"
READY_PR = "status-08:ready-pr"
PR_CREATED = "status-10:pr-created"


def _repo_config(name: str) -> dict[str, str]:
    return {
        "repo_url": f"https://github.com/user/{name}.git",
        "executor_job_path": f"Jobs/{name}",
        "github_credentials_id": "github-pat-123",
        "executor_os": "linux",
    }


def _job_url(path: str) -> str:
    return f"https://jenkins.example.com/job/{path}/"


def _waiting_build(path: str) -> BuildInfo:
    return BuildInfo(
        job_path=path,
        folder="Jobs",
        job_name=path.rsplit("/", 1)[-1],
        number=99,
        status="running",
        timestamp=datetime.now(UTC),
        duration_ms=None,
        url=f"https://jenkins.example.com/{path}/99/",
        display_name="#99",
    )


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        command="coordinator",
        repo=None,
        all=True,
        log_level="INFO",
        force_refresh=False,
    )


class _Env:
    """Patched collaborators plus the per-repo state their side effects read."""

    def __init__(self, patched: dict[str, MagicMock]) -> None:
        self.patched = patched
        self.issues: dict[str, list[IssueData]] = {"repo_a": [], "repo_b": []}
        self.busy: set[str] = set()

    def __getitem__(self, key: str) -> MagicMock:
        return self.patched[key]


@pytest.fixture
def env(_no_pr_health: MagicMock) -> Iterator[_Env]:
    """Patch everything around execute_coordinator_run for repo_a and repo_b.

    Yields:
        The patched callables and the per-repo state.
    """
    with (
        patch(f"{_COMMANDS}.create_default_config", return_value=False),
        patch(
            f"{_COMMANDS}.load_config",
            return_value={"coordinator": {"repos": {"repo_a": {}, "repo_b": {}}}},
        ),
        patch(
            f"{_COMMANDS}.get_jenkins_credentials",
            return_value=("https://jenkins.example.com", "u", "t"),
        ),
        patch(f"{_COMMANDS}.JenkinsClient") as jenkins_cls,
        patch(f"{_COMMANDS}.load_repo_config", side_effect=_repo_config),
        patch(f"{_COMMANDS}.validate_repo_config"),
        patch(f"{_COMMANDS}.get_cache_refresh_minutes", return_value=1440),
        patch(f"{_COMMANDS}.IssueManager"),
        patch(f"{_COMMANDS}.IssueBranchManager"),
        patch(f"{_COMMANDS}.get_all_cached_issues") as get_cached,
        patch(f"{_COMMANDS}.get_eligible_issues", return_value=[]) as get_eligible,
        patch(
            f"{_COMMANDS}.dispatch_workflow", return_value=DispatchResult.STARTED
        ) as dispatch,
        patch(f"{_COMMANDS}.update_issue_labels_in_cache"),
    ):
        jenkins = jenkins_cls.return_value
        state = _Env(
            {
                "pr_health": _no_pr_health,
                "get_cached": get_cached,
                "get_eligible": get_eligible,
                "dispatch": dispatch,
            }
        )

        def recent_builds(*, path: str, statuses: list[str]) -> list[BuildInfo]:
            del statuses
            return [_waiting_build(path)] if path in state.busy else []

        def fetch(identifier: RepoIdentifier, **_kwargs: Any) -> list[IssueData]:
            return state.issues[identifier.repo_name]

        jenkins.get_job_url.side_effect = _job_url
        jenkins.get_recent_builds.side_effect = recent_builds
        get_cached.side_effect = fetch
        yield state


class TestPrHealthInCollectWork:
    """check_pr_health runs once per repo with capacity and a working cache."""

    def test_called_per_repo_with_full_cached_list(self, env: _Env) -> None:
        unassigned_pr = make_issue_data(number=10, labels=[PR_CREATED])
        closed = make_issue_data(number=11, labels=[PLAN_READY], state="closed")
        eligible = make_issue_data(number=12, labels=[PLAN_READY])
        env.issues["repo_a"] = [unassigned_pr, closed, eligible]
        env.issues["repo_b"] = [make_issue_data(number=20, labels=[PR_CREATED])]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert env["pr_health"].call_args_list == [
            call("repo_a", _repo_config("repo_a"), env.issues["repo_a"]),
            call("repo_b", _repo_config("repo_b"), env.issues["repo_b"]),
        ]
        dispatched = [
            c.kwargs["issue"]["number"] for c in env["dispatch"].call_args_list
        ]
        assert dispatched == [12]

    def test_not_called_for_busy_repo(self, env: _Env) -> None:
        env.issues["repo_a"] = [make_issue_data(number=1, labels=[PR_CREATED])]
        env.issues["repo_b"] = [make_issue_data(number=2, labels=[PR_CREATED])]
        env.busy.add("Jobs/repo_a")

        result = execute_coordinator_run(_args())

        assert result == 0
        assert [c.args[0] for c in env["pr_health"].call_args_list] == ["repo_b"]
        fetched = [c.args[0].full_name for c in env["get_cached"].call_args_list]
        assert fetched == ["user/repo_b"]

    def test_cache_failure_uses_direct_fetch_and_skips_pr_health(
        self, env: _Env
    ) -> None:
        env["get_cached"].side_effect = RuntimeError("cache broken")

        result = execute_coordinator_run(_args())

        assert result == 0
        assert env["get_eligible"].call_count == 2
        env["pr_health"].assert_not_called()

    def test_rate_limit_from_pr_health_exits_0_without_dispatch(
        self, env: _Env
    ) -> None:
        env.issues["repo_a"] = [make_issue_data(number=1, labels=[PLAN_READY])]
        env["pr_health"].side_effect = GitHubRateLimitError("limited")

        result = execute_coordinator_run(_args())

        assert result == 0
        env["dispatch"].assert_not_called()

    def test_other_pr_health_error_propagates_without_fallback(self, env: _Env) -> None:
        env.issues["repo_a"] = [make_issue_data(number=1, labels=[PLAN_READY])]
        env["pr_health"].side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            execute_coordinator_run(_args())

        env["get_eligible"].assert_not_called()
        env["dispatch"].assert_not_called()

    def test_filter_error_uses_direct_fetch_and_skips_pr_health(
        self, env: _Env
    ) -> None:
        env.issues["repo_a"] = [make_issue_data(number=1, labels=[PLAN_READY])]

        with patch(
            f"{_COMMANDS}._filter_eligible_issues",
            side_effect=KeyError("workflow_labels"),
        ):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert env["get_eligible"].call_count == 2
        env["pr_health"].assert_not_called()


def _error_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == _COMMANDS and r.levelno == logging.ERROR
    ]


class TestMultipleStatusLabels:
    """One ERROR per open issue with more than one status-* label."""

    def test_error_per_open_issue_with_two_status_labels(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=[PLAN_READY, PR_CREATED]),
        ]
        env.issues["repo_b"] = [
            make_issue_data(number=8, labels=["bug", PR_CREATED, PLAN_READY]),
        ]

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert _error_messages(caplog) == [
            f"repo_a #7 has multiple status labels: {PLAN_READY}, {PR_CREATED}",
            f"repo_b #8 has multiple status labels: {PR_CREATED}, {PLAN_READY}",
        ]

    def test_no_error_for_closed_issue(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=[PLAN_READY, PR_CREATED], state="closed"),
        ]

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert not _error_messages(caplog)

    def test_no_error_for_single_status_label(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=["bug", PR_CREATED, "enhancement"]),
        ]

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert not _error_messages(caplog)

    def test_no_error_for_busy_repo(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=[PLAN_READY, PR_CREATED]),
        ]
        env.busy.add("Jobs/repo_a")

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert not _error_messages(caplog)

    def test_no_error_on_cache_fallback(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env["get_eligible"].return_value = [
            make_issue_data(number=7, labels=[READY_PR, PR_CREATED]),
        ]
        env["get_cached"].side_effect = RuntimeError("cache broken")

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert not _error_messages(caplog)

    def test_error_logged_when_pr_health_rate_limited(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=[PLAN_READY, PR_CREATED]),
        ]
        env["pr_health"].side_effect = GitHubRateLimitError("limited")

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert _error_messages(caplog) == [
            f"repo_a #7 has multiple status labels: {PLAN_READY}, {PR_CREATED}",
        ]
        env["dispatch"].assert_not_called()

    def test_issue_with_multiple_labels_still_dispatched(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [
            make_issue_data(number=7, labels=[READY_PR, PR_CREATED]),
        ]

        with caplog.at_level(logging.ERROR, logger=_COMMANDS):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert _error_messages(caplog) == [
            f"repo_a #7 has multiple status labels: {READY_PR}, {PR_CREATED}",
        ]
        dispatched = [
            c.kwargs["issue"]["number"] for c in env["dispatch"].call_args_list
        ]
        assert dispatched == [7]
