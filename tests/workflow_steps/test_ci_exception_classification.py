"""Tests for exception classification and no-retry behavior in workflow_steps/ci.py."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import GithubException
from mcp_coder.workflow_steps.ci import (
    _classify_ci_exception,
    _poll_for_ci_completion,
    _wait_for_new_ci_run,
)
from mcp_coder.workflow_steps.constants import CI_NEW_RUN_MAX_POLL_ATTEMPTS


class TestClassifyCiException:
    """Tests for _classify_ci_exception."""

    def test_rate_limit_with_retry_after_header(self) -> None:
        """Status 403 with Retry-After header is classified as rate limit."""
        exc = GithubException(status=403, data=None, headers={"Retry-After": "30"})

        result = _classify_ci_exception(exc)

        assert "rate limit" in result
        assert "30" in result

    def test_rate_limit_with_remaining_zero_and_reset_header(self) -> None:
        """Status 429 with remaining=0 and reset header reports the reset time."""
        exc = GithubException(
            status=429,
            data=None,
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1700000000",
            },
        )

        result = _classify_ci_exception(exc)

        assert "rate limit" in result
        assert "resets at" in result
        assert "T" in result
        assert "+00:00" in result

    def test_rate_limit_status_without_matching_headers_is_not_rate_limit(
        self,
    ) -> None:
        """Status 403 with no rate-limit headers is an auth/permission error."""
        exc = GithubException(status=403, data=None, headers={})

        result = _classify_ci_exception(exc)

        assert "auth/permission" in result
        assert "rate limit" not in result

    def test_auth_status_without_headers(self) -> None:
        """Status 401 with headers=None does not raise and is auth/permission."""
        exc = GithubException(status=401, data=None, headers=None)

        result = _classify_ci_exception(exc)

        assert "auth/permission" in result

    def test_non_github_exception_is_generic(self) -> None:
        """A non-GithubException is classified as a generic unexpected error."""
        exc = ValueError("boom")

        result = _classify_ci_exception(exc)

        assert "unexpected error" in result
        assert "boom" in result
        assert "auth/permission" not in result
        assert "rate limit" not in result


class TestPollExceptionClassification:
    """_poll_for_ci_completion's exception branch logs a classified message."""

    def test_rate_limit_exception_exits_immediately_with_classified_line(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A rate-limit GithubException exits with (None, True), no retry."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = GithubException(
            status=403, data=None, headers={"Retry-After": "10"}
        )

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert status is None
        assert passed is True
        assert mock_ci_manager.get_latest_ci_status.call_count == 1
        assert "rate limit" in caplog.text

    def test_auth_exception_exits_immediately_with_classified_line(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An auth GithubException exits with (None, True), no retry."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = GithubException(
            status=401, data=None, headers=None
        )

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert status is None
        assert passed is True
        assert mock_ci_manager.get_latest_ci_status.call_count == 1
        assert "auth/permission" in caplog.text

    def test_non_github_exception_still_exits_immediately(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A non-GithubException also exits with (None, True), no retry."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = ValueError("boom")

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                status, passed = _poll_for_ci_completion(mock_ci_manager, "main")

        assert status is None
        assert passed is True
        assert mock_ci_manager.get_latest_ci_status.call_count == 1
        assert "unexpected error" in caplog.text
        assert "boom" in caplog.text
        assert "auth/permission" not in caplog.text


class TestWaitForNewCiRunNoRetryOnException:
    """_wait_for_new_ci_run exits immediately (no retry) on a raised exception."""

    def test_raised_exception_exits_immediately_no_retry(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A rate-limit GithubException exits with (None, False), no retry."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = GithubException(
            status=403, data=None, headers={"Retry-After": "5"}
        )

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                result = _wait_for_new_ci_run(
                    mock_ci_manager, "main", previous_run_ids=set()
                )

        assert result == (None, False)
        assert mock_ci_manager.get_latest_ci_status.call_count == 1
        assert "rate limit" in caplog.text

    def test_raised_generic_exception_also_exits_immediately(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A non-GithubException also exits with (None, False), no retry."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = ValueError("boom")

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.INFO):
                result = _wait_for_new_ci_run(
                    mock_ci_manager, "main", previous_run_ids=set()
                )

        assert result == (None, False)
        assert mock_ci_manager.get_latest_ci_status.call_count == 1
        assert "unexpected error" in caplog.text
        assert "No new CI run detected after 30s" not in caplog.text

    def test_timeout_without_exception_still_warns_as_before(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No-exception timeout path is unchanged: warns and returns (None, False)."""
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"run_ids": []},
            "jobs": [],
        }

        with patch("mcp_coder.workflow_steps.ci.time.sleep"):
            with caplog.at_level(logging.WARNING):
                result = _wait_for_new_ci_run(
                    mock_ci_manager, "main", previous_run_ids=set()
                )

        assert result == (None, False)
        assert mock_ci_manager.get_latest_ci_status.call_count == (
            CI_NEW_RUN_MAX_POLL_ATTEMPTS
        )
        assert "No new CI run detected after 30s" in caplog.text
