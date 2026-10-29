"""Tests for the rate-limit helpers in workflow_utils.rate_limit."""

import logging
from datetime import datetime, timezone

import pytest

from mcp_coder.mcp_workspace_github import GithubException, GitHubRateLimitError
from mcp_coder.workflow_utils.rate_limit import (
    as_rate_limit,
    log_rate_limit_stop,
    raise_if_rate_limited,
)

RESET_EPOCH = 1_900_000_000


def _rest_rate_limit() -> GithubException:
    return GithubException(
        403,
        {"message": "API rate limit exceeded"},
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(RESET_EPOCH)},
    )


def _graphql_rate_limit() -> GithubException:
    return GithubException(400, {"errors": [{"type": "RATE_LIMITED"}]})


def _wrapped_rate_limit() -> ValueError:
    try:
        try:
            raise _rest_rate_limit()
        except GithubException as e:
            raise ValueError("could not get user") from e
    except ValueError as wrapped:
        return wrapped


class TestAsRateLimit:
    """as_rate_limit recognises all rate-limit shapes."""

    def test_rate_limit_error_returned_unchanged(self) -> None:
        exc = GitHubRateLimitError("limited")
        assert as_rate_limit(exc) is exc

    def test_rest_rate_limit_has_reset_at(self) -> None:
        result = as_rate_limit(_rest_rate_limit())
        assert isinstance(result, GitHubRateLimitError)
        assert result.reset_at == datetime.fromtimestamp(RESET_EPOCH, tz=timezone.utc)

    def test_graphql_rate_limit_without_reset_at(self) -> None:
        result = as_rate_limit(_graphql_rate_limit())
        assert isinstance(result, GitHubRateLimitError)
        assert result.reset_at is None

    def test_rate_limit_wrapped_as_cause(self) -> None:
        assert isinstance(as_rate_limit(_wrapped_rate_limit()), GitHubRateLimitError)

    def test_not_found_is_not_rate_limit(self) -> None:
        assert as_rate_limit(GithubException(404, {"message": "Not Found"})) is None

    def test_plain_value_error_is_not_rate_limit(self) -> None:
        assert as_rate_limit(ValueError("boom")) is None


class TestRaiseIfRateLimited:
    """raise_if_rate_limited raises only for rate limits."""

    def test_raises_with_cause(self) -> None:
        original = _rest_rate_limit()
        with pytest.raises(GitHubRateLimitError) as exc_info:
            raise_if_rate_limited(original)
        assert exc_info.value.__cause__ is original

    def test_reraises_rate_limit_error_itself(self) -> None:
        original = GitHubRateLimitError("limited")
        with pytest.raises(GitHubRateLimitError) as exc_info:
            raise_if_rate_limited(original)
        assert exc_info.value is original

    def test_noop_for_other_errors(self) -> None:
        raise_if_rate_limited(ValueError("boom"))
        raise_if_rate_limited(GithubException(404, {"message": "Not Found"}))


class TestLogRateLimitStop:
    """log_rate_limit_stop writes one line with or without the reset time."""

    def test_with_reset_at(self, caplog: pytest.LogCaptureFixture) -> None:
        reset_at = datetime.fromtimestamp(RESET_EPOCH, tz=timezone.utc)
        with caplog.at_level(logging.DEBUG):
            log_rate_limit_stop(GitHubRateLimitError("limited", reset_at))
        assert "GitHub rate limit hit" in caplog.text
        assert "reset at" in caplog.text

    def test_without_reset_at(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.DEBUG):
            log_rate_limit_stop(GitHubRateLimitError("limited"))
        assert "reset time unknown" in caplog.text
