"""Tests for Jenkins client module.

Covers config resolution, construction, the base_url/_http probe seam and the
happy paths. The diagnosed error messages live in ``test_client_errors.py``;
the shared doubles and fixture constants live in ``conftest.py``.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from jenkins import JenkinsException
from requests import Session
from requests.auth import HTTPBasicAuth

from mcp_coder.utils.jenkins_operations.client import (
    JenkinsClient,
    JenkinsError,
    get_jenkins_config,
)
from mcp_coder.utils.jenkins_operations.models import JobStatus

from .conftest import BASE_URL, FIXTURE_HTML, FORBIDDEN_HEAD, _mock_jenkins, _response


class TestGetJenkinsConfig:
    """Tests for get_jenkins_config helper."""

    def test_config_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration from environment variables."""
        # Setup - set all env vars
        monkeypatch.setenv("JENKINS_URL", "http://jenkins-env:8080")
        monkeypatch.setenv("JENKINS_USER", "env-user")
        monkeypatch.setenv("JENKINS_TOKEN", "env-token")

        # Execute
        config = get_jenkins_config()

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
        config = get_jenkins_config()

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
        config = get_jenkins_config()

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
        config = get_jenkins_config()

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
    """Tests for the base_url / probe_session seam onto python-jenkins internals.

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
        """probe_session returns python-jenkins' own session, not a fresh one."""
        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert client.probe_session is client._client._session

    def test_http_session_is_authenticated_on_first_access(self) -> None:
        """probe_session resolves basic auth before any request has been issued.

        Regression guard: this fails if a future python-jenkins reorders
        _auths or changes when session auth is populated - a diagnostic probe
        would then go out anonymous and misreport a false 401/403.
        """
        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert isinstance(client.probe_session.auth, HTTPBasicAuth)

    def test_auth_resolution_makes_no_network_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neither construction nor reading probe_session touches the network."""

        def _fail(*args: Any, **kwargs: Any) -> None:
            raise AssertionError("probe_session must not issue a request")

        monkeypatch.setattr(Session, "request", _fail)

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        assert client.probe_session.auth is not None

    def test_http_tolerates_missing_auths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unexpected _auths shape degrades to an unauthenticated session."""
        client = JenkinsClient("http://jenkins:8080", "user", "token")
        # Simulate python-jenkins renaming/reshaping its internals
        monkeypatch.setattr(client._client, "_auths", object())
        client._client._session.auth = None

        assert client.probe_session is client._client._session
        assert client.probe_session.auth is None


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
