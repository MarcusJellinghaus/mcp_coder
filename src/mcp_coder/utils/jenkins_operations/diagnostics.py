r"""Jenkins permission diagnostics.

python-jenkins converts 401/403/500 responses into ``JenkinsException(msg +
"\n" + response.text)`` and 404 into ``NotFoundException``, discarding the
response object. That means neither the failing endpoint nor the response body
survives in a usable form: the endpoint is unrecoverable and the body arrives
as ~60 lines of HTML.

This module answers both questions after the fact, by issuing its own probe
requests on an injected ``requests.Session``:

- :func:`extract_jenkins_error` reduces a Jenkins error page to its one useful
  sentence.
- :func:`probe` performs a single introspection request that never raises.
- :func:`diagnose_403` / :func:`diagnose_404` return the complete
  operator-facing diagnosis - cause, remedy and the docs pointer. Callers only
  prefix their own context.

The session must be the one python-jenkins itself uses (see
``JenkinsClient._http``): a fresh session inherits neither the retry adapter
nor the TLS/header configuration, and would misreport transport problems as
permission problems.

Security:
    A Jenkins error page contains a live CSRF crumb and the username. Log only
    the extracted sentence, never the raw page above DEBUG.
"""

import html as html_lib
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

from requests import RequestException, Session

DOCS_POINTER = "See docs/repository-setup/jenkins.md"

# session.get() bypasses Jenkins._request, and the library's own timeout lives
# on the Jenkins object rather than on the session, so probes must pass one.
_PROBE_TIMEOUT = 10

# A diagnosis is a log line, not a document: cap whatever we extract.
_MAX_ERROR_LEN = 200

# The useful sentence sits in <p class="error">, but the observed page wraps it
# in an HTML comment and never closes the tag - so stop at whichever of </p>,
# a comment opener, a heading or the end of the body comes first.
_ERROR_PARAGRAPH_RE = re.compile(
    r"<p[^>]*class=[\"']?error[\"']?[^>]*>(.*?)(?:</p>|<!--|<h[1-6]|\Z)",
    re.DOTALL | re.IGNORECASE,
)
_HEADING_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class ProbeResult:
    """Outcome of a single probe request.

    Attributes:
        status: HTTP status code, or None if the request never completed
            (DNS, TLS, connection refused).
        url: Absolute URL that was probed.
        error_text: Extracted Jenkins error sentence, the transport error when
            status is None, or None when there is nothing to report.
    """

    status: Optional[int]
    url: str
    error_text: Optional[str]


def job_url_path(job_path: str) -> str:
    """Convert a Jenkins job path into the URL path Jenkins serves it under.

    Jenkins nests folders as ``/job/<name>`` segments, so
    "Tests/mcp-coder-test" becomes "/job/Tests/job/mcp-coder-test". Each
    segment is URL-encoded to handle spaces and special characters.

    Args:
        job_path: Slash-separated job path, e.g. "Tests/mcp-coder-test".
            Leading and trailing slashes are tolerated.

    Returns:
        The URL path only (no scheme or host), e.g.
        "/job/Tests/job/mcp-coder-test".
    """
    parts = [part for part in job_path.split("/") if part]
    return "/job/" + "/job/".join(quote(part, safe="") for part in parts)


def extract_jenkins_error(body: str) -> Optional[str]:
    """Reduce a Jenkins error page to its single error sentence.

    Deliberately tolerant: Jenkins error pages are not well-formed, and in the
    observed 403 page the sentence sits inside an HTML comment with no closing
    ``</p>``. When no marker is recognised the whole body is used, stripped and
    truncated, rather than returning nothing.

    Args:
        body: Raw response body, usually HTML.

    Returns:
        The error sentence with markup stripped, entities unescaped and
        whitespace collapsed, truncated to 200 characters plus "...". None if
        the body holds no text at all.
    """
    if not body.strip():
        return None

    match = _ERROR_PARAGRAPH_RE.search(body) or _HEADING_RE.search(body)
    raw = match.group(1) if match else body

    text = _TAG_RE.sub(" ", raw)
    text = html_lib.unescape(text)
    text = " ".join(text.split())

    if not text:
        return None
    if len(text) > _MAX_ERROR_LEN:
        return text[:_MAX_ERROR_LEN] + "..."
    return text


def probe(session: Session, base_url: str, path: str) -> ProbeResult:
    """Issue one introspection request, never raising.

    A failing probe must not mask the original error it exists to explain, so
    transport failures are returned as data.

    Args:
        session: python-jenkins' own session (see ``JenkinsClient._http``).
        base_url: Server URL without a trailing slash.
        path: URL path starting with "/".

    Returns:
        ProbeResult describing the outcome.
    """
    url = f"{base_url}{path}"
    try:
        response = session.get(url, timeout=_PROBE_TIMEOUT)
    except RequestException as exc:
        return ProbeResult(status=None, url=url, error_text=str(exc))

    error_text = None if response.ok else extract_jenkins_error(response.text)
    return ProbeResult(status=response.status_code, url=url, error_text=error_text)


def diagnose_403(
    session: Session, base_url: str, original_error: Optional[str] = None
) -> str:
    """Diagnose a 403 by probing the endpoints every REST call depends on.

    Probes ``/api/json`` and ``/crumbIssuer/api/json`` in order and reports the
    first one that rejects: a crumb-issuer rejection is invisible in the
    original exception, yet it is what actually fails when Overall/Read is
    missing.

    When both probes succeed the rejection was specific to the failing request
    (typically Job/Build on the executor job). The probes cannot reproduce it,
    so ``original_error`` - the sentence extracted from the failing response -
    is the only evidence naming the cause and is surfaced verbatim.

    Args:
        session: python-jenkins' own session (see ``JenkinsClient._http``).
        base_url: Server URL without a trailing slash.
        original_error: Error sentence already extracted from the body of the
            failure being diagnosed, if any.

    Returns:
        Complete operator-facing diagnosis including remedy and docs pointer.
    """
    for path in ("/api/json", "/crumbIssuer/api/json"):
        result = probe(session, base_url, path)
        detail = f' - "{result.error_text}"' if result.error_text else ""

        if result.status == 401:
            return (
                f"401 Unauthorized on {path}{detail}. Authentication failed - "
                f"check username and API token. {DOCS_POINTER}"
            )
        if result.status == 403:
            return (
                f"403 Forbidden on {path}{detail}. The API user is authenticated "
                "but not authorized; Jenkins requires Overall/Read for any REST "
                "call. Grant it in the global authorization matrix (it cannot be "
                f"granted per-job). {DOCS_POINTER}"
            )

    if original_error:
        return (
            f'403 Forbidden - "{original_error}". Overall/Read is granted (both '
            "/api/json and /crumbIssuer/api/json succeeded), so the missing "
            "permission is specific to the request that failed - typically "
            f"Job/Build on the executor job. {DOCS_POINTER}"
        )
    return (
        "403 Forbidden, but /api/json and /crumbIssuer/api/json both succeeded, "
        "and the response carried no error text. Overall/Read is granted; the "
        "missing permission is specific to the failing request - check Job/Build "
        f"on the executor job. {DOCS_POINTER}"
    )


def diagnose_404(session: Session, base_url: str, job_path: str) -> str:
    """Diagnose a 404 by finding the deepest readable ancestor of the job path.

    Naming that ancestor narrows the search to a single path segment. The
    wording stays deliberately non-committal: Jenkins hides unreadable jobs
    from their parent's listing, so a wrong name and a missing Job/Read are
    indistinguishable from outside.

    Args:
        session: python-jenkins' own session (see ``JenkinsClient._http``).
        base_url: Server URL without a trailing slash.
        job_path: Job path that returned 404, e.g. "Windows-Agents/Executor".

    Returns:
        Complete operator-facing diagnosis including remedy and docs pointer.
    """
    parts = [part for part in job_path.split("/") if part]

    # Skip the leaf - it already 404'd - and walk ancestors deepest-first.
    for depth in range(len(parts) - 1, 0, -1):
        ancestor = "/".join(parts[:depth])
        result = probe(session, base_url, job_url_path(ancestor) + "/api/json")
        if result.status == 200:
            return (
                f"404 on '{job_path}' - the folder '{ancestor}' is readable; "
                f"'{parts[depth]}' under it is not. Either the name is wrong or "
                f"the API user lacks Job/Read on it. Check both. {DOCS_POINTER}"
            )

    return (
        f"404 on '{job_path}' - no part of that path is readable. Either the path "
        "is wrong or the API user lacks Job/Read (and possibly Overall/Read). "
        f"Check both. {DOCS_POINTER}"
    )
