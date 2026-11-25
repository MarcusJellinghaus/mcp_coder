"""check_pr_health re-raises GitHub rate limits."""

from unittest.mock import Mock

import pytest

from mcp_coder.mcp_workspace_github import GithubException, GitHubRateLimitError
from mcp_coder.workflows.pr_health.checks import check_pr_health
from tests.workflows.pr_health.test_checks import (
    REPO_CONFIG,
    _make_pr_issue,
    _setup,
)

CHECKS = "mcp_coder.workflows.pr_health.checks"


def _rate_limit() -> GithubException:
    return GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1900000000"},
    )


def _wrapped_rate_limit() -> ValueError:
    """The ``GET /user`` shape: a ValueError whose ``__cause__`` is the limit."""
    try:
        try:
            raise _rate_limit()
        except GithubException as e:
            raise ValueError("could not get user") from e
    except ValueError as wrapped:
        return wrapped


class TestCheckPrHealthRateLimit:
    """check_pr_health stops on the first rate limit."""

    @pytest.mark.parametrize(
        "manager_index, method",
        [
            (1, "lookup"),
            (3, "find_pr"),
            (3, "mergeable_state"),
            (3, "ci_status"),
            (2, "get_latest_ci_status"),
            (3, "feedback"),
        ],
    )
    def test_limit_in_first_issue_propagates(
        self, monkeypatch: pytest.MonkeyPatch, manager_index: int, method: str
    ) -> None:
        mocks = _setup(monkeypatch)
        if method == "get_latest_ci_status":
            mocks[3].find_pr.return_value = None  # no open PR → live CI lookup
        # BranchLookupCache.lookup converts rate limits itself.
        limit = GitHubRateLimitError("limited") if method == "lookup" else _rate_limit()
        getattr(mocks[manager_index], method).side_effect = limit
        branch_cache = mocks[1]

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1

    def test_escalate_label_limit_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"
        monkeypatch.setattr(
            f"{CHECKS}.update_workflow_label",
            Mock(side_effect=GitHubRateLimitError("limited")),
        )

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1

    def test_username_limit_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _setup(monkeypatch)
        monkeypatch.setattr(
            f"{CHECKS}.get_github_username", Mock(side_effect=_wrapped_rate_limit())
        )

        with pytest.raises(GitHubRateLimitError):
            check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1)])
