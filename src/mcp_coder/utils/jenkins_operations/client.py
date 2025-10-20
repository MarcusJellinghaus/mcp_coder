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

import os
from typing import Any, Optional, cast

import structlog
from jenkins import Jenkins

from mcp_coder.utils import get_config_value
from mcp_coder.utils.log_utils import log_function_call

from .models import JobStatus, QueueSummary

# Setup logger
logger = structlog.get_logger(__name__)


class JenkinsError(Exception):
    """Base exception for Jenkins operations.

    All Jenkins-related errors are wrapped in this exception type.
    This keeps error handling simple while providing clear context.

    The original exception is preserved via exception chaining for debugging.
    """

    pass


def _get_jenkins_config() -> dict[str, Optional[str]]:
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
    # Check environment variables first (priority)
    server_url = os.getenv("JENKINS_URL")
    username = os.getenv("JENKINS_USER")
    api_token = os.getenv("JENKINS_TOKEN")

    # Fall back to config file for missing values
    if server_url is None:
        server_url = get_config_value("jenkins", "server_url")

    if username is None:
        username = get_config_value("jenkins", "username")

    if api_token is None:
        api_token = get_config_value("jenkins", "api_token")

    return {
        "server_url": server_url,
        "username": username,
        "api_token": api_token,
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

    @log_function_call
    def start_job(self, job_path: str, params: Optional[dict[str, Any]] = None) -> int:
        """Start a Jenkins job and return queue ID.

        Args:
            job_path: Jenkins job path (e.g., "folder/job-name")
            params: Optional job parameters dict

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
            queue_id_result = self._client.build_job(job_path, parameters=params)
            # Cast to int as build_job returns the queue ID
            queue_id = cast(int, queue_id_result)
            logger.debug(
                "Job started successfully", job_path=job_path, queue_id=queue_id
            )
            return queue_id
        except Exception as e:
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
                # Extract job name from queue item for get_build_info call
                # The task dict has a 'name' field with the job name
                task_dict: dict[str, Any] = item.get("task", {})
                job_name = task_dict.get("name", "")

                build_info = self._client.get_build_info(job_name, build_number)

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

        except Exception as e:
            # Wrap all exceptions as JenkinsError with context
            raise JenkinsError(
                f"Failed to get status for queue_id {queue_id}: {str(e)}"
            ) from e

    @log_function_call
    def get_queue_summary(self) -> QueueSummary:
        """Get summary of Jenkins queue.

        Returns:
            QueueSummary with counts of running and queued jobs

        Raises:
            JenkinsError: For any Jenkins API errors
        """
        try:
            # Get queue info and running builds
            queue = self._client.get_queue_info()
            builds = self._client.get_running_builds()

            # Count queued and running jobs
            queued_count = len(queue)
            running_count = len(builds)

            return QueueSummary(running=running_count, queued=queued_count)

        except Exception as e:
            # Wrap all exceptions as JenkinsError with context
            raise JenkinsError(f"Failed to get queue summary: {str(e)}") from e
