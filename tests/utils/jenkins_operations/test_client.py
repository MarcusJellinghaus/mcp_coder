"""Tests for Jenkins client module."""

import logging
import re
from pathlib import Path
from typing import Any, Union
from unittest.mock import MagicMock, Mock, patch

import pytest
from jenkins import JenkinsException, NotFoundException
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError

from mcp_coder.utils.jenkins_operations.client import (
    JenkinsClient,
    JenkinsError,
    _get_jenkins_config,
    _http_error_hint,
)
from mcp_coder.utils.jenkins_operations.models import JobStatus

BASE_URL = "http://jenkins:8080"

# The hostile ~60-line Jenkins error page (see step 3), used here in the exact
# shape python-jenkins produces: its own one-line message, then the raw body.
FIXTURE_HTML = (
    Path(__file__).parent / "fixtures" / "jenkins_403_access_denied.html"
).read_text(encoding="utf-8")
FIXTURE_ERROR = "job_manager is missing the Overall/Read permission"

FORBIDDEN_HEAD = "Error in request. Possibly authentication failed [403]: Forbidden"
SERVER_ERROR_HEAD = (
    "Error in request. Possibly authentication failed [500]: Internal Server Error"
)
SERVER_ERROR_BODY = (
    "<html><body><h1>Oops!</h1>"
    '<p class="error">A problem occurred while processing the request</p>'
    "</body></html>"
)


def _response(status: int, text: str = "") -> MagicMock:
    """Build a minimal requests.Response double."""
    response = MagicMock()
    response.status_code = status
    response.ok = 200 <= status < 400
    response.text = text
    return response


def _mock_jenkins(
    mock_jenkins_class: MagicMock,
    responses: Union[dict[str, Union[MagicMock, Exception]], None] = None,
) -> MagicMock:
    """Configure the patched Jenkins class with a URL-keyed probe session.

    Args:
        mock_jenkins_class: The patched ``client.Jenkins`` class.
        responses: Probe responses keyed by absolute URL. An Exception value is
            raised instead of returned.

    Returns:
        The mocked python-jenkins client, whose ``_session.get`` is a Mock.
    """
    mock_client = MagicMock()
    mock_client.server = BASE_URL + "/"
    mock_jenkins_class.return_value = mock_client

    lookup = responses or {}

    def _get(url: str, **_kwargs: Any) -> MagicMock:
        entry = lookup[url]
        if isinstance(entry, Exception):
            raise entry
        return entry

    # A plain MagicMock (not spec=Session): _http reads session.auth, which is
    # an instance attribute and therefore absent from a specced Session double.
    session = MagicMock()
    session.get.side_effect = _get
    mock_client._session = session
    return mock_client


class TestGetJenkinsConfig:
    """Tests for _get_jenkins_config helper."""

    def test_config_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment variables."""
        # Setup - set all env vars
        monkeypatch.setenv("JENKINS_URL", "http://jenkins-env:8080")
        monkeypatch.setenv("JENKINS_USER", "env-user")
        monkeypatch.setenv("JENKINS_TOKEN", "env-token")

        # Execute
        config = _get_jenkins_config()

        # Verify
        assert config["server_url"] == "http://jenkins-env:8080"
        assert config["username"] == "env-user"
        assert config["api_token"] == "env-token"

    @patch("mcp_coder.utils.jenkins_operations.client.get_config_values")
    def test_config_from_config_file(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test configuration from config file."""
        # Setup - no env vars, use config file
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        # Mock config file values - the new batch API returns a dict
        mock_get_config.return_value = {
            ("jenkins", "server_url"): "http://jenkins-config:8080",
            ("jenkins", "username"): "config-user",
            ("jenkins", "api_token"): "config-token",
        }

        # Execute
        config = _get_jenkins_config()

        # Verify
        assert config["server_url"] == "http://jenkins-config:8080"
        assert config["username"] == "config-user"
        assert config["api_token"] == "config-token"

    @patch("mcp_coder.utils.user_config.get_config_file_path")
    def test_config_env_priority(
        self,
        mock_config_path: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test environment variables take priority over config file.

        Note: get_config_value now handles environment variables internally,
        so we must let the real function run. We mock the config file instead.
        """
        # Setup - set env vars for URL and user, but not token
        monkeypatch.setenv("JENKINS_URL", "http://jenkins-env:8080")
        monkeypatch.setenv("JENKINS_USER", "env-user")
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)  # Only token from config

        # Create a mock config file with all values
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            "[jenkins]\n"
            'server_url = "http://jenkins-config:8080"\n'
            'username = "config-user"\n'
            'api_token = "config-token"\n'
        )
        mock_config_path.return_value = config_file

        # Execute
        config = _get_jenkins_config()

        # Verify - env vars win for URL and user, config for token
        assert config["server_url"] == "http://jenkins-env:8080"
        assert config["username"] == "env-user"
        assert config["api_token"] == "config-token"

    @patch("mcp_coder.utils.jenkins_operations.client.get_config_values")
    def test_config_missing_returns_none(
        self, mock_get_config: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test missing config returns None values."""
        # Setup - no env vars, no config file
        monkeypatch.delenv("JENKINS_URL", raising=False)
        monkeypatch.delenv("JENKINS_USER", raising=False)
        monkeypatch.delenv("JENKINS_TOKEN", raising=False)

        # The new batch API returns a dict with None values for missing config
        mock_get_config.return_value = {
            ("jenkins", "server_url"): None,
            ("jenkins", "username"): None,
            ("jenkins", "api_token"): None,
        }

        # Execute
        config = _get_jenkins_config()

        # Verify
        assert config["server_url"] is None
        assert config["username"] is None
        assert config["api_token"] is None


class TestJenkinsClientInit:
    """Tests for JenkinsClient initialization."""

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_success(self, mock_jenkins_class: MagicMock) -> None:
        """Test successful initialization."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Execute
        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Verify
        mock_jenkins_class.assert_called_once_with(
            "http://jenkins:8080", username="user", password="token", timeout=30
        )
        assert client._client == mock_client

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_missing_server_url(self, mock_jenkins_class: MagicMock) -> None:
        """Test initialization fails with missing server_url."""
        # Execute & Verify
        with pytest.raises(ValueError, match="server_url is required"):
            JenkinsClient(None, "user", "token")  # type: ignore

        with pytest.raises(ValueError, match="server_url is required"):
            JenkinsClient("", "user", "token")

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_missing_username(self, mock_jenkins_class: MagicMock) -> None:
        """Test initialization fails with missing username."""
        # Execute & Verify
        with pytest.raises(ValueError, match="username is required"):
            JenkinsClient("http://jenkins:8080", None, "token")  # type: ignore

        with pytest.raises(ValueError, match="username is required"):
            JenkinsClient("http://jenkins:8080", "", "token")

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_missing_api_token(self, mock_jenkins_class: MagicMock) -> None:
        """Test initialization fails with missing api_token."""
        # Execute & Verify
        with pytest.raises(ValueError, match="api_token is required"):
            JenkinsClient("http://jenkins:8080", "user", None)  # type: ignore

        with pytest.raises(ValueError, match="api_token is required"):
            JenkinsClient("http://jenkins:8080", "user", "")

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_empty_string_values(self, mock_jenkins_class: MagicMock) -> None:
        """Test initialization fails with empty strings."""
        # Execute & Verify - empty server_url
        with pytest.raises(ValueError, match="server_url is required"):
            JenkinsClient("   ", "user", "token")

        # Empty username
        with pytest.raises(ValueError, match="username is required"):
            JenkinsClient("http://jenkins:8080", "   ", "token")

        # Empty api_token
        with pytest.raises(ValueError, match="api_token is required"):
            JenkinsClient("http://jenkins:8080", "user", "   ")


class TestJenkinsClientHttpAccess:
    """Tests for the base_url / _http seam onto python-jenkins internals.

    These tests deliberately do NOT patch client.Jenkins - they exist to pin
    real python-jenkins behaviour (session ownership, lazy auth resolution),
    which a Mock would make untestable. Constructing a Jenkins object performs
    no network I/O.
    """

    @pytest.mark.parametrize(
        "server_url", ["http://jenkins:8080", "http://jenkins:8080/"]
    )
    def test_base_url_strips_trailing_slash(self, server_url: str) -> None:
        """base_url has no trailing slash regardless of the configured URL."""
        client = JenkinsClient(server_url, "user", "token")

        assert client.base_url == "http://jenkins:8080"

    def test_http_session_is_the_library_session(self) -> None:
        """_http returns python-jenkins' own session, not a fresh one."""
        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert client._http is client._client._session

    def test_http_session_is_authenticated_on_first_access(self) -> None:
        """_http resolves basic auth before any request has been issued.

        Regression guard: this fails if a future python-jenkins reorders
        _auths or changes when session auth is populated - a diagnostic probe
        would then go out anonymous and misreport a false 401/403.
        """
        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert isinstance(client._http.auth, HTTPBasicAuth)

    def test_auth_resolution_makes_no_network_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neither construction nor reading _http touches the network."""

        def _fail(*args: Any, **kwargs: Any) -> None:
            raise AssertionError("_http must not issue a request")

        monkeypatch.setattr(Session, "request", _fail)

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert client._http.auth is not None

    def test_http_tolerates_missing_auths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unexpected _auths shape degrades to an unauthenticated session."""
        client = JenkinsClient("http://jenkins:8080", "user", "token")
        # Simulate python-jenkins renaming/reshaping its internals
        monkeypatch.setattr(client._client, "_auths", object())
        client._client._session.auth = None

        assert client._http is client._client._session
        assert client._http.auth is None


class TestJenkinsClientStartJob:
    """Tests for JenkinsClient.start_job method."""

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_success(self, mock_jenkins_class: MagicMock) -> None:
        """Test successful job start returns queue ID."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.build_job.return_value = 12345

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        queue_id = client.start_job("test-job")

        # Verify
        assert queue_id == 12345
        mock_client.build_job.assert_called_once_with(
            "test-job", parameters={}, token=None
        )

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_with_params(self, mock_jenkins_class: MagicMock) -> None:
        """Test starting job with parameters."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.build_job.return_value = 12346

        client = JenkinsClient("http://jenkins:8080", "user", "token")
        params = {"BRANCH": "main", "ENV": "prod"}

        # Execute
        queue_id = client.start_job("test-job", params)

        # Verify
        assert queue_id == 12346
        mock_client.build_job.assert_called_once_with(
            "test-job", parameters=params, token=None
        )

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_folder_path(self, mock_jenkins_class: MagicMock) -> None:
        """Test starting job with folder path."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.build_job.return_value = 12347

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        queue_id = client.start_job("folder/subfolder/job-name")

        # Verify
        assert queue_id == 12347
        mock_client.build_job.assert_called_once_with(
            "folder/subfolder/job-name", parameters={}, token=None
        )

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_invalid_params_type(self, mock_jenkins_class: MagicMock) -> None:
        """Test starting job with invalid params type raises ValueError."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(ValueError, match="params must be a dict"):
            client.start_job("test-job", "not-a-dict")  # pyright: ignore

        with pytest.raises(ValueError, match="params must be a dict"):
            client.start_job("test-job", ["list", "not", "dict"])  # pyright: ignore

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_jenkins_error(self, mock_jenkins_class: MagicMock) -> None:
        """Test JenkinsException is wrapped as JenkinsError.

        The payload is the real shape python-jenkins produces - its one-line
        message plus the raw HTML body. A one-line payload here is what let the
        HTML bug look correct.
        """
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

        # Execute & Verify
        with pytest.raises(JenkinsError, match="Failed to start job 'test-job'"):
            client.start_job("test-job")

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_generic_error(self, mock_jenkins_class: MagicMock) -> None:
        """Test generic exceptions are wrapped as JenkinsError."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.build_job.side_effect = Exception("Network error")

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(JenkinsError, match="Failed to start job 'test-job'"):
            client.start_job("test-job")


class TestJenkinsClientGetJobStatus:
    """Tests for JenkinsClient.get_job_status method."""

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_queued(self, mock_jenkins_class: MagicMock) -> None:
        """Test job status when queued."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Queue item with no executable (still queued)
        mock_client.get_queue_item.return_value = {
            "executable": None,
            "why": "Waiting for executor",
        }

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        status = client.get_job_status(12345)

        # Verify
        assert isinstance(status, JobStatus)
        assert status.status == "queued"
        assert status.build_number is None
        assert status.duration_ms is None
        assert status.url is None

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_running(self, mock_jenkins_class: MagicMock) -> None:
        """Test job status when running."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Queue item with executable (job started)
        mock_client.get_queue_item.return_value = {
            "executable": {"number": 42, "url": "http://jenkins:8080/job/test/42/"}
        }

        # Build info for running job (no result yet, duration is None)
        mock_client.get_build_info.return_value = {
            "result": None,  # Still running
            "duration": 0,  # Not completed
            "url": "http://jenkins:8080/job/test/42/",
        }

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        status = client.get_job_status(12345)

        # Verify
        assert isinstance(status, JobStatus)
        assert status.status == "running"
        assert status.build_number == 42
        assert status.duration_ms is None
        assert status.url == "http://jenkins:8080/job/test/42/"

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_success(self, mock_jenkins_class: MagicMock) -> None:
        """Test job status when completed successfully."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Queue item with executable
        mock_client.get_queue_item.return_value = {
            "executable": {"number": 42, "url": "http://jenkins:8080/job/test/42/"}
        }

        # Build info for successful job
        mock_client.get_build_info.return_value = {
            "result": "SUCCESS",
            "duration": 12340,
            "url": "http://jenkins:8080/job/test/42/",
        }

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        status = client.get_job_status(12345)

        # Verify
        assert isinstance(status, JobStatus)
        assert status.status == "SUCCESS"
        assert status.build_number == 42
        assert status.duration_ms == 12340
        assert status.url == "http://jenkins:8080/job/test/42/"

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_failure(self, mock_jenkins_class: MagicMock) -> None:
        """Test job status when failed."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Queue item with executable
        mock_client.get_queue_item.return_value = {
            "executable": {"number": 42, "url": "http://jenkins:8080/job/test/42/"}
        }

        # Build info for failed job
        mock_client.get_build_info.return_value = {
            "result": "FAILURE",
            "duration": 5678,
            "url": "http://jenkins:8080/job/test/42/",
        }

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        status = client.get_job_status(12345)

        # Verify
        assert isinstance(status, JobStatus)
        assert status.status == "FAILURE"
        assert status.build_number == 42
        assert status.duration_ms == 5678
        assert status.url == "http://jenkins:8080/job/test/42/"

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_aborted(self, mock_jenkins_class: MagicMock) -> None:
        """Test job status when aborted."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client

        # Queue item with executable
        mock_client.get_queue_item.return_value = {
            "executable": {"number": 42, "url": "http://jenkins:8080/job/test/42/"}
        }

        # Build info for aborted job
        mock_client.get_build_info.return_value = {
            "result": "ABORTED",
            "duration": 3000,
            "url": "http://jenkins:8080/job/test/42/",
        }

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute
        status = client.get_job_status(12345)

        # Verify
        assert isinstance(status, JobStatus)
        assert status.status == "ABORTED"
        assert status.build_number == 42
        assert status.duration_ms == 3000
        assert status.url == "http://jenkins:8080/job/test/42/"

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_get_job_status_error(self, mock_jenkins_class: MagicMock) -> None:
        """Test errors are wrapped as JenkinsError."""
        # Setup
        mock_client = MagicMock()
        mock_jenkins_class.return_value = mock_client
        mock_client.get_queue_item.side_effect = JenkinsException("Queue item expired")

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(
            JenkinsError, match="Failed to get status for queue_id 12345"
        ):
            client.get_job_status(12345)


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
