"""Jenkins job automation utilities.

This package provides utilities for interacting with Jenkins servers
to start jobs, check status, and monitor the queue.

Main Components:
    JenkinsClient: Main client for Jenkins operations
    JobStatus: Dataclass for job status information
    QueueSummary: Dataclass for queue statistics
    JenkinsError: Exception for all Jenkins operations

Example:
    >>> from mcp_coder.utils import JenkinsClient, JobStatus
    >>> client = JenkinsClient("http://jenkins:8080", "user", "token")
    >>> queue_id = client.start_job("my-job", {"PARAM": "value"})
    >>> status = client.get_job_status(queue_id)
    >>> print(status)
    Job #42: running

Configuration:
    See client.py for configuration details.
"""

# Client and exception
from .client import JenkinsClient, JenkinsError

# Data models
from .models import JobStatus, QueueSummary

__all__ = [
    # Client
    "JenkinsClient",
    # Models
    "JobStatus",
    "QueueSummary",
    # Exception
    "JenkinsError",
]
