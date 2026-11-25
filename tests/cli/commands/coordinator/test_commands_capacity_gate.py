"""Tests for the executor capacity gate and dispatch delay in execute_coordinator_run."""

import argparse
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_coder.cli.commands.coordinator import DispatchResult, execute_coordinator_run
from mcp_coder.cli.commands.coordinator.commands import (
    _collect_work,
    _recheck_after_delay,
    _Repo,
)
from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    IssueData,
)
from mcp_coder.utils.jenkins_operations.client import JenkinsError
from mcp_coder.utils.jenkins_operations.models import BuildInfo
from tests.github_factories import make_issue_data

_COMMANDS = "mcp_coder.cli.commands.coordinator.commands"

TRUSTED = BodyTrustResult(status=BodyTrust.TRUSTED, reason="")
UNTRUSTED = BodyTrustResult(status=BodyTrust.UNTRUSTED, reason="author not trusted")

FAILING_CI = "status-81:failing-ci"
READY_PR = "status-08:ready-pr"
PLAN_READY = "status-05:plan-ready"
AWAITING_PLANNING = "status-02:awaiting-planning"

JOB_A = "Jobs/A"
JOB_B = "Jobs/B"
URL_A = "https://jenkins.example.com/job/Jobs/job/A/"
URL_B = "https://jenkins.example.com/job/Jobs/job/B/"

Event = tuple[str, Any]


def _issue(number: int, label: str = PLAN_READY) -> IssueData:
    return make_issue_data(number=number, labels=[label])


def _waiting_build(path: str, number: int) -> BuildInfo:
    return BuildInfo(
        job_path=path,
        folder="Jobs",
        job_name=path.rsplit("/", 1)[-1],
        number=number,
        status="running",
        timestamp=datetime.now(UTC),
        duration_ms=None,
        url=f"https://jenkins.example.com/{path}/{number}/",
        display_name=f"#{number}",
    )


def _args(repo: str | None = None, force_refresh: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        command="coordinator",
        repo=repo,
        all=repo is None,
        log_level="INFO",
        force_refresh=force_refresh,
    )


class _Env:
    """Patched collaborators plus the state their side effects read and record."""

    def __init__(self, patched: dict[str, MagicMock]) -> None:
        self.patched = patched
        self.issues: dict[str, list[IssueData]] = {"repo_a": [], "repo_b": []}
        self.paths: dict[str, str] = {"repo_a": JOB_A, "repo_b": JOB_B}
        self.urls: dict[str, str] = {JOB_A: URL_A, JOB_B: URL_B}
        # Per path, one entry per get_recent_builds call: True = a waiting build,
        # an exception = raised. Exhausted -> free.
        self.busy: dict[str, list[bool | Exception]] = {}
        self.untrusted: set[int] = set()
        self.results: dict[int, DispatchResult] = {}
        self.events: list[Event] = []

    def __getitem__(self, key: str) -> MagicMock:
        return self.patched[key]

    @property
    def jenkins(self) -> MagicMock:
        return self.patched["jenkins"]

    def gate_events(self) -> list[Event]:
        """Events without the issue fetches."""
        return [e for e in self.events if e[0] != "fetch"]

    def dispatched(self) -> list[int]:
        return [n for kind, n in self.events if kind == "dispatch"]


@pytest.fixture
def env(
    _trusted_issue_bodies: MagicMock,
    _no_dispatch_sleep: MagicMock,
    _dispatch_delay: MagicMock,
) -> Iterator[_Env]:
    """Patch everything around execute_coordinator_run for repo_a and repo_b.

    Yields:
        The patched callables and the state their side effects use.
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
        patch(f"{_COMMANDS}.load_repo_config") as load_repo,
        patch(f"{_COMMANDS}.validate_repo_config"),
        patch(f"{_COMMANDS}.get_cache_refresh_minutes", return_value=1440),
        patch(f"{_COMMANDS}.IssueManager") as issue_mgr_cls,
        patch(f"{_COMMANDS}.IssueBranchManager"),
        patch(f"{_COMMANDS}.get_cached_eligible_issues") as get_cached,
        patch(f"{_COMMANDS}.get_eligible_issues"),
        patch(f"{_COMMANDS}.dispatch_workflow") as dispatch,
        patch(f"{_COMMANDS}.update_issue_labels_in_cache") as update_cache,
    ):
        jenkins = jenkins_cls.return_value
        state = _Env(
            {
                "jenkins": jenkins,
                "sleep": _no_dispatch_sleep,
                "delay": _dispatch_delay,
                "trust": _trusted_issue_bodies,
                "issue_mgr_cls": issue_mgr_cls,
                "get_cached": get_cached,
                "dispatch": dispatch,
                "update_cache": update_cache,
            }
        )

        def repo_config(name: str) -> dict[str, str]:
            return {
                "repo_url": f"https://github.com/user/{name}.git",
                "executor_job_path": state.paths[name],
                "github_credentials_id": "github-pat-123",
                "executor_os": "linux",
            }

        def recent_builds(*, path: str, statuses: list[str]) -> list[BuildInfo]:
            assert statuses == ["running"]
            state.events.append(("builds", path))
            queue = state.busy.get(path, [])
            outcome = queue.pop(0) if queue else False
            if isinstance(outcome, Exception):
                raise outcome
            return [_waiting_build(path, 99)] if outcome else []

        def fetch(**kwargs: Any) -> list[IssueData]:
            name = kwargs["repo_full_name"].split("/")[1]
            state.events.append(("fetch", name))
            return state.issues[name]

        def trust(_issue_manager: object, issue: IssueData) -> BodyTrustResult:
            state.events.append(("trust", issue["number"]))
            return UNTRUSTED if issue["number"] in state.untrusted else TRUSTED

        def dispatch_side_effect(**kwargs: Any) -> DispatchResult:
            number = kwargs["issue"]["number"]
            state.events.append(("dispatch", number))
            return state.results.get(number, DispatchResult.STARTED)

        load_repo.side_effect = repo_config
        jenkins.get_job_url.side_effect = lambda path: state.urls[path]
        jenkins.get_recent_builds.side_effect = recent_builds
        get_cached.side_effect = fetch
        _trusted_issue_bodies.side_effect = trust
        dispatch.side_effect = dispatch_side_effect
        _no_dispatch_sleep.side_effect = lambda s: state.events.append(("sleep", s))
        yield state


def _error_messages(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [
        r for r in caplog.records if r.name == _COMMANDS and r.levelno == logging.ERROR
    ]


class TestInitialCapacityCheck:
    """A busy executor job skips its repos before any GitHub call."""

    @pytest.mark.parametrize("force_refresh", [False, True])
    def test_busy_job_skips_repo_before_github(
        self, env: _Env, force_refresh: bool
    ) -> None:
        env.issues["repo_a"] = [_issue(1)]
        env.issues["repo_b"] = [_issue(2)]
        env.busy[JOB_A] = [True]

        result = execute_coordinator_run(_args(force_refresh=force_refresh))

        assert result == 0
        repo_urls = [c.kwargs["repo_url"] for c in env["issue_mgr_cls"].call_args_list]
        assert repo_urls == ["https://github.com/user/repo_b.git"]
        fetched = [c.kwargs["repo_full_name"] for c in env["get_cached"].call_args_list]
        assert fetched == ["user/repo_b"]
        assert env.dispatched() == [2]

    def test_paths_with_same_url_checked_once_and_both_skipped(self, env: _Env) -> None:
        env.paths["repo_b"] = "Jobs/A/"
        env.urls["Jobs/A/"] = URL_A
        env.issues["repo_a"] = [_issue(1)]
        env.issues["repo_b"] = [_issue(2)]
        env.busy[JOB_A] = [True]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert env.events == [("builds", JOB_A)]
        env["issue_mgr_cls"].assert_not_called()
        env["dispatch"].assert_not_called()

    def test_job_url_looked_up_once_per_distinct_path(self, env: _Env) -> None:
        env.paths["repo_b"] = JOB_A
        env.issues["repo_a"] = [_issue(1)]

        execute_coordinator_run(_args())

        assert env.jenkins.get_job_url.call_args_list == [call(JOB_A)]

    def test_repo_mode_runs_the_same_gate(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1)]
        env.busy[JOB_A] = [True]

        result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 0
        assert env.events == [("builds", JOB_A)]
        env["issue_mgr_cls"].assert_not_called()
        env["get_cached"].assert_not_called()


class TestDelayAndRecheck:
    """After a start, the next dispatch waits and re-checks the job that got it."""

    def test_one_sleep_between_two_starts_none_after_last(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1), _issue(2)]

        result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 0
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("trust", 1),
            ("dispatch", 1),
            ("sleep", 15),
            ("builds", JOB_A),
            ("trust", 2),
            ("dispatch", 2),
        ]

    def test_recheck_finds_waiting_build_blocks_rest_of_job(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1), _issue(2), _issue(3)]
        env.busy[JOB_A] = [False, True]

        result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 0
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("trust", 1),
            ("dispatch", 1),
            ("sleep", 15),
            ("builds", JOB_A),
        ]

    def test_recheck_uses_previous_job_then_dispatches_other_job(
        self, env: _Env
    ) -> None:
        env.issues["repo_a"] = [_issue(1, FAILING_CI)]
        env.issues["repo_b"] = [_issue(2, PLAN_READY)]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("builds", JOB_B),
            ("trust", 1),
            ("dispatch", 1),
            ("sleep", 15),
            ("builds", JOB_A),
            ("trust", 2),
            ("dispatch", 2),
        ]
        assert env.jenkins.get_recent_builds.call_args.kwargs["path"] == JOB_A

    def test_blocked_job_skipped_without_taking_pending_delay(self, env: _Env) -> None:
        # Dispatch order: #1 (B), #2 (A), #3 (B), #4 (A)
        env.issues["repo_a"] = [_issue(2, READY_PR), _issue(4, AWAITING_PLANNING)]
        env.issues["repo_b"] = [_issue(1, FAILING_CI), _issue(3, PLAN_READY)]
        env.busy[JOB_B] = [False, True]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert env.dispatched() == [1, 2, 4]
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("builds", JOB_B),
            ("trust", 1),
            ("dispatch", 1),
            ("sleep", 15),
            ("builds", JOB_B),
            ("trust", 2),
            ("dispatch", 2),
            ("sleep", 15),
            ("builds", JOB_A),
            ("trust", 4),
            ("dispatch", 4),
        ]

    def test_not_started_sets_no_delay(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1), _issue(2)]
        env.results[1] = DispatchResult.NOT_STARTED

        result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 0
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("trust", 1),
            ("dispatch", 1),
            ("trust", 2),
            ("dispatch", 2),
        ]
        updated = [c.kwargs["issue_number"] for c in env["update_cache"].call_args_list]
        assert updated == [1, 2]

    def test_recheck_runs_before_trust_gate_of_untrusted_issue(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1), _issue(2), _issue(3)]
        env.untrusted = {2}

        result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 0
        assert env.gate_events() == [
            ("builds", JOB_A),
            ("trust", 1),
            ("dispatch", 1),
            ("sleep", 15),
            ("builds", JOB_A),
            ("trust", 2),
            ("trust", 3),
            ("dispatch", 3),
        ]


class TestDelayConfig:
    """The delay is read once at run start."""

    def test_configured_delay_is_slept(self, env: _Env) -> None:
        env["delay"].return_value = 30
        env.issues["repo_a"] = [_issue(1), _issue(2)]

        execute_coordinator_run(_args(repo="repo_a"))

        env["sleep"].assert_called_once_with(30)

    def test_invalid_delay_exits_1_before_fetch(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env["delay"].side_effect = ValueError("dispatch_delay_seconds: expected int")
        env.issues["repo_a"] = [_issue(1)]

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 1
        messages = [r.getMessage() for r in _error_messages(caplog)]
        assert messages == ["dispatch_delay_seconds: expected int"]
        env["get_cached"].assert_not_called()
        env.jenkins.get_job_url.assert_not_called()


class TestGateErrors:
    """Jenkins errors of the gate end the run with one ERROR line, exit 1."""

    def test_job_lookup_error_exits_1_with_one_line(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        message = f"Failed to look up job '{JOB_A}': 404 Not Found - check the path"
        env.jenkins.get_job_url.side_effect = JenkinsError(message)
        env.issues["repo_a"] = [_issue(1)]

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 1
        errors = _error_messages(caplog)
        assert [r.getMessage() for r in errors] == [message]
        assert errors[0].exc_info is None
        assert "Failed processing issue" not in caplog.text
        env["get_cached"].assert_not_called()

    def test_recheck_error_exits_1_and_logs_untrusted_summary(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.issues["repo_a"] = [_issue(1), _issue(2), _issue(3)]
        env.untrusted = {1}
        env.busy[JOB_A] = [
            False,
            JenkinsError(f"Failed to list builds under '{JOB_A}': 500"),
        ]

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args(repo="repo_a"))

        assert result == 1
        assert env.dispatched() == [2]
        errors = [r.getMessage() for r in _error_messages(caplog)]
        assert len(errors) == 1
        assert JOB_A in errors[0]
        assert "Failed processing issue" not in caplog.text
        assert "Skipped 1 issue(s) in repo_a with untrusted body" in caplog.text


def _pending_repo() -> _Repo:
    return _Repo(
        config_index=0,
        name="repo_a",
        full_name="user/repo_a",
        config={},
        issue_manager=MagicMock(),
        branch_manager=MagicMock(),
        job_url=URL_A,
        job_path=JOB_A,
    )


class TestRecheckAfterDelay:
    """_recheck_after_delay sleeps, then re-checks the pending repo's job."""

    def test_sleeps_before_checking_the_job_path(
        self, _no_dispatch_sleep: MagicMock
    ) -> None:
        events: list[Event] = []

        def recent_builds(**kwargs: Any) -> list[BuildInfo]:
            events.append(("builds", kwargs))
            return []

        client = MagicMock()
        client.get_recent_builds.side_effect = recent_builds
        _no_dispatch_sleep.side_effect = lambda s: events.append(("sleep", s))

        _recheck_after_delay(client, _pending_repo(), 15, set())

        assert events == [
            ("sleep", 15),
            ("builds", {"path": JOB_A, "statuses": ["running"]}),
        ]

    @pytest.mark.parametrize(
        ("builds", "expected"),
        [([_waiting_build(JOB_A, 7)], {URL_A}), ([], set())],
    )
    def test_blocks_job_only_when_build_waiting(
        self, builds: list[BuildInfo], expected: set[str]
    ) -> None:
        client = MagicMock()
        client.get_recent_builds.return_value = builds
        blocked: set[str] = set()

        _recheck_after_delay(client, _pending_repo(), 15, blocked)

        assert blocked == expected

    def test_jenkins_error_propagates(self) -> None:
        client = MagicMock()
        client.get_recent_builds.side_effect = JenkinsError("boom")
        blocked: set[str] = set()

        with pytest.raises(JenkinsError, match="boom"):
            _recheck_after_delay(client, _pending_repo(), 15, blocked)

        assert not blocked


class TestCollectWorkGate:
    """_collect_work resolves jobs and checks capacity before any GitHub call."""

    def test_busy_job_blocked_and_its_repo_contributes_nothing(self, env: _Env) -> None:
        env.issues["repo_a"] = [_issue(1)]
        env.issues["repo_b"] = [_issue(2)]
        env.busy[JOB_A] = [True]
        blocked: set[str] = set()

        work = _collect_work(["repo_a", "repo_b"], False, env.jenkins, blocked)

        assert blocked == {URL_A}
        assert [(issue["number"], repo.name) for issue, repo in work] == [(2, "repo_b")]
        assert work[0][1].job_url == URL_B
        assert work[0][1].job_path == JOB_B

    def test_paths_with_same_url_share_job_url_and_first_path(self, env: _Env) -> None:
        env.paths["repo_b"] = "Jobs/A/"
        env.urls["Jobs/A/"] = URL_A
        env.issues["repo_a"] = [_issue(1)]
        env.issues["repo_b"] = [_issue(2)]

        work = _collect_work(["repo_a", "repo_b"], False, env.jenkins, set())

        assert env.jenkins.get_job_url.call_args_list == [call(JOB_A), call("Jobs/A/")]
        assert env.jenkins.get_recent_builds.call_count == 1
        assert [(repo.job_url, repo.job_path) for _, repo in work] == [
            (URL_A, JOB_A),
            (URL_A, JOB_A),
        ]

    def test_job_lookup_error_propagates_before_issue_manager(self, env: _Env) -> None:
        env.jenkins.get_job_url.side_effect = JenkinsError("Failed to look up job")

        with pytest.raises(JenkinsError, match="Failed to look up job"):
            _collect_work(["repo_a", "repo_b"], False, env.jenkins, set())

        env["issue_mgr_cls"].assert_not_called()
