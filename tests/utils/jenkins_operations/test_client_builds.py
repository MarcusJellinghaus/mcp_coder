"""Tests for JenkinsClient.get_recent_builds and get_console_output.

python-jenkins is mocked; the pure tree/selection logic is covered by
``test_builds.py``.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
from jenkins import JenkinsException, NotFoundException, TimeoutException
from requests import Request

from mcp_coder.utils.jenkins_operations.builds import build_tree_query
from mcp_coder.utils.jenkins_operations.client import JenkinsClient, JenkinsError

from .conftest import (
    BASE_URL,
    FIXTURE_HTML,
    FORBIDDEN_HEAD,
    _mock_jenkins,
    _response,
)

_JENKINS = "mcp_coder.utils.jenkins_operations.client.Jenkins"


def _build(
    number: int, timestamp: int, result: str | None = "SUCCESS"
) -> dict[str, Any]:
    """Build a raw Jenkins build dict."""
    return {
        "number": number,
        "building": result is None,
        "result": result,
        "timestamp": timestamp,
        "duration": 1000,
        "url": f"{BASE_URL}/job/x/{number}/",
    }


def _tree() -> dict[str, Any]:
    """Return a two-job tree: a top-level job and one in folder A."""
    return {
        "jobs": [
            {
                "fullName": "top",
                "url": f"{BASE_URL}/job/top/",
                "builds": [
                    _build(1, 1_000_000, "SUCCESS"),
                    _build(2, 3_000_000, "FAILURE"),
                ],
            },
            {
                "fullName": "A",
                "url": f"{BASE_URL}/job/A/",
                "jobs": [
                    {
                        "fullName": "A/job",
                        "url": f"{BASE_URL}/job/A/job/job/",
                        "builds": [_build(5, 2_000_000, "FAILURE")],
                    }
                ],
            },
        ]
    }


class TestGetRecentBuilds:
    """Tests for JenkinsClient.get_recent_builds."""

    @patch(_JENKINS)
    def test_single_request_returns_builds_newest_first(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """One get_info call over the root; builds merged and sorted."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = _tree()

        client = JenkinsClient(BASE_URL, "user", "token")
        builds = client.get_recent_builds()

        mock_client.get_info.assert_called_once_with(
            item="", query=build_tree_query(100)
        )
        assert [(b.job_path, b.number) for b in builds] == [
            ("top", 2),
            ("A/job", 5),
            ("top", 1),
        ]
        assert builds[1].folder == "A"
        assert builds[1].job_name == "job"
        assert builds[0].status == "failure"

    @pytest.mark.parametrize("limit,field", [(100, "builds["), (101, "allBuilds[")])
    @patch(_JENKINS)
    def test_limit_selects_builds_or_all_builds(
        self, mock_jenkins_class: MagicMock, limit: int, field: str
    ) -> None:
        """limit above 100 switches the query to allBuilds."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {"jobs": []}

        client = JenkinsClient(BASE_URL, "user", "token")
        assert client.get_recent_builds(limit=limit) == []

        mock_client.get_info.assert_called_once()
        query = mock_client.get_info.call_args.kwargs["query"]
        assert field in query
        if field == "builds[":
            assert "allBuilds[" not in query

    @patch(_JENKINS)
    def test_folder_becomes_item_path(self, mock_jenkins_class: MagicMock) -> None:
        """folder segments are passed unencoded as job/<a>/job/<b>."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = {"jobs": []}

        client = JenkinsClient(BASE_URL, "user", "token")
        client.get_recent_builds(folder="A/B")

        assert mock_client.get_info.call_args.kwargs["item"] == "job/A/job/B"

    @patch(_JENKINS)
    def test_unknown_status_raises_value_error_before_request(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """An invalid status is a caller error, not a JenkinsError."""
        mock_client = _mock_jenkins(mock_jenkins_class)

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(ValueError, match="failed"):
            client.get_recent_builds(statuses=["failed"])

        mock_client.get_info.assert_not_called()

    @pytest.mark.parametrize("limit", [0, -5])
    @patch(_JENKINS)
    def test_limit_below_one_raises_value_error_before_request(
        self, mock_jenkins_class: MagicMock, limit: int
    ) -> None:
        """A limit below 1 is a caller error, not a JenkinsError."""
        mock_client = _mock_jenkins(mock_jenkins_class)

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(ValueError, match="limit"):
            client.get_recent_builds(limit=limit)

        mock_client.get_info.assert_not_called()

    @patch(_JENKINS)
    def test_statuses_filter_after_truncation(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """limit is a window over the newest builds; statuses filter inside it."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.return_value = _tree()

        client = JenkinsClient(BASE_URL, "user", "token")
        builds = client.get_recent_builds(limit=1, statuses=["failure"])
        assert [(b.job_path, b.number) for b in builds] == [("top", 2)]

        # The newest build is a failure; with limit=1 the older A/job #5
        # failure falls outside the window.
        builds = client.get_recent_builds(limit=1, statuses=["success"])
        assert builds == []

    @patch(_JENKINS)
    def test_missing_folder_runs_404_diagnosis(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """A missing folder is diagnosed with the ancestor walk."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/job/A/api/json": _response(200, "{}")},
        )
        mock_client.get_info.side_effect = NotFoundException(
            "Requested item could not be found"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_recent_builds(folder="A/Missing")

        message = str(excinfo.value)
        assert "Failed to list builds in folder 'A/Missing'" in message
        assert "'A' is readable" in message
        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_403_runs_403_diagnosis(self, mock_jenkins_class: MagicMock) -> None:
        """A 403 is diagnosed by probing /api/json."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/api/json": _response(403, FIXTURE_HTML)},
        )
        mock_client.get_info.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_recent_builds()

        message = str(excinfo.value)
        assert "Failed to list builds" in message
        assert "403 Forbidden on /api/json" in message
        assert "<html" not in message

    @patch(_JENKINS)
    def test_timeout_goes_through_wrap(self, mock_jenkins_class: MagicMock) -> None:
        """python-jenkins' TimeoutException is a JenkinsException."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.get_info.side_effect = TimeoutException(
            "Error in request: timed out"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="timed out") as excinfo:
            client.get_recent_builds()

        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_connection_error_goes_through_generic_branch(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """Transport errors outside python-jenkins keep their cause."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        error = requests.ConnectionError("refused")
        mock_client.get_info.side_effect = error

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="refused") as excinfo:
            client.get_recent_builds()

        assert excinfo.value.__cause__ is error


class TestGetConsoleOutput:
    """Tests for JenkinsClient.get_console_output."""

    @patch(_JENKINS)
    def test_requests_console_text_url(self, mock_jenkins_class: MagicMock) -> None:
        """Encoded branch names are encoded again in the URL."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.jenkins_open.return_value = "line 1\nline 2\n"

        client = JenkinsClient(BASE_URL, "user", "token")
        text = client.get_console_output("A/mb/feature%2Fx", 7)

        assert text == "line 1\nline 2\n"
        mock_client.jenkins_open.assert_called_once()
        request = mock_client.jenkins_open.call_args.args[0]
        assert isinstance(request, Request)
        assert request.method == "GET"
        assert request.url == f"{BASE_URL}/job/A/job/mb/job/feature%252Fx/7/consoleText"

    @patch(_JENKINS)
    def test_404_runs_build_diagnosis(self, mock_jenkins_class: MagicMock) -> None:
        """A readable job with a missing build blames the build record."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/job/A/job/B/api/json": _response(200, "{}")},
        )
        mock_client.jenkins_open.side_effect = NotFoundException(
            "Requested item could not be found"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_console_output("A/B", 7)

        message = str(excinfo.value)
        assert "Failed to get console output for 'A/B' #7" in message
        assert "build #7" in message
        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_403_runs_403_diagnosis(self, mock_jenkins_class: MagicMock) -> None:
        """A 403 is diagnosed via _wrap_jenkins_error."""
        mock_client = _mock_jenkins(
            mock_jenkins_class,
            {f"{BASE_URL}/api/json": _response(403, FIXTURE_HTML)},
        )
        mock_client.jenkins_open.side_effect = JenkinsException(
            FORBIDDEN_HEAD + "\n" + FIXTURE_HTML
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError) as excinfo:
            client.get_console_output("A/B", 7)

        message = str(excinfo.value)
        assert "403 Forbidden on /api/json" in message
        assert "<html" not in message
        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_timeout_raises_jenkins_error(self, mock_jenkins_class: MagicMock) -> None:
        """A timeout becomes a JenkinsError."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        mock_client.jenkins_open.side_effect = TimeoutException(
            "Error in request: timed out"
        )

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="timed out") as excinfo:
            client.get_console_output("A/B", 7)

        assert excinfo.value.__cause__ is None

    @patch(_JENKINS)
    def test_connection_error_goes_through_generic_branch(
        self, mock_jenkins_class: MagicMock
    ) -> None:
        """Transport errors outside python-jenkins keep their cause."""
        mock_client = _mock_jenkins(mock_jenkins_class)
        error = requests.ConnectionError("refused")
        mock_client.jenkins_open.side_effect = error

        client = JenkinsClient(BASE_URL, "user", "token")
        with pytest.raises(JenkinsError, match="refused") as excinfo:
            client.get_console_output("A/B", 7)

        assert excinfo.value.__cause__ is error
