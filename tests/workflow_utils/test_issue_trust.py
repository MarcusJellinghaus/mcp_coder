"""Tests for evaluate_body_trust in workflow_utils.issue_trust."""

from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    GithubException,
    GitHubRateLimitError,
    IssueData,
    IssueManager,
    create_empty_issue_data,
)
from mcp_coder.workflow_utils.issue_trust import evaluate_body_trust


def _issue() -> IssueData:
    issue = create_empty_issue_data()
    issue["number"] = 42
    return issue


def _manager(**kwargs: object) -> MagicMock:
    manager = MagicMock(spec=IssueManager)
    for name, value in kwargs.items():
        setattr(manager.check_body_trust, name, value)
    return manager


@pytest.mark.parametrize(
    "status", [BodyTrust.TRUSTED, BodyTrust.UNTRUSTED, BodyTrust.LOOKUP_FAILED]
)
def test_upstream_result_passed_through(status: BodyTrust) -> None:
    result = BodyTrustResult(status=status, reason="upstream reason")
    manager = _manager(return_value=result)
    issue = _issue()

    assert evaluate_body_trust(manager, issue) is result
    manager.check_body_trust.assert_called_once_with(issue)


def test_other_exception_becomes_lookup_failed_with_type_name() -> None:
    manager = _manager(side_effect=RuntimeError("secret text"))

    result = evaluate_body_trust(manager, _issue())

    assert result.status is BodyTrust.LOOKUP_FAILED
    assert result.reason == "RuntimeError"
    assert "secret text" not in result.reason


def test_rate_limit_error_reraised() -> None:
    error = GitHubRateLimitError("limited")
    manager = _manager(side_effect=error)

    with pytest.raises(GitHubRateLimitError) as exc_info:
        evaluate_body_trust(manager, _issue())
    assert exc_info.value is error


def test_raw_rate_limit_becomes_rate_limit_error() -> None:
    raw = GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1900000000"},
    )
    manager = _manager(side_effect=raw)

    with pytest.raises(GitHubRateLimitError) as exc_info:
        evaluate_body_trust(manager, _issue())
    assert exc_info.value.__cause__ is raw
