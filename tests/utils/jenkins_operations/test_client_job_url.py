"""Tests for JenkinsClient.get_job_url."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests
from jenkins import NotFoundException, TimeoutException

from mcp_coder.utils.jenkins_operations.client import JenkinsClient, JenkinsError

from .conftest import BASE_URL, _mock_jenkins, _response

_JENKINS = "mcp_coder.utils.jenkins_operations.client.Jenkins"
_JOB_URL = f"{BASE_URL}/job/A/job/Executor/"


class TestGetJobUrl:
    """Tests for JenkinsClient.get_job_url."""

    @patch(_JENKINS)
    def test_job_found_returns_reported_url(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """The URL Jenkins reports is returned; one get_info call."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {"url": _JOB_URL, "buildable": True}

        client = JenkinsClient(BASE_URL, "user", "token")

        assert client.get_job_url("A/Executor") == _JOB_URL
        mock_client.get_info.assert_called_once_with(
            item="job/A/job/Executor", query="?tree=url,buildable"
        )

    @pytest.mark.parametrize("path", ["/A/Executor", "A/Executor/", "A//Executor"])
    @patch(_JENKINS)
    def test_extra_slashes_are_tolerated(
        self, mock_jenkins_class: MagicMock, path: str
    ) -> None:
        """Leading, trailing and double slashes give the same item path."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {"url": _JOB_URL, "buildable": False}

        client = JenkinsClient(BASE_URL, "user", "token")

        assert client.get_job_url(path) == _JOB_URL
        assert mock_client.get_info.call_args.kwargs["item"] == "job/A/job/Executor"

    @patch(_JENKINS)
    def test_missing_job_runs_404_diagnosis(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A wrong path is diagnosed with the ancestor walk; chain broken."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/job/A/api/json": _response(200, "{}")},
        )
        mock_client.get_info.side_effect = NotFoundException(
            "Requested item could not be found"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_job_url("A/Missing")

        message = str(excinfo.value)
        assert "Failed to look up job 'A/Missing'" in message
        assert "'A' is readable" in message
        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_folder_is_not_a_job(self, mock_jenkins_class: MagicMock) -> None:
        """A response without 'buildable' (a folder) is rejected."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {
            "url": f"{BASE_URL}/job/A/",
            "_class": "com.cloudbees.hudson.plugins.folder.Folder",
        }

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="not a job") as excinfo:
            client.get_job_url("A")

        assert "Failed to look up job 'A'" in str(excinfo.value)

    @patch(_JENKINS)
    def test_missing_url_is_not_a_job(self, mock_jenkins_class: MagicMock) -> None:
        """A response without a string URL is rejected."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {"buildable": True}

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="not a job"):
            client.get_job_url("A/Executor")

    @patch(_JENKINS)
    def test_connection_error_keeps_cause(self, mock_jenkins_class: MagicMock) -> None:
        """Transport errors outside python-jenkins keep their cause."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        error = requests.ConnectionError("refused")
        mock_client.get_info.side_effect = error

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_job_url("A/Executor")

        message = str(excinfo.value)
        assert message.startswith("Failed to look up job 'A/Executor': ")
        assert "refused" in message
        assert excinfo.value.__cause__ is error

    @patch(_JENKINS)
    def test_timeout_goes_through_wrap(self, mock_jenkins_class: MagicMock) -> None:
        """python-jenkins' TimeoutException is a JenkinsException."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.side_effect = TimeoutException(
            "Error in request: timed out"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_job_url("A/Executor")

        message = str(excinfo.value)
        assert message.startswith("Failed to look up job 'A/Executor': ")
        assert "timed out" in message
        assert excinfo.value.__cause__ is None

    @pytest.mark.parametrize(
        "side_effect",
        [
            NotFoundException("Requested item could not be found"),
            requests.ConnectionError("refused"),
            TimeoutException("Error in request: timed out"),
        ],
    )
    @patch(_JENKINS)
    def test_failure_logs_no_error_record(
        self,
        mock_jenkins_class: MagicMock,
        side_effect: Exception,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The caller logs the one error line; the client logs none itself."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/job/A/api/json": _response(200, "{}")},
        )
        mock_client.get_info.side_effect = side_effect

        client = JenkinsClient(BASE_URL, "user", "token")
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(JenkinsError):
                client.get_job_url("A/Missing")

        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
