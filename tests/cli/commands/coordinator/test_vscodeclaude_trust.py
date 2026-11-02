"""vscodeclaude intervention mode: issue manager wiring and rate-limit stop."""

import argparse
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.cli.commands.coordinator.commands_vscodeclaude import (
    execute_coordinator_vscodeclaude,
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
