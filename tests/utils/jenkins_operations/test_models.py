"""Tests for Jenkins operation models."""

import pytest

from mcp_coder.utils.jenkins_operations.models import JobStatus, QueueSummary


class TestJobStatus:
    """Tests for JobStatus dataclass."""

    def test_job_status_creation(self) -> None:
        """Test JobStatus creation with all fields."""
        status = JobStatus(
            status="SUCCESS",
            build_number=42,
            duration_ms=1234,
            url="https://jenkins.example.com/job/test/42",
        )

        assert status.status == "SUCCESS"
        assert status.build_number == 42
        assert status.duration_ms == 1234
        assert status.url == "https://jenkins.example.com/job/test/42"

    def test_job_status_creation_with_none_fields(self) -> None:
        """Test JobStatus creation with Optional fields as None."""
        status = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        assert status.status == "queued"
        assert status.build_number is None
        assert status.duration_ms is None
        assert status.url is None

    def test_job_status_str_queued(self) -> None:
        """Test __str__() for queued job."""
        status = JobStatus(
            status="queued",
            build_number=None,
            duration_ms=None,
            url=None,
        )

        assert str(status) == "Job queued"

    def test_job_status_str_running(self) -> None:
        """Test __str__() for running job."""
        status = JobStatus(
            status="running",
            build_number=42,
            duration_ms=None,
            url="https://jenkins.example.com/job/test/42",
        )

        assert str(status) == "Job #42: running"

    def test_job_status_str_completed(self) -> None:
        """Test __str__() for completed job."""
        status = JobStatus(
            status="SUCCESS",
            build_number=42,
            duration_ms=1234,
            url="https://jenkins.example.com/job/test/42",
        )

        assert str(status) == "Job #42: SUCCESS (1234ms)"


class TestQueueSummary:
    """Tests for QueueSummary dataclass."""

    def test_queue_summary_creation(self) -> None:
        """Test QueueSummary creation."""
        summary = QueueSummary(running=3, queued=2)

        assert summary.running == 3
        assert summary.queued == 2

    def test_queue_summary_str_multiple(self) -> None:
        """Test __str__() with multiple jobs."""
        summary = QueueSummary(running=3, queued=2)

        assert str(summary) == "3 jobs running, 2 jobs queued"

    def test_queue_summary_str_singular(self) -> None:
        """Test __str__() with single job."""
        summary = QueueSummary(running=1, queued=0)

        assert str(summary) == "1 job running, 0 jobs queued"

    def test_queue_summary_str_empty(self) -> None:
        """Test __str__() with zero jobs."""
        summary = QueueSummary(running=0, queued=0)

        assert str(summary) == "0 jobs running, 0 jobs queued"
