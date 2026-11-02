"""vscodeclaude trust wiring: intervention mode and the status command."""

import argparse
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
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


@pytest.fixture
def intervention_mocks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator of the intervention path with a MagicMock."""
    issue_manager = MagicMock()
    issue_manager.get_issue.return_value = {
        "number": 42,
        "title": "Test",
        "labels": [],
        "state": "open",
        "url": "",
    }
    branch_manager = MagicMock()
    branch_manager.get_branch_with_pr_fallback.return_value = "feature-branch"
    mocks = SimpleNamespace(
        create_default_config=MagicMock(return_value=False),
        load_vscodeclaude_config=MagicMock(
            return_value={"workspace_base": "/tmp", "max_sessions": 5}
        ),
        load_repo_config=MagicMock(
            return_value={"repo_url": "https://github.com/owner/repo.git"}
        ),
        IssueManager=MagicMock(return_value=issue_manager),
        IssueBranchManager=MagicMock(return_value=branch_manager),
        load_repo_vscodeclaude_config=MagicMock(return_value={}),
        prepare_and_launch_session=MagicMock(return_value={"issue_number": 42}),
    )
    for name, mock in vars(mocks).items():
        monkeypatch.setattr(f"{_MOD}.{name}", mock)
    mocks.issue_manager = issue_manager
    return mocks


def _intervene_args() -> argparse.Namespace:
    return argparse.Namespace(
        repo="repo",
        max_sessions=None,
        cleanup=False,
        intervene=True,
        issue=42,
        no_install_from_github=False,
    )


def _stop_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if _STOP_LINE in r.getMessage()]


class TestInterventionTrust:
    """execute_coordinator_vscodeclaude with --intervene."""

    def test_passes_issue_manager_and_intervention_flag(
        self, intervention_mocks: SimpleNamespace
    ) -> None:
        result = execute_coordinator_vscodeclaude(_intervene_args())

        assert result == 0
        kwargs = intervention_mocks.prepare_and_launch_session.call_args.kwargs
        assert kwargs["issue_manager"] is intervention_mocks.issue_manager
        assert kwargs["is_intervention"] is True

    def test_rate_limit_error_exits_zero_with_stop_line(
        self,
        intervention_mocks: SimpleNamespace,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        intervention_mocks.prepare_and_launch_session.side_effect = (
            GitHubRateLimitError("limited")
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_intervene_args())

        assert result == 0
        assert len(_stop_lines(caplog)) == 1
        assert all(r.exc_info is None for r in caplog.records)

    def test_raw_rate_limit_exception_exits_zero(
        self,
        intervention_mocks: SimpleNamespace,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        intervention_mocks.prepare_and_launch_session.side_effect = _rest_rate_limit()

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude(_intervene_args())

        assert result == 0
        assert len(_stop_lines(caplog)) == 1

    def test_other_error_is_reraised(self, intervention_mocks: SimpleNamespace) -> None:
        intervention_mocks.prepare_and_launch_session.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            execute_coordinator_vscodeclaude(_intervene_args())


@pytest.fixture
def status_mocks(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch every collaborator of the status command with a MagicMock."""
    sessions = [{"repo": "owner/repo", "issue_number": 7}]
    mocks = SimpleNamespace(
        load_sessions=MagicMock(
            return_value={"sessions": sessions, "last_updated": ""}
        ),
        load_config=MagicMock(return_value={"coordinator": {"repos": {"repo": {}}}}),
        load_vscodeclaude_config=MagicMock(
            return_value={"workspace_base": "/tmp", "max_sessions": 5}
        ),
        _build_cached_issues_by_repo=MagicMock(return_value=({}, set())),
        build_assessments=MagicMock(return_value={}),
        render_explain=MagicMock(return_value="EXPLAIN TEXT"),
    )
    for name, mock in vars(mocks).items():
        monkeypatch.setattr(f"{_MOD}.{name}", mock)
    mocks.sessions = sessions
    mocks.eligible = [("owner/repo", {"number": 42})]
    mocks.without_branch = {("owner/repo", 5)}
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.issues."
        "build_eligible_issues_with_branch_check",
        MagicMock(return_value=(mocks.eligible, mocks.without_branch)),
    )
    mocks.finder = MagicMock(return_value={("owner/repo", 42)})
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.issues.find_untrusted_launch_keys",
        mocks.finder,
    )
    mocks.display_status_table = MagicMock()
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.status.display_status_table",
        mocks.display_status_table,
    )
    return mocks


class TestStatusTrust:
    """execute_coordinator_vscodeclaude_status wiring of find_untrusted_launch_keys."""

    def test_explain_skips_finder(self, status_mocks: SimpleNamespace) -> None:
        result = execute_coordinator_vscodeclaude_status(
            argparse.Namespace(repo=None, explain=True)
        )

        assert result == 0
        status_mocks.finder.assert_not_called()

    def test_finder_rate_limit_exits_zero_without_table(
        self, status_mocks: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        status_mocks.finder.side_effect = GitHubRateLimitError("limited")

        with caplog.at_level(logging.DEBUG):
            result = execute_coordinator_vscodeclaude_status(
                argparse.Namespace(repo=None, explain=False)
            )

        assert result == 0
        status_mocks.display_status_table.assert_not_called()
        assert len(_stop_lines(caplog)) == 1

    def test_finder_result_passed_to_display(
        self, status_mocks: SimpleNamespace
    ) -> None:
        result = execute_coordinator_vscodeclaude_status(
            argparse.Namespace(repo="repo", explain=False)
        )

        assert result == 0
        status_mocks.finder.assert_called_once_with(
            status_mocks.eligible,
            status_mocks.sessions,
            status_mocks.without_branch,
            "repo",
        )
        kwargs = status_mocks.display_status_table.call_args.kwargs
        assert kwargs["untrusted_keys"] == {("owner/repo", 42)}
