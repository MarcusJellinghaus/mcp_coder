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
from .diagnostics import diagnose_403, diagnose_404, extract_jenkins_error
from .models import JobStatus

# Setup logger
logger = logging.getLogger(__name__)

# The literal message python-jenkins builds in jenkins_request() for 401/403/500
# before it discards the response object.
_AUTH_FAIL_RE = re.compile(r"Possibly authentication failed \[(\d+)\]")


def _clean_jenkins_message(text: str) -> str:
    """Reduce a python-jenkins message to its first line plus any error sentence.

    python-jenkins appends the whole response body - typically a ~60-line
    Jenkins HTML error page - to its own one-line message. Only that first line
    and the single sentence buried in the page are worth showing.

    Args:
        text: The exception message, i.e. str(JenkinsException).

    Returns:
        The first line, with the extracted error sentence appended in quotes
        when the body yields one.
    """
    head, _sep, body = text.partition("\n")
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


def _get_jenkins_config() -> dict[str, str | None]:
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
        return str(self._client.server).rstrip("/")  # pylint: disable=protected-access

    @property
    def _http(self) -> Session:
        """python-jenkins' own requests session, with auth resolved on first access.

        Diagnostic probes must reuse this session rather than create their own:
        Jenkins.__init__ configures it with a retry adapter, honours
        PYTHONHTTPSVERIFY=0 and injects JENKINS_API_EXTRA_HEADERS. A probe on a
        fresh session inherits none of that and would misreport transport
        problems (self-signed cert, proxy header) as permission problems.

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
        self, exc: JenkinsException, context: str, job_path: Optional[str] = None
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

        Returns:
            JenkinsError carrying the context followed by the diagnosis.
        """
        # The raw page holds a live CSRF crumb and the username: DEBUG only, once.
        logger.debug("Raw Jenkins error for %s: %s", context, exc)

        try:
            if isinstance(exc, NotFoundException):
                detail = (
                    diagnose_404(self._http, self.base_url, job_path)
                    if job_path
                    else (
                        "404 - the queue item was not found (it may have expired) "
                        "or is not readable"
                    )
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
                    self._http,
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
                    base_url = self._client.server.rstrip("/")
                    job_url_part = url.replace(base_url, "").rstrip("/")
                    # Remove the build number suffix (e.g., "/123")
                    job_url_part = job_url_part.rsplit("/", 1)[0]
                    # Remove "/job/" prefixes to get the path format for get_build_info
                    # "/job/Folder/job/JobName" -> "Folder/JobName"
                    job_path = job_url_part.replace("/job/", "/").lstrip("/")
                else:
                    # Fallback to task name if URL not available or mocked
                    task_dict: dict[str, Any] = item.get("task", {})
                    job_path = task_dict.get("name", "")

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
            # No job_path is available here, so a 404 reports the queue item
            # rather than walking a path.
            raise self._wrap_jenkins_error(
                e, f"Failed to get status for queue_id {queue_id}"
            ) from None
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            # Wrap all exceptions as JenkinsError with context
            raise JenkinsError(
                f"Failed to get status for queue_id {queue_id}: {str(e)}"
            ) from e
