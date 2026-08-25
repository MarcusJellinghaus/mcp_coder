"""Test configuration and shared doubles for jenkins_operations tests."""

import sys
from pathlib import Path
from typing import Any, Union
from unittest.mock import MagicMock

# Add src directory to Python path to ensure jenkins_operations module can be imported
# This is needed when the package editable install hasn't picked up new modules yet
project_root = Path(__file__).parent.parent.parent.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


BASE_URL = "http://jenkins:8080"

# The hostile ~60-line Jenkins error page (see step 3), used in the exact shape
# python-jenkins produces: its own one-line message, then the raw body.
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
