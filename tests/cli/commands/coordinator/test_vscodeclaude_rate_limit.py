"""vscodeclaude ``launch`` and ``status`` stop GitHub work on a rate limit."""

import argparse
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
    _build_cached_issues_by_repo,
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
)
from mcp_coder.mcp_workspace_github import GithubException, GitHubRateLimitError

_MOD = "mcp_coder.cli.commands.coordinator.commands_vscodeclaude"
_STOP_LINE = "GitHub rate limit hit"


def _rest_rate_limit() -> GithubException:
    return GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1900000000"},
    )


def _wrapped_rate_limit() -> ValueError:
    try:
        try:
            raise _rest_rate_limit()
        except GithubException as e:
            raise ValueError("could not get user") from e
    except ValueError as wrapped:
        return wrapped


def _assessment(active: bool) -> SimpleNamespace:
    return SimpleNamespace(verdict=SimpleNamespace(active=active))


@pytest.fixture
def launch_mocks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator of the launch command with a MagicMock."""
    mocks = SimpleNamespace(
        create_default_config=MagicMock(return_value=False),
        load_vscodeclaude_config=MagicMock(
            return_value={"workspace_base": "/tmp", "max_sessions": 5}
        ),
        load_config=MagicMock(
            return_value={"coordinator": {"repos": {"repo1": {}, "repo2": {}}}}
        ),
        load_sessions=MagicMock(return_value={"sessions": [], "last_updated": ""}),
        _build_cached_issues_by_repo=MagicMock(
            return_value=(
                {"owner/repo1": {1: MagicMock()}, "owner/repo2": {2: MagicMock()}},
                set(),
            )
        ),
        build_assessments=MagicMock(return_value={"C:/w/a": _assessment(True)}),
        cleanup_stale_sessions=MagicMock(),
        restart_closed_sessions=MagicMock(return_value=[]),
        apply_assessments=MagicMock(),
        load_repo_config=MagicMock(
            side_effect=lambda name: {"repo_url": f"https://github.com/owner/{name}"}
        ),
        check_pr_health=MagicMock(),
        process_eligible_issues=MagicMock(return_value=[]),
    )
    for name, mock in vars(mocks).items():
        monkeypatch.setattr(f"{_MOD}.{name}", mock)
    return mocks


def _launch_args() -> argparse.Namespace:
    return argparse.Namespace(
        repo=None,
        max_sessions=None,
        cleanup=False,
        intervene=False,
        issue=None,
        no_install_from_github=False,
    )


def _stop_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if _STOP_LINE in r.getMessage()]


class TestLaunchRateLimit:
    """execute_coordinator_vscodeclaude under a GitHub rate limit."""

    def test_cache_build_limit_runs_offline_and_stops(
        self, launch_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        launch_mocks._build_cached_issues_by_repo.side_effect = GitHubRateLimitError(
            "limited"
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_launch_args())

        assert result == 0
        launch_mocks.build_assessments.assert_called_once_with([], None)
        launch_mocks.cleanup_stale_sessions.assert_called_once()
        launch_mocks.apply_assessments.assert_called_once()
        launch_mocks.restart_closed_sessions.assert_not_called()
        launch_mocks.check_pr_health.assert_not_called()
        launch_mocks.process_eligible_issues.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_restart_limit_still_applies_assessments(
        self, launch_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        launch_mocks.restart_closed_sessions.side_effect = _rest_rate_limit()

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_launch_args())

        assert result == 0
        launch_mocks.apply_assessments.assert_called_once()
        launch_mocks.check_pr_health.assert_not_called()
        launch_mocks.process_eligible_issues.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_pr_health_limit_stops_before_next_repo(
        self, launch_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        launch_mocks.check_pr_health.side_effect = GitHubRateLimitError("limited")

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_launch_args())

        assert result == 0
        assert launch_mocks.check_pr_health.call_count == 1
        launch_mocks.process_eligible_issues.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_wrapped_limit_in_launch_exits_zero(
        self, launch_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        launch_mocks.process_eligible_issues.side_effect = _wrapped_rate_limit()

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_launch_args())

        assert result == 0
        assert launch_mocks.process_eligible_issues.call_count == 1
        assert len(_stop_lines(caplog)) == 1

    def test_other_error_is_reraised(self, launch_mocks: SimpleNamespace) -> None:
        launch_mocks.check_pr_health.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            execute_coordinator_vscodeclaude(_launch_args())

    def test_other_cache_error_is_reraised(self, launch_mocks: SimpleNamespace) -> None:
        launch_mocks._build_cached_issues_by_repo.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            execute_coordinator_vscodeclaude(_launch_args())
        launch_mocks.cleanup_stale_sessions.assert_not_called()


@pytest.fixture
def status_mocks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator of the status command with a MagicMock."""
    mocks = SimpleNamespace(
        load_sessions=MagicMock(return_value={"sessions": [], "last_updated": ""}),
        load_config=MagicMock(return_value={"coordinator": {"repos": {"repo1": {}}}}),
        load_vscodeclaude_config=MagicMock(
            return_value={"workspace_base": "/tmp", "max_sessions": 5}
        ),
        _build_cached_issues_by_repo=MagicMock(return_value=({}, set())),
        build_assessments=MagicMock(return_value={}),
        render_explain=MagicMock(return_value="EXPLAIN TEXT"),
    )
    for name, mock in vars(mocks).items():
        monkeypatch.setattr(f"{_MOD}.{name}", mock)
    mocks.branch_check = MagicMock(return_value=([], set()))
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.issues."
        "build_eligible_issues_with_branch_check",
        mocks.branch_check,
    )
    mocks.display_status_table = MagicMock()
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.status.display_status_table",
        mocks.display_status_table,
    )
    return mocks


class TestStatusRateLimit:
    """execute_coordinator_vscodeclaude_status under a GitHub rate limit."""

    def test_cache_limit_prints_only_stop_line(
        self, status_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        status_mocks._build_cached_issues_by_repo.side_effect = GitHubRateLimitError(
            "limited"
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude_status(
                argparse.Namespace(repo=None, explain=False)
            )

        assert result == 0
        status_mocks.display_status_table.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_branch_check_limit_prints_no_table(
        self, status_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        status_mocks.branch_check.side_effect = _rest_rate_limit()

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude_status(
                argparse.Namespace(repo=None, explain=False)
            )

        assert result == 0
        status_mocks.display_status_table.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_explain_limit_prints_no_explain_text(
        self, status_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        status_mocks.build_assessments.side_effect = _wrapped_rate_limit()

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude_status(
                argparse.Namespace(repo=None, explain=True)
            )

        assert result == 0
        status_mocks.render_explain.assert_not_called()
        assert "EXPLAIN TEXT" not in caplog.text
        assert len(_stop_lines(caplog)) == 1

    def test_other_error_is_reraised(self, status_mocks: SimpleNamespace) -> None:
        status_mocks.branch_check.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            execute_coordinator_vscodeclaude_status(
                argparse.Namespace(repo=None, explain=False)
            )


class TestBuildCachedIssuesRateLimit:
    """_build_cached_issues_by_repo stops on the first rate limit."""

    def test_limit_propagates_and_skips_next_repo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            f"{_MOD}.load_repo_config",
            lambda name: {"repo_url": f"https://github.com/owner/{name}"},
        )
        monkeypatch.setattr(f"{_MOD}.IssueManager", MagicMock())
        get_all = MagicMock(side_effect=_rest_rate_limit())
        monkeypatch.setattr(f"{_MOD}.get_all_cached_issues", get_all)

        with pytest.raises(GitHubRateLimitError):
            _build_cached_issues_by_repo(["repo1", "repo2"])

        assert get_all.call_count == 1

    def test_other_error_is_swallowed_per_repo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            f"{_MOD}.load_repo_config",
            lambda name: {"repo_url": f"https://github.com/owner/{name}"},
        )
        monkeypatch.setattr(f"{_MOD}.IssueManager", MagicMock())
        get_all = MagicMock(side_effect=RuntimeError("boom"))
        monkeypatch.setattr(f"{_MOD}.get_all_cached_issues", get_all)

        cached, failed = _build_cached_issues_by_repo(["repo1", "repo2"])

        assert cached == {}
        assert failed == {"owner/repo1", "owner/repo2"}
        assert get_all.call_count == 2
