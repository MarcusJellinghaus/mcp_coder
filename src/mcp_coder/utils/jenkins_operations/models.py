"""Data models for Jenkins job operations.

This module provides dataclasses for representing Jenkins job status
and queue information.

Example:
    >>> status = JobStatus(
    ...     status="SUCCESS",
    ...     build_number=42,
    ...     duration_ms=1234,
    ...     url="https://jenkins.example.com/job/test/42"
    ... )
    >>> print(status)
    Job #42: SUCCESS (1234ms)

    >>> summary = QueueSummary(running=3, queued=2)
    >>> print(summary)
    3 jobs running, 2 jobs queued
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class JobStatus:
    """Represents the status of a Jenkins job.

    Attributes:
        status: Job state - "queued", "running", "SUCCESS", "FAILURE", "ABORTED", "UNSTABLE"
        build_number: Build number once job starts (None if still queued)
        duration_ms: Duration in milliseconds (None until job completes)
        url: Jenkins job URL from API (None if not available)

    Example:
        >>> # Queued job
        >>> status = JobStatus(status="queued", build_number=None, duration_ms=None, url=None)
        >>> print(status)
        Job queued

        >>> # Running job
        >>> status = JobStatus(
        ...     status="running",
        ...     build_number=42,
        ...     duration_ms=None,
        ...     url="https://jenkins.example.com/job/test/42"
        ... )
        >>> print(status)
        Job #42: running

        >>> # Completed job
        >>> status = JobStatus(
        ...     status="SUCCESS",
        ...     build_number=42,
        ...     duration_ms=1234,
        ...     url="https://jenkins.example.com/job/test/42"
        ... )
        >>> print(status)
        Job #42: SUCCESS (1234ms)
    """

    status: str
    build_number: Optional[int]
    duration_ms: Optional[int]
    url: Optional[str]

    def __str__(self) -> str:
        """Return human-readable job status.

        Returns:
            Formatted job status string.
        """
        if self.status == "queued":
            return "Job queued"

        if self.build_number is not None:
            result = f"Job #{self.build_number}: {self.status}"
            if self.duration_ms is not None:
                result += f" ({self.duration_ms}ms)"
            return result

        return self.status


@dataclass
class QueueSummary:
    """Summary of Jenkins queue status.

    Attributes:
        running: Number of jobs currently running
        queued: Number of jobs waiting in queue

    Example:
        >>> # Multiple jobs
        >>> summary = QueueSummary(running=3, queued=2)
        >>> print(summary)
        3 jobs running, 2 jobs queued

        >>> # Single job
        >>> summary = QueueSummary(running=1, queued=0)
        >>> print(summary)
        1 job running, 0 jobs queued

        >>> # Empty queue
        >>> summary = QueueSummary(running=0, queued=0)
        >>> print(summary)
        0 jobs running, 0 jobs queued
    """

    running: int
    queued: int

    def __str__(self) -> str:
        """Return human-readable queue summary.

        Returns:
            Formatted queue summary string.
        """
        running_text = f"{self.running} job{'s' if self.running != 1 else ''} running"
        queued_text = f"{self.queued} job{'s' if self.queued != 1 else ''} queued"
        return f"{running_text}, {queued_text}"
