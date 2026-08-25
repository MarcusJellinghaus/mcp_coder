"""Tests for the error messages JenkinsClient produces.

Split out of ``test_client.py`` (which covers config, construction, the probe
seam and the happy paths) to keep both modules under the repo file-size limit.
"""

import logging
import re
from unittest.mock import MagicMock, Mock, patch

import pytest
from jenkins import JenkinsException, NotFoundException
from requests.exceptions import HTTPError

from mcp_coder.utils.jenkins_operations.client import (
    JenkinsClient,
    JenkinsError,
    _http_error_hint,
)

from .conftest import (
    BASE_URL,
    FIXTURE_ERROR,
    FIXTURE_HTML,
    FORBIDDEN_HEAD,
    SERVER_ERROR_BODY,
    SERVER_ERROR_HEAD,
    _mock_jenkins,
    _response,
)


class TestStartJobHttpErrorMessages:
    """Tests for clean HTTP error messages in start_job."""

    # Only 409 reaches this branch in production: python-jenkins converts
    # 401/403/500 into JenkinsException and 404 into NotFoundException before
    # they can surface as HTTPError. The 500 case lives in
    # TestJenkinsExceptionMessages.test_start_job_500_has_no_html_and_no_probe.
    @pytest.mark.parametrize(
        "status_code,reason,expected_hint",
        [
            (409, "Conflict", " (job may be disabled, already queued, or running)"),
        ],
    )
    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_http_error_clean_message(
        self,
        mock_jenkins_class: MagicMock,
        status_code: int,
        reason: str,
        expected_hint: str,
    ) -> None:
        """HTTP errors produce clean message with appropriate hint, no URL."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.reason = reason

        http_error = HTTPError(
            f"{status_code} {reason}: https://jenkins:8080/job/folder/job/test/buildWithParameters?param=value%20encoded",
            response=mock_response,
        )
        mock_client.build_job.side_effect = http_error

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        expected_msg = f"Failed to start job 'Windows-Agents/Executor': {status_code} {reason}{expected_hint}"
        with pytest.raises(JenkinsError, match=re.escape(expected_msg)) as exc_info:
            client.start_job("Windows-Agents/Executor")
        assert "buildWithParameters" not in str(exc_info.value)
        assert "https://jenkins" not in str(exc_info.value)

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_http_error_no_response(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """HTTPError without response falls back to str(e)."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        http_error = HTTPError("Connection failed")
        http_error.response = None
        mock_client.build_job.side_effect = http_error

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(
            JenkinsError, match="Failed to start job 'test-job': Connection failed"
        ):
            client.start_job("test-job")


class TestHttpErrorHint:
    """Tests for _http_error_hint helper."""

    def test_known_status_409(self) -> None:
        """409 returns hint about disabled/queued/running."""
        assert (
            _http_error_hint(409)
            == " (job may be disabled, already queued, or running)"
        )

    def test_unknown_status_returns_empty(self) -> None:
        """Unknown status codes return empty string."""
        assert _http_error_hint(500) == ""
        assert _http_error_hint(404) == ""
        assert _http_error_hint(200) == ""


class TestJenkinsExceptionMessages:
    """Tests for the diagnosed messages built from python-jenkins exceptions.

    python-jenkins converts 401/403/500 into ``JenkinsException(msg + "\\n" +
    response.text)`` and 404 into ``NotFoundException`` before they escape the
    library, so these - not HTTPError - are what the handlers actually see.
    """

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_403_message_contains_no_html(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """The primary regression guard: no markup reaches the message."""
        # Setup
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(403, FIXTURE_HTML),
            },
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        message = str(excinfo.value)
        for marker in ("<html", "<svg", "<!DOCTYPE", "<template"):
            assert marker not in message
        assert len(message.splitlines()) <= 3

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_403_names_failing_endpoint_and_permission(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """The crumb-issuer rejection, the permission and the docs are named."""
        # Setup
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(403, FIXTURE_HTML),
            },
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        message = str(excinfo.value)
        assert "Failed to start job 'Windows-Agents/Executor'" in message
        assert "/crumbIssuer/api/json" in message
        assert "missing the Overall/Read permission" in message
        assert "not authorized" in message
        assert "docs/repository-setup/jenkins.md" in message

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_403_breaks_exception_chain(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """`from None` keeps the raw page out of every traceback."""
        # Setup
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/api/json": _response(403, FIXTURE_HTML),
            },
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        assert excinfo.value.__cause__ is None

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_404_names_deepest_readable_ancestor(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A 404 narrows the search to the one unreadable path segment."""
        # Setup
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/job/Windows-Agents/api/json": _response(200, "{}"),
                f"{BASE_URL}/job/Windows-Agents/job/Executor/api/json": _response(
                    404, ""
                ),
            },
        )
        mock_client.build_job.side_effect = NotFoundException(
            "Requested item could not be found"
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify - both segments named, wording stays non-committal
        message = str(excinfo.value)
        assert "'Windows-Agents'" in message
        assert "'Executor'" in message
        assert "Job/Read" in message
        assert "Check both" in message

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_403_on_build_reports_original_cause(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """When probes cannot reproduce the 403 the original sentence survives.

        The real missing-Job/Build shape: /api/json and /crumbIssuer/api/json
        both return 200, so the exception body is the only evidence there is.
        """
        # Setup
        original = "job_manager is missing the Job/Build permission"
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(200, "{}"),
            },
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD
            + "\n"
            + f'<html><body><p class="error">{original}</p></body></html>'
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        message = str(excinfo.value)
        assert original in message
        assert "may have changed" not in message
        assert "<html" not in message

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_500_has_no_html_and_no_probe(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A 500 is not a permission problem: clean the message, probe nothing."""
        # Setup
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.build_job.side_effect = JenkinsException(
            SERVER_ERROR_HEAD + "\n" + SERVER_ERROR_BODY
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        message = str(excinfo.value)
        assert "A problem occurred while processing the request" in message
        assert "<html" not in message
        assert "<p" not in message
        mock_client._session.get.assert_not_called()

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_500_does_not_claim_authentication_failure(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A 500 must not be reported as a possible authentication failure.

        python-jenkins labels 401, 403 *and* 500 "Possibly authentication
        failed". Sending an operator to check the API token for a server fault
        is the same wrong-turn the 403 wording caused; only the status and the
        reason survive.
        """
        # Setup
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.build_job.side_effect = JenkinsException(
            SERVER_ERROR_HEAD + "\n" + SERVER_ERROR_BODY
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify
        message = str(excinfo.value)
        assert "authentication failed" not in message.lower()
        assert "500 Internal Server Error" in message

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_500_does_not_claim_authentication_failure(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """The same cleaning applies on the queue-item path."""
        # Setup
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_queue_item.side_effect = JenkinsException(
            SERVER_ERROR_HEAD + "\n" + SERVER_ERROR_BODY
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.get_job_status(12345)

        # Verify
        message = str(excinfo.value)
        assert "authentication failed" not in message.lower()
        assert "500 Internal Server Error" in message

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_404_reports_queue_item(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """With no job path there is nothing to walk - say so about the item."""
        # Setup
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_queue_item.side_effect = NotFoundException(
            "Requested item could not be found"
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.get_job_status(12345)

        # Verify
        message = str(excinfo.value)
        assert "Failed to get status for queue_id 12345" in message
        assert "queue item" in message
        mock_client._session.get.assert_not_called()

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_raw_body_logged_only_at_debug(
        self, mock_jenkins_class: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The page carries a live CSRF crumb and the username: DEBUG only."""
        # Setup
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(403, FIXTURE_HTML),
            },
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute - at DEBUG the raw page is logged exactly once
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(JenkinsError):
                client.start_job("Windows-Agents/Executor")

        raw_records = [
            record
            for record in caplog.records
            if "<!DOCTYPE html" in record.getMessage()
        ]
        assert len(raw_records) == 1
        assert raw_records[0].levelno == logging.DEBUG

        # Execute - at INFO it appears nowhere
        caplog.clear()
        with caplog.at_level(logging.INFO):
            with pytest.raises(JenkinsError):
                client.start_job("Windows-Agents/Executor")

        assert not [
            record
            for record in caplog.records
            if "<!DOCTYPE html" in record.getMessage()
        ]

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_probe_failure_does_not_mask_original_error(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A broken diagnostic must never replace the error it explains."""
        # Setup - an unexpected failure inside the probe, not a RequestException
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/api/json": RuntimeError("probe exploded")},
        )
        mock_client.build_job.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")

        # Execute
        with pytest.raises(JenkinsError) as excinfo:
            client.start_job("Windows-Agents/Executor")

        # Verify - falls back to the cleaned message, chain still broken
        message = str(excinfo.value)
        assert "Failed to start job 'Windows-Agents/Executor'" in message
        assert FIXTURE_ERROR in message
        assert "<html" not in message
        assert "probe exploded" not in message
        assert excinfo.value.__cause__ is None
