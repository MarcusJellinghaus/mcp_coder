"""Tests for Jenkins diagnostics helpers.

No network: every probe runs against a ``Mock(spec=Session)`` whose ``get()``
is keyed by URL.
"""

from pathlib import Path
from typing import Any, Union, cast
from unittest.mock import MagicMock, Mock

import pytest
from requests import RequestException, Session

from mcp_coder.utils.jenkins_operations.diagnostics import (
    _MAX_ERROR_LEN,
    DOCS_POINTER,
    diagnose_403,
    diagnose_404,
    extract_jenkins_error,
    job_url_path,
    probe,
)

BASE_URL = "http://jenkins:8080"
FIXTURE_DIR = Path(__file__).parent / "fixtures"

# The single sentence the hostile fixture must yield.
FIXTURE_ERROR = "job_manager is missing the Overall/Read permission"


@pytest.fixture(name="access_denied_html")
def fixture_access_denied_html() -> str:
    """The synthesised Jenkins 403 page (comment-wrapped, no closing </p>)."""
    return (FIXTURE_DIR / "jenkins_403_access_denied.html").read_text(encoding="utf-8")


def _response(status: int, text: str = "") -> MagicMock:
    """Build a minimal requests.Response double."""
    response = MagicMock()
    response.status_code = status
    response.ok = 200 <= status < 400
    response.text = text
    return response


def _session(responses: dict[str, Union[MagicMock, Exception]]) -> Session:
    """Build a Session double whose get() is keyed by absolute URL."""
    session = Mock(spec=Session)

    def _get(url: str, **_kwargs: Any) -> MagicMock:
        entry = responses[url]
        if isinstance(entry, Exception):
            raise entry
        return entry

    session.get.side_effect = _get
    return cast(Session, session)


class TestExtractJenkinsError:
    """Tests for extract_jenkins_error."""

    def test_hostile_fixture_yields_the_error_sentence(
        self, access_denied_html: str
    ) -> None:
        """The comment-wrapped <p class="error"> with no closing tag is extracted."""
        assert extract_jenkins_error(access_denied_html) == FIXTURE_ERROR

    def test_hostile_fixture_leaks_neither_crumb_nor_markup(
        self, access_denied_html: str
    ) -> None:
        """The extracted line must not carry the CSRF crumb or any markup."""
        result = extract_jenkins_error(access_denied_html)

        assert result is not None
        assert "crumb" not in result.lower()
        assert "<" not in result

    def test_well_formed_error_paragraph(self) -> None:
        """A tidy <p class="error">Foo</p> yields 'Foo'."""
        body = '<html><body><p class="error">Foo</p></body></html>'

        assert extract_jenkins_error(body) == "Foo"

    def test_html_entities_are_unescaped(self) -> None:
        """&#039; becomes a plain apostrophe."""
        body = '<p class="error">user &#039;job_manager&#039; is denied</p>'

        assert extract_jenkins_error(body) == "user 'job_manager' is denied"

    def test_h1_fallback(self) -> None:
        """A page with only an <h1> falls back to the heading text."""
        body = "<html><body><h1>Access Denied</h1><div>noise</div></body></html>"

        assert extract_jenkins_error(body) == "Access Denied"

    def test_unrecognised_page_is_bounded(self) -> None:
        """No marker at all still returns bounded text, not the whole page."""
        body = "<div>" + ("permission denied blah " * 200) + "</div>"

        result = extract_jenkins_error(body)

        assert result is not None
        assert len(result) <= _MAX_ERROR_LEN + 3
        assert result.endswith("...")

    @pytest.mark.parametrize("body", ["", "   ", "\n\t "])
    def test_empty_body_returns_none(self, body: str) -> None:
        """Empty or whitespace-only bodies have nothing to report."""
        assert extract_jenkins_error(body) is None

    def test_markup_only_body_returns_none(self) -> None:
        """A body that is nothing but tags yields no sentence."""
        assert extract_jenkins_error("<div><span></span></div>") is None


class TestJobUrlPath:
    """Tests for job_url_path."""

    def test_folder_and_job(self) -> None:
        """Each path segment gets its own /job/ prefix."""
        assert job_url_path("A/B") == "/job/A/job/B"

    def test_segments_are_percent_encoded(self) -> None:
        """Spaces and '#' are encoded so the URL stays valid."""
        assert job_url_path("Tests/my job#2") == "/job/Tests/job/my%20job%232"

    def test_leading_and_trailing_slashes_tolerated(self) -> None:
        """Surrounding slashes produce no empty segments."""
        assert job_url_path("/Tests/mcp-coder-test/") == "/job/Tests/job/mcp-coder-test"


class TestProbe:
    """Tests for probe."""

    def test_success_has_no_error_text(self) -> None:
        """A 200 carries no error sentence."""
        session = _session({f"{BASE_URL}/api/json": _response(200, "{}")})

        result = probe(session, BASE_URL, "/api/json")

        assert result.status == 200
        assert result.url == f"{BASE_URL}/api/json"
        assert result.error_text is None

    def test_failure_extracts_error_text(self, access_denied_html: str) -> None:
        """A 403 body is reduced to its error sentence."""
        session = _session({f"{BASE_URL}/api/json": _response(403, access_denied_html)})

        result = probe(session, BASE_URL, "/api/json")

        assert result.status == 403
        assert result.error_text == FIXTURE_ERROR

    def test_request_exception_does_not_raise(self) -> None:
        """A transport failure is reported, never re-raised."""
        session = _session(
            {f"{BASE_URL}/api/json": RequestException("connection refused")}
        )

        result = probe(session, BASE_URL, "/api/json")

        assert result.status is None
        assert result.url == f"{BASE_URL}/api/json"
        assert result.error_text is not None
        assert "connection refused" in result.error_text

    def test_timeout_is_passed_explicitly(self) -> None:
        """session.get() bypasses Jenkins._request, so timeout must be explicit."""
        session = _session({f"{BASE_URL}/api/json": _response(200, "{}")})

        probe(session, BASE_URL, "/api/json")

        _args, kwargs = cast(Mock, session).get.call_args
        assert kwargs["timeout"] > 0


class TestDiagnose403:
    """Tests for diagnose_403."""

    def test_crumb_issuer_rejection_is_named(self, access_denied_html: str) -> None:
        """Regression guard: /api/json passing must not hide a crumb-issuer 403."""
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(403, access_denied_html),
            }
        )

        message = diagnose_403(session, BASE_URL)

        assert "/crumbIssuer/api/json" in message
        assert FIXTURE_ERROR in message
        assert "Overall/Read" in message
        assert message.endswith(DOCS_POINTER)

    def test_api_json_rejection_is_named(self, access_denied_html: str) -> None:
        """The first rejecting endpoint is the one reported."""
        session = _session({f"{BASE_URL}/api/json": _response(403, access_denied_html)})

        message = diagnose_403(session, BASE_URL)

        assert "403 Forbidden on /api/json" in message
        assert "/crumbIssuer" not in message
        assert message.endswith(DOCS_POINTER)

    def test_401_reports_authentication_not_authorization(self) -> None:
        """A 401 is a credentials problem, not a permissions problem."""
        session = _session({f"{BASE_URL}/api/json": _response(401, "")})

        message = diagnose_403(session, BASE_URL)

        assert "401 Unauthorized on /api/json" in message
        assert "Authentication failed" in message
        assert "API token" in message
        assert "not authorized" not in message
        assert message.endswith(DOCS_POINTER)

    def test_all_probes_ok_surfaces_original_error(self) -> None:
        """Regression guard: the original sentence is the only evidence there is."""
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(200, "{}"),
            }
        )
        original = "job_manager is missing the Job/Build permission"

        message = diagnose_403(session, BASE_URL, original_error=original)

        assert original in message
        assert "Job/Build" in message
        assert "Overall/Read is granted" in message
        assert message.endswith(DOCS_POINTER)

    def test_all_probes_ok_without_original_error(self) -> None:
        """With no evidence the message still points at the failing request."""
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": _response(200, "{}"),
            }
        )

        message = diagnose_403(session, BASE_URL)

        assert "both succeeded" in message
        assert "Overall/Read is granted" in message
        assert "Job/Build" in message
        assert message.endswith(DOCS_POINTER)


class TestDiagnose404:
    """Tests for diagnose_404."""

    def test_readable_folder_narrows_to_one_segment(self) -> None:
        """The deepest readable ancestor and the unreadable segment are both named."""
        session = _session(
            {f"{BASE_URL}/job/Windows-Agents/api/json": _response(200, "{}")}
        )

        message = diagnose_404(session, BASE_URL, "Windows-Agents/Executor")

        assert "Windows-Agents" in message
        assert "'Executor'" in message
        assert "Job/Read" in message
        assert message.endswith(DOCS_POINTER)

    def test_nothing_readable(self) -> None:
        """When no ancestor is readable the message says so."""
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": _response(404, ""),
                f"{BASE_URL}/job/A/api/json": _response(404, ""),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "no part of that path is readable" in message
        assert message.endswith(DOCS_POINTER)

    def test_single_segment_path(self) -> None:
        """A leaf-only path has no ancestor to probe and must not index-error."""
        session = _session({})

        message = diagnose_404(session, BASE_URL, "Executor")

        assert "no part of that path is readable" in message
        assert message.endswith(DOCS_POINTER)
        cast(Mock, session).get.assert_not_called()
