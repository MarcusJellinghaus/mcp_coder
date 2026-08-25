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
    diagnose_build_404,
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

    @pytest.mark.parametrize("status", [500, 503])
    def test_server_error_probe_claims_no_permission_verdict(self, status: int) -> None:
        """A 5xx probe proves nothing about Overall/Read, so nothing is claimed.

        Regression guard for treating "neither 401 nor 403" as success: that
        reports "Overall/Read is granted" and points at Job/Build for a server
        that was never in a position to answer.
        """
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(status, ""),
                f"{BASE_URL}/crumbIssuer/api/json": _response(status, ""),
            }
        )

        message = diagnose_403(
            session, BASE_URL, original_error="job_manager is denied"
        )

        assert "could not be determined" in message
        assert f"returned HTTP {status}" in message
        assert "/api/json" in message
        assert "job_manager is denied" in message
        assert "Overall/Read is granted" not in message
        assert "Job/Build" not in message
        assert message.endswith(DOCS_POINTER)

    def test_server_error_body_is_reduced_to_a_sentence(self) -> None:
        """A 5xx page reaches the diagnosis as one sentence, never as markup.

        The whole point of the module is that a Jenkins error page is summarised
        rather than pasted, and the inconclusive branch is the one path where a
        non-200 body is quoted back to the operator.
        """
        body = (
            "<!DOCTYPE html><html><head><title>Error 500</title></head><body>"
            "<h1>HTTP ERROR 500 java.lang.NullPointerException</h1>"
            "<table><tr><th>URI:</th><td>/api/json</td></tr></table>"
            "</body></html>"
        )
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(500, body),
                f"{BASE_URL}/crumbIssuer/api/json": _response(500, body),
            }
        )

        message = diagnose_403(session, BASE_URL)

        assert (
            'returned HTTP 500 - "HTTP ERROR 500 java.lang.NullPointerException"'
            in message
        )
        assert "<" not in message
        assert "could not be determined" in message
        assert message.endswith(DOCS_POINTER)

    def test_transport_failure_claims_no_permission_verdict(self) -> None:
        """A probe that never completed is reported as such, not as success."""
        session = _session(
            {
                f"{BASE_URL}/api/json": RequestException("connection refused"),
                f"{BASE_URL}/crumbIssuer/api/json": RequestException(
                    "connection refused"
                ),
            }
        )

        message = diagnose_403(session, BASE_URL)

        assert "could not be determined" in message
        assert "did not complete" in message
        assert "connection refused" in message
        assert "Overall/Read is granted" not in message
        assert "Job/Build" not in message
        assert message.endswith(DOCS_POINTER)

    def test_crumb_issuer_failure_claims_no_permission_verdict(self) -> None:
        """A healthy /api/json does not license a verdict when the crumb probe fails."""
        session = _session(
            {
                f"{BASE_URL}/api/json": _response(200, "{}"),
                f"{BASE_URL}/crumbIssuer/api/json": RequestException("timed out"),
            }
        )

        message = diagnose_403(session, BASE_URL)

        assert "could not be determined" in message
        assert "/crumbIssuer/api/json" in message
        assert "both succeeded" not in message
        assert "Job/Build" not in message


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

    @pytest.mark.parametrize("status", [401, 403, 404])
    def test_nothing_readable(self, status: int) -> None:
        """When every ancestor was reached and refused the message says so.

        401/403/404 are all answers: Jenkins reached a verdict, so concluding
        that nothing in the path is readable is backed by evidence.
        """
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": _response(status, ""),
                f"{BASE_URL}/job/A/api/json": _response(status, ""),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "no folder in that path is readable" in message
        assert message.endswith(DOCS_POINTER)

    @pytest.mark.parametrize("status", [500, 503])
    def test_server_error_ancestor_is_undetermined_not_unreadable(
        self, status: int
    ) -> None:
        """A 5xx is not a permission verdict, so none may be reported.

        Regression guard for inferring "unreadable" from "not 200": a Jenkins
        restart would otherwise send the operator into the authorization
        matrix for a server that was simply down.
        """
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": _response(status, ""),
                f"{BASE_URL}/job/A/api/json": _response(status, ""),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "could not be determined" in message
        assert f"returned HTTP {status}" in message
        # The deepest unreached ancestor is the one worth naming: it is the
        # narrowest thing the walk failed to establish.
        assert "the probe of 'A/B'" in message
        assert "the probe of 'A'" not in message
        assert "no folder in that path is readable" not in message
        assert "lacks Job/Read" not in message
        assert message.endswith(DOCS_POINTER)

    @pytest.mark.parametrize("status", [401, 403, 404])
    def test_readable_ancestor_names_a_denied_segment(self, status: int) -> None:
        """A definite answer on both sides narrows the search to one segment."""
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": _response(status, ""),
                f"{BASE_URL}/job/A/api/json": _response(200, "{}"),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "the folder 'A' is readable; 'B' under it is not" in message
        assert "lacks Job/Read" in message
        assert "could not be determined" not in message

    @pytest.mark.parametrize("status", [500, 503])
    def test_readable_ancestor_does_not_blame_an_unreached_segment(
        self, status: int
    ) -> None:
        """A 5xx on 'A/B' is no evidence that 'B' is unreadable.

        Regression guard for returning as soon as any ancestor answers 200: 'A'
        answering says nothing about 'B', whose own probe never reached a
        verdict, yet the operator would be sent to grant Job/Read on it.
        """
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": _response(status, ""),
                f"{BASE_URL}/job/A/api/json": _response(200, "{}"),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "the folder 'A' is readable" in message
        assert "could not be determined" in message
        assert "the probe of 'A/B'" in message
        assert f"returned HTTP {status}" in message
        assert "under it is not" not in message
        assert "lacks Job/Read" not in message
        assert message.endswith(DOCS_POINTER)

    def test_readable_ancestor_does_not_blame_an_unreachable_segment(self) -> None:
        """A transport failure on 'A/B' is likewise no verdict on 'B'."""
        session = _session(
            {
                f"{BASE_URL}/job/A/job/B/api/json": RequestException(
                    "connection refused"
                ),
                f"{BASE_URL}/job/A/api/json": _response(200, "{}"),
            }
        )

        message = diagnose_404(session, BASE_URL, "A/B/C")

        assert "the folder 'A' is readable" in message
        assert "could not be determined" in message
        assert "did not complete" in message
        assert "connection refused" in message
        assert "lacks Job/Read" not in message

    def test_single_segment_path_claims_only_what_was_probed(self) -> None:
        """A leaf-only path has no ancestor, so nothing may be claimed about one.

        Regression guard: asserting "no part of that path is readable" here
        would be a diagnosis with zero evidence behind it - no probe ran - and
        an unreadable-root claim is exactly the kind of confidently wrong
        message this module exists to replace.
        """
        session = _session({})

        message = diagnose_404(session, BASE_URL, "Executor")

        assert "top-level job" in message
        assert "readable" not in message
        assert "Job/Read" in message
        assert "Check both" in message
        assert message.endswith(DOCS_POINTER)
        cast(Mock, session).get.assert_not_called()


class TestDiagnoseBuild404:
    """Tests for diagnose_build_404."""

    def test_readable_job_blames_the_build_record(self) -> None:
        """The job answers, so Job/Read is granted and only the build is gone."""
        session = _session(
            {
                f"{BASE_URL}/job/Windows-Agents/job/Executor/api/json": _response(
                    200, "{}"
                )
            }
        )

        message = diagnose_build_404(session, BASE_URL, "Windows-Agents/Executor", 42)

        assert "build #42" in message
        assert "Windows-Agents/Executor" in message
        assert "log rotation" in message
        # A permission remedy here would be the wrong turn.
        assert "Job/Read" not in message
        assert DOCS_POINTER not in message

    def test_unreadable_job_delegates_to_the_ancestor_walk(self) -> None:
        """When the job itself 404s the build number explains nothing."""
        session = _session(
            {
                f"{BASE_URL}/job/Windows-Agents/job/Executor/api/json": _response(404),
                f"{BASE_URL}/job/Windows-Agents/api/json": _response(200, "{}"),
            }
        )

        message = diagnose_build_404(session, BASE_URL, "Windows-Agents/Executor", 42)

        assert "'Windows-Agents'" in message
        assert "'Executor'" in message
        assert "Job/Read" in message
        assert "build #42" not in message
        assert message.endswith(DOCS_POINTER)

    def test_transport_failure_falls_back_to_the_job_diagnosis(self) -> None:
        """A probe that never completed must not be read as a readable job.

        Nor as an unreadable one: with both requests refused, nothing at all
        was established about the path, so the message must say the probes did
        not complete rather than blame Job/Read.
        """
        session = _session(
            {
                f"{BASE_URL}/job/Windows-Agents/job/Executor/api/json": RequestException(
                    "connection refused"
                ),
                f"{BASE_URL}/job/Windows-Agents/api/json": RequestException(
                    "connection refused"
                ),
            }
        )

        message = diagnose_build_404(session, BASE_URL, "Windows-Agents/Executor", 42)

        assert "could not be determined" in message
        assert "did not complete" in message
        assert "connection refused" in message
        assert "no folder in that path is readable" not in message
        assert "lacks Job/Read" not in message
        assert "build #42" not in message
