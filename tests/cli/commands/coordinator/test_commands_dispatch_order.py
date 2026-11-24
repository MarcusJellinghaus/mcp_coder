"""Tests for the global dispatch order of execute_coordinator_run."""

import argparse
import logging
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import DispatchResult, execute_coordinator_run
from mcp_coder.cli.commands.coordinator.commands import _collect_work
from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    IssueData,
)
from tests.github_factories import make_issue_data

_COMMANDS = "mcp_coder.cli.commands.coordinator.commands"

TRUSTED = BodyTrustResult(status=BodyTrust.TRUSTED, reason="")
UNTRUSTED = BodyTrustResult(status=BodyTrust.UNTRUSTED, reason="author not trusted")

FAILING_CI = "status-81:failing-ci"
READY_PR = "status-08:ready-pr"
PLAN_READY = "status-05:plan-ready"
AWAITING_PLANNING = "status-02:awaiting-planning"

_EVENTS_LOGGER = logging.getLogger("tests.dispatch_order.events")


def _issue(number: int, label: str) -> IssueData:
    return make_issue_data(number=number, labels=[label])


def _repo_config(name: str) -> dict[str, Any]:
    return {
        "repo_url": f"https://github.com/user/{name}.git",
        "executor_job_path": f"Jobs/{name}-executor",
        "github_credentials_id": "github-pat-123",
        "executor_os": "linux",
    }


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        command="coordinator",
        repo=None,
        all=True,
        log_level="INFO",
        force_refresh=False,
    )


def _dispatched_numbers(dispatch: MagicMock) -> list[int]:
    return [c.kwargs["issue"]["number"] for c in dispatch.call_args_list]


class _Mocks:
    """Patched collaborators plus the per-repo issue lists they serve."""

    def __init__(self, patched: dict[str, MagicMock]) -> None:
        self.patched = patched
        self.issues: dict[str, list[IssueData]] = {"repo_a": [], "repo_b": []}
        self.events: list[tuple[str, Any]] = []

    def __getitem__(self, key: str) -> MagicMock:
        return self.patched[key]


@pytest.fixture
def mocks(_trusted_issue_bodies: MagicMock) -> Iterator[_Mocks]:
    """Patch everything around execute_coordinator_run for repo_a and repo_b.

    Yields:
        The patched callables and the per-repo issue lists.
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
        patch(f"{_COMMANDS}.JenkinsClient"),
        patch(f"{_COMMANDS}.load_repo_config", side_effect=_repo_config),
        patch(f"{_COMMANDS}.validate_repo_config") as validate,
        patch(f"{_COMMANDS}.get_cache_refresh_minutes", return_value=1440),
        patch(f"{_COMMANDS}.IssueManager") as issue_mgr_cls,
        patch(f"{_COMMANDS}.IssueBranchManager"),
        patch(f"{_COMMANDS}.get_cached_eligible_issues") as get_cached,
        patch(f"{_COMMANDS}.get_eligible_issues") as get_eligible,
        patch(f"{_COMMANDS}.dispatch_workflow") as dispatch,
        patch(f"{_COMMANDS}.update_issue_labels_in_cache") as update_cache,
    ):
        state = _Mocks(
            {
                "trust": _trusted_issue_bodies,
                "validate": validate,
                "issue_mgr_cls": issue_mgr_cls,
                "get_cached": get_cached,
                "get_eligible": get_eligible,
                "dispatch": dispatch,
                "update_cache": update_cache,
            }
        )

        def fetch(**kwargs: Any) -> list[IssueData]:
            name = kwargs["repo_full_name"].split("/")[1]
            state.events.append(("fetch", name))
            return state.issues[name]

        def dispatch_side_effect(**kwargs: Any) -> DispatchResult:
            number = kwargs["issue"]["number"]
            state.events.append(("dispatch", number))
            _EVENTS_LOGGER.info("dispatch #%d", number)
            return DispatchResult.STARTED

        get_cached.side_effect = fetch
        dispatch.side_effect = dispatch_side_effect
        yield state


def _summary_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelno == logging.INFO and "untrusted body" in r.getMessage()
    ]


class TestGlobalDispatchOrder:
    """Issues of all repos are dispatched in one reverse-pipeline order."""

    def test_global_order_across_repos(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(1, AWAITING_PLANNING), _issue(2, READY_PR)]
        mocks.issues["repo_b"] = [_issue(3, FAILING_CI), _issue(4, PLAN_READY)]

        result = execute_coordinator_run(_args())

        assert result == 0
        assert _dispatched_numbers(mocks["dispatch"]) == [3, 2, 4, 1]

    def test_same_stage_tie_broken_by_config_repo_order(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(10, PLAN_READY)]
        mocks.issues["repo_b"] = [_issue(9, PLAN_READY)]

        execute_coordinator_run(_args())

        assert _dispatched_numbers(mocks["dispatch"]) == [10, 9]
        repo_names = [c.kwargs["repo_name"] for c in mocks["dispatch"].call_args_list]
        assert repo_names == ["repo_a", "repo_b"]

    def test_stable_within_stage_and_repo(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(7, PLAN_READY), _issue(5, PLAN_READY)]

        execute_coordinator_run(_args())

        assert _dispatched_numbers(mocks["dispatch"]) == [7, 5]

    def test_all_repos_fetched_before_first_dispatch(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(1, PLAN_READY)]
        mocks.issues["repo_b"] = [_issue(2, PLAN_READY)]

        execute_coordinator_run(_args())

        assert mocks.events == [
            ("fetch", "repo_a"),
            ("fetch", "repo_b"),
            ("dispatch", 1),
            ("dispatch", 2),
        ]

    def test_dispatch_uses_the_issues_own_repo(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(1, AWAITING_PLANNING)]
        mocks.issues["repo_b"] = [_issue(2, FAILING_CI)]

        execute_coordinator_run(_args())

        first, second = mocks["dispatch"].call_args_list
        assert first.kwargs["repo_name"] == "repo_b"
        assert first.kwargs["repo_config"]["repo_url"] == (
            "https://github.com/user/repo_b.git"
        )
        assert second.kwargs["repo_name"] == "repo_a"
        cache_repos = [
            c.args[0].full_name for c in mocks["update_cache"].call_args_list
        ]
        assert cache_repos == ["user/repo_b", "user/repo_a"]


class TestUntrustedSummaryAtEnd:
    """The untrusted-body summary is logged per repo after all dispatches."""

    def test_one_summary_per_repo_after_last_dispatch(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.issues["repo_a"] = [_issue(1, PLAN_READY), _issue(2, AWAITING_PLANNING)]
        mocks.issues["repo_b"] = [_issue(3, READY_PR), _issue(4, PLAN_READY)]
        # Sorted order: 3 (b), 1 (a), 4 (b), 2 (a)
        mocks["trust"].side_effect = [UNTRUSTED, UNTRUSTED, TRUSTED, TRUSTED]

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 0
        assert _dispatched_numbers(mocks["dispatch"]) == [4, 2]
        messages = [r.getMessage() for r in caplog.records]
        summaries = [i for i, m in enumerate(messages) if "untrusted body" in m]
        dispatches = [i for i, m in enumerate(messages) if m.startswith("dispatch #")]
        assert len(summaries) == 2
        assert min(summaries) > max(dispatches)
        assert _summary_lines(caplog) == [
            "Skipped 1 issue(s) in repo_b with untrusted body: "
            "#3 (untrusted: author not trusted)",
            "Skipped 1 issue(s) in repo_a with untrusted body: "
            "#1 (untrusted: author not trusted)",
        ]

    def test_fail_fast_still_logs_earlier_summary(
        self, mocks: _Mocks, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.issues["repo_a"] = [_issue(1, READY_PR)]
        mocks.issues["repo_b"] = [_issue(2, PLAN_READY), _issue(3, AWAITING_PLANNING)]
        mocks["trust"].side_effect = [UNTRUSTED, TRUSTED, TRUSTED]
        mocks["dispatch"].side_effect = RuntimeError("jenkins down")

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_run(_args())

        assert result == 1
        assert _dispatched_numbers(mocks["dispatch"]) == [2]
        assert _summary_lines(caplog) == [
            "Skipped 1 issue(s) in repo_a with untrusted body: "
            "#1 (untrusted: author not trusted)"
        ]


class TestCollectWork:
    """_collect_work fetches every repo in config order, unsorted."""

    def test_items_in_config_and_fetch_order(self, mocks: _Mocks) -> None:
        mocks.issues["repo_a"] = [_issue(1, AWAITING_PLANNING), _issue(2, READY_PR)]
        mocks.issues["repo_b"] = [_issue(3, FAILING_CI)]

        work = _collect_work(["repo_a", "repo_b"], force_refresh=False)

        assert [issue["number"] for issue, _ in work] == [1, 2, 3]
        repos = [repo for _, repo in work]
        assert [(r.config_index, r.name, r.full_name) for r in repos] == [
            (0, "repo_a", "user/repo_a"),
            (0, "repo_a", "user/repo_a"),
            (1, "repo_b", "user/repo_b"),
        ]
        assert repos[0].config["executor_job_path"] == "Jobs/repo_a-executor"

    def test_repo_without_issues_contributes_nothing(self, mocks: _Mocks) -> None:
        mocks.issues["repo_b"] = [_issue(3, PLAN_READY)]

        work = _collect_work(["repo_a", "repo_b"], force_refresh=False)

        assert [(issue["number"], repo.name) for issue, repo in work] == [(3, "repo_b")]

    def test_cache_failure_falls_back_to_direct_fetch(self, mocks: _Mocks) -> None:
        fallback_issue = _issue(8, PLAN_READY)
        mocks["get_cached"].side_effect = RuntimeError("cache broken")
        mocks["get_eligible"].return_value = [fallback_issue]

        work = _collect_work(["repo_a"], force_refresh=True)

        assert [(issue, repo.name) for issue, repo in work] == [
            (fallback_issue, "repo_a")
        ]
        mocks["get_eligible"].assert_called_once_with(
            mocks["issue_mgr_cls"].return_value
        )

    def test_invalid_repo_config_propagates(self, mocks: _Mocks) -> None:
        mocks["validate"].side_effect = ValueError("value for field missing")

        with pytest.raises(ValueError, match="value for field missing"):
            _collect_work(["repo_a", "repo_b"], force_refresh=False)

        mocks["get_cached"].assert_not_called()
