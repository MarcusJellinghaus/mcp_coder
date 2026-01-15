"""Tests for Jenkins client module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from jenkins import JenkinsException

from mcp_coder.utils.jenkins_operations.client import (
    JenkinsClient,
    JenkinsError,
)
from mcp_coder.utils.jenkins_operations.models import JobStatus


class TestJenkinsClientInit:
    """Tests for JenkinsClient initialization."""

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_init_success(self, mock_jenkins_class: MagicMock) -> None:
        """Test successful initialization."""
        # Setup
        mock_client = Mock()
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


class TestJenkinsClientStartJob:
    """Tests for JenkinsClient.start_job method."""

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_success(self, mock_jenkins_class: MagicMock) -> None:
        """Test successful job start returns queue ID."""
        # Setup
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
        mock_jenkins_class.return_value = mock_client

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(ValueError, match="params must be a dict"):
            client.start_job("test-job", "not-a-dict")  # pyright: ignore

        with pytest.raises(ValueError, match="params must be a dict"):
            client.start_job("test-job", ["list", "not", "dict"])  # pyright: ignore

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_jenkins_error(self, mock_jenkins_class: MagicMock) -> None:
        """Test JenkinsException is wrapped as JenkinsError."""
        # Setup
        mock_client = Mock()
        mock_jenkins_class.return_value = mock_client
        mock_client.build_job.side_effect = JenkinsException("Job not found")

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(JenkinsError, match="Failed to start job 'test-job'"):
            client.start_job("test-job")

    @patch("mcp_coder.utils.jenkins_operations.client.Jenkins")
    def test_start_job_generic_error(self, mock_jenkins_class: MagicMock) -> None:
        """Test generic exceptions are wrapped as JenkinsError."""
        # Setup
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
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
        mock_client = Mock()
        mock_jenkins_class.return_value = mock_client
        mock_client.get_queue_item.side_effect = JenkinsException("Queue item expired")

        client = JenkinsClient("http://jenkins:8080", "user", "token")

        # Execute & Verify
        with pytest.raises(
            JenkinsError, match="Failed to get status for queue_id 12345"
        ):
            client.get_job_status(12345)
