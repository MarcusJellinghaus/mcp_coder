"""Jenkins job automation client.

This module provides the JenkinsClient class for interacting with Jenkins
to start jobs, check status, and monitor the queue.

Configuration:
    ~/.mcp_coder/config.toml:
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "jenkins-user"
        api_token = "your-api-token"

    Environment Variables (override config):
        JENKINS_URL, JENKINS_USER, JENKINS_TOKEN

Limitations:
    - All errors wrapped as JenkinsError (check error message for details)
    - Queue items may expire if queried long after job completion

Example:
    >>> from mcp_coder.utils.jenkins_operations import JenkinsClient
    >>> client = JenkinsClient("http://jenkins:8080", "user", "token")
    >>> queue_id = client.start_job("my-job", {"PARAM": "value"})
    >>> status = client.get_job_status(queue_id)
    >>> print(status)
    Job #42: SUCCESS (1234ms)
"""

import logging
import re
from typing import Any, Optional, cast

from jenkins import Jenkins, JenkinsException, NotFoundException
from requests import Session
from requests.exceptions import HTTPError

from ..log_utils import log_function_call
from ..user_config import get_config_values
from .diagnostics import (
    diagnose_403,
    diagnose_404,
    diagnose_build_404,
    extract_jenkins_error,
)
from .models import JobStatus

# Setup logger
logger = logging.getLogger(__name__)

# The literal message python-jenkins builds in jenkins_request() for 401/403/500
# before it discards the response object: it captures the status and the reason
# but labels all three "Possibly authentication failed".
_AUTH_FAIL_RE = re.compile(r"Possibly authentication failed \[(\d+)\](?::[ \t]*(.*))?")


def _clean_jenkins_message(text: str) -> str:
    """Reduce a python-jenkins message to one accurate line plus any error sentence.

    Two things need removing. python-jenkins appends the whole response body -
    typically a ~60-line Jenkins HTML error page - to its own one-line message,
    and that message guesses "Possibly authentication failed" for every one of
    401, 403 and 500. The guess is wrong for all three: 403 is authorization
    and 500 is a server fault. Keep the status and the reason, drop the guess.

    Args:
        text: The exception message, i.e. str(JenkinsException).

    Returns:
        A single line - "<status> <reason>" for the messages python-jenkins
        builds from a response, the original first line otherwise - with the
        error sentence extracted from the body appended in quotes when there
        is one.
    """
    head, _sep, body = text.partition("\n")
    if match := _AUTH_FAIL_RE.search(head):
        reason = (match.group(2) or "").strip()
        head = f"{match.group(1)} {reason}".strip()
    extracted = extract_jenkins_error(body) if body else None
    return f'{head} - "{extracted}"' if extracted else head


def _http_error_hint(status_code: int) -> str:
    """Return a human-readable hint for known HTTP status codes.

    Args:
        status_code: HTTP status code from the response.

    Returns:
        Hint string with leading space and parens, or empty string if unknown.
    """
    hints = {409: " (job may be disabled, already queued, or running)"}
    return hints.get(status_code, "")


class JenkinsError(Exception):
    """Base exception for Jenkins operations.

    All Jenkins-related errors are wrapped in this exception type.
    This keeps error handling simple while providing clear context.

    The original exception is preserved via exception chaining for debugging.
    """


def get_jenkins_config() -> dict[str, str | None]:
    """Get Jenkins configuration from environment or config file.

    Priority: Environment variables > Config file > None

    Environment Variables:
        JENKINS_URL: Jenkins server URL with port
        JENKINS_USER: Jenkins username
        JENKINS_TOKEN: Jenkins API token

    Config File (~/.mcp_coder/config.toml):
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "user"
        api_token = "token"

    Returns:
        Dict with keys: server_url, username, api_token
        Values are None if not configured

    Note:
        test_job is NOT included here - it's only for integration tests
        and is handled separately in the test fixture.
    """
    # get_config_values automatically checks environment variables first
    config = get_config_values(
        [
            ("jenkins", "server_url", None),
            ("jenkins", "username", None),
            ("jenkins", "api_token", None),
        ]
    )

    return {
        "server_url": (
            config[("jenkins", "server_url")]
            if isinstance(config[("jenkins", "server_url")], str)
            else None
        ),
        "username": (
            config[("jenkins", "username")]
            if isinstance(config[("jenkins", "username")], str)
            else None
        ),
        "api_token": (
            config[("jenkins", "api_token")]
            if isinstance(config[("jenkins", "api_token")], str)
            else None
        ),
    }


class JenkinsClient:
    """Jenkins job automation client.

    Provides methods to start jobs, check status, and monitor queue.
    Uses python-jenkins library for API communication.
    """

    def __init__(self, server_url: str, username: str, api_token: str) -> None:
        """Initialize Jenkins client with credentials.

        Timeout: Fixed 30 seconds for all operations (not configurable).

        Args:
            server_url: Jenkins server URL (e.g., "http://jenkins:8080")
            username: Jenkins username
            api_token: Jenkins API token

        Raises:
            ValueError: If any required parameter is None or empty
        """
        # Validate required parameters
        if not server_url or (isinstance(server_url, str) and not server_url.strip()):
            raise ValueError("server_url is required")

        if not username or (isinstance(username, str) and not username.strip()):
            raise ValueError("username is required")

        if not api_token or (isinstance(api_token, str) and not api_token.strip()):
            raise ValueError("api_token is required")

        # Create Jenkins client with fixed 30-second timeout
        self._client = Jenkins(
            server_url, username=username, password=api_token, timeout=30
        )

    @property
    def base_url(self) -> str:
        """Jenkins server URL with no trailing slash.

        python-jenkins has no public accessor for the server URL, and always
        appends a trailing slash to whatever was configured.

        Returns:
            Server URL without a trailing slash, e.g. "http://jenkins:8080".
        """
        return str(self._client.server).rstrip("/")

    @property
    def probe_session(self) -> Session:
        """python-jenkins' own requests session, with auth resolved on first access.

        Diagnostic probes must reuse this session rather than create their own:
        Jenkins.__init__ configures it with a retry adapter, honours
        PYTHONHTTPSVERIFY=0 and injects JENKINS_API_EXTRA_HEADERS. A probe on a
        fresh session inherits none of that and would misreport transport
        problems (self-signed cert, proxy header) as permission problems.

        This is the public probe seam: it is the one place that reaches into
        python-jenkins' internals, so callers (``_wrap_jenkins_error``,
        ``cli.commands.verify_jenkins``) need no protected access of their own.

        Returns:
            The library's session, authenticated where possible.
        """
        # pylint: disable=protected-access
        # python-jenkins resolves auth lazily inside _maybe_add_auth() on the first
        # request. Diagnostic probes reuse this session directly and would otherwise
        # go out anonymous and misreport a false 401/403, so resolve it here instead.
        # _auths[0] is the basic-auth entry when username and password are supplied
        # (kerberos, when installed, is appended at index 1) and both are validated
        # non-empty in __init__. Reading it here rather than calling _maybe_add_auth()
        # also avoids the live GET /api/json that method issues when
        # requests_kerberos is installed.
        session: Session = self._client._session
        if session.auth is None:
            auths = getattr(self._client, "_auths", None)
            try:
                session.auth = auths[0][1]  # type: ignore[index]
            except (TypeError, IndexError, KeyError):
                # Unexpected python-jenkins internals: probe unauthenticated rather
                # than turning a diagnostic into a crash.
                logger.debug("Could not resolve python-jenkins session auth")
        return session

    def _wrap_jenkins_error(
        self,
        exc: JenkinsException,
        context: str,
        job_path: Optional[str] = None,
        build_number: Optional[int] = None,
    ) -> JenkinsError:
        """Compose a clean, diagnosed JenkinsError for a python-jenkins failure.

        Returns the exception instead of raising it, so that ``from None`` stays
        visible at the raise site: breaking the chain is what keeps the raw
        Jenkins HTML page out of the traceback.

        Args:
            exc: The exception python-jenkins raised.
            context: Call-context prefix, e.g. "Failed to start job 'x'".
            job_path: Job path involved, when there is one. Enables the 404
                ancestor walk; omitted for queue-item lookups.
            build_number: Build being fetched, when the failing call was a build
                lookup rather than a job lookup. A build 404 has a second
                explanation - a discarded build record - that a job 404 does not.

        Returns:
            JenkinsError carrying the context followed by the diagnosis.
        """
        # The raw page holds a live CSRF crumb and the username: DEBUG only, once.
        logger.debug("Raw Jenkins error for %s: %s", context, exc)

        try:
            if isinstance(exc, NotFoundException):
                if job_path and build_number is not None:
                    detail = diagnose_build_404(
                        self.probe_session, self.base_url, job_path, build_number
                    )
                elif job_path:
                    detail = diagnose_404(self.probe_session, self.base_url, job_path)
                else:
                    detail = (
                        "404 - the queue item was not found (it may have expired) "
                        "or is not readable"
                    )
            elif (match := _AUTH_FAIL_RE.search(str(exc))) and match.group(1) in (
                "401",
                "403",
            ):
                # Pass on the sentence python-jenkins appended: when every probe
                # succeeds (e.g. Job/Build missing on the executor) it is the only
                # evidence naming the cause, and diagnose_403 must not discard it.
                _head, _sep, body = str(exc).partition("\n")
                detail = diagnose_403(
                    self.probe_session,
                    self.base_url,
                    extract_jenkins_error(body) if body else None,
                )
            else:
                # 500 and everything else: no permission question to answer.
                detail = _clean_jenkins_message(str(exc))
        except Exception:  # pylint: disable=broad-exception-caught
            # A diagnostic must never replace a real error with its own stack trace.
            logger.debug("Jenkins diagnosis failed", exc_info=True)
            detail = _clean_jenkins_message(str(exc))

        return JenkinsError(f"{context}: {detail}")

    @log_function_call
    def start_job(
        self,
        job_path: str,
        params: Optional[dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> int:
        """Start a Jenkins job and return queue ID.

        Args:
            job_path: Jenkins job path (e.g., "folder/job-name")
            params: Optional job parameters dict
            token: Optional per-job build authentication token
                   (configured in Jenkins job under "Trigger builds remotely")

        Returns:
            Queue ID for tracking the job

        Raises:
            ValueError: If params is not None and not a dict
            JenkinsError: For any Jenkins API errors
        """
        # Validate params type
        if params is not None and not isinstance(params, dict):
            raise ValueError("params must be a dict")

        # Default params to empty dict
        if params is None:
            params = {}

        try:
            # Start the job and get queue ID
            # Pass token to build_job - it will append it to the URL if provided
            queue_id_result = self._client.build_job(
                job_path, parameters=params, token=token
            )
            # Cast to int as build_job returns the queue ID
            queue_id = cast(int, queue_id_result)
            logger.debug(
                "Job started successfully",
                extra={"job_path": job_path, "queue_id": queue_id},
            )
            return queue_id
        except JenkinsException as e:
            # python-jenkins converts 401/403/404/500 into its own exception types
            # before they can surface as HTTPError, so this branch must come first.
            raise self._wrap_jenkins_error(
                e, f"Failed to start job '{job_path}'", job_path
            ) from None
        except HTTPError as e:
            # HTTP errors: build a clean message without the full URL
            if e.response is not None:
                code = e.response.status_code
                reason = e.response.reason
                hint = _http_error_hint(code)
                msg = f"Failed to start job '{job_path}': {code} {reason}{hint}"
            else:
                msg = f"Failed to start job '{job_path}': {str(e)}"
            raise JenkinsError(msg) from e
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            # Wrap all exceptions as JenkinsError with context
            raise JenkinsError(f"Failed to start job '{job_path}': {str(e)}") from e

    @log_function_call
    def get_job_status(self, queue_id: int) -> JobStatus:
        """Get job status by queue ID.

        Args:
            queue_id: Queue ID returned from start_job()

        Returns:
            JobStatus dataclass with current status information

        Raises:
            JenkinsError: For any Jenkins API errors
        """
        # Which lookup is in flight, so a 404 can name the right thing. None
        # until the build is known: up to that point only the queue item can 404.
        build_lookup: Optional[tuple[str, int]] = None
        try:
            # Get queue item information
            item = self._client.get_queue_item(queue_id)

            # Check if job has started (has executable)
            if item.get("executable"):
                executable = item["executable"]
                build_number = executable["number"]
                url = executable.get("url")

                # Get build info for status and duration
                # Extract full job path from the URL in the executable dict
                # The URL format is: http://server/job/Folder/job/JobName/BUILD_NUMBER/
                # We need to extract "Folder/JobName" from this URL
                if (
                    url
                    and isinstance(url, str)
                    and isinstance(self._client.server, str)
                ):
                    # Parse the job path from URL by removing base URL and build number
                    # Example: "http://server/job/Folder/job/JobName/123/" -> "Folder/JobName"
                    job_url_part = url.replace(self.base_url, "").rstrip("/")
                    # Remove the build number suffix (e.g., "/123")
                    job_url_part = job_url_part.rsplit("/", 1)[0]
                    # Remove "/job/" prefixes to get the path format for get_build_info
                    # "/job/Folder/job/JobName" -> "Folder/JobName"
                    job_path = job_url_part.replace("/job/", "/").lstrip("/")
                else:
                    # Fallback to task name if URL not available or mocked
                    task_dict: dict[str, Any] = item.get("task", {})
                    job_path = task_dict.get("name", "")

                build_lookup = (job_path, build_number)
                build_info = self._client.get_build_info(job_path, build_number)

                result = build_info.get("result")
                duration = build_info.get("duration")

                # Determine status
                if result is None:
                    # Job is still running
                    status = "running"
                    duration_ms = None
                else:
                    # Job completed with result (SUCCESS, FAILURE, ABORTED, etc.)
                    status = result
                    duration_ms = duration if duration != 0 else None

                return JobStatus(
                    status=status,
                    build_number=build_number,
                    duration_ms=duration_ms,
                    url=url,
                )
            else:
                # Job is still queued
                return JobStatus(
                    status="queued",
                    build_number=None,
                    duration_ms=None,
                    url=None,
                )

        except JenkinsException as e:
            # Before the build is known there is no path to walk, so a 404 can
            # only be the queue item; afterwards it is the build lookup, which
            # has its own diagnosis.
            raise self._wrap_jenkins_error(
                e,
                f"Failed to get status for queue_id {queue_id}",
                job_path=build_lookup[0] if build_lookup else None,
                build_number=build_lookup[1] if build_lookup else None,
            ) from None
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            # Wrap all exceptions as JenkinsError with context
            raise JenkinsError(
                f"Failed to get status for queue_id {queue_id}: {str(e)}"
            ) from e
