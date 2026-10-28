"""Integration tests for Jenkins operations.

These tests verify JenkinsClient works with a real Jenkins server.
Tests are skipped if Jenkins is not configured.

Configuration:
    Environment Variables (highest priority):
        JENKINS_URL: Jenkins server URL with port
        JENKINS_USER: Jenkins username
        JENKINS_TOKEN: Jenkins API token
        JENKINS_TEST_JOB: Test job name (required)

    Config File (~/.mcp_coder/config.toml):
        [jenkins]
        server_url = "https://jenkins.example.com:8080"
        username = "jenkins-user"
        api_token = "your-api-token"
        test_job = "mcp-coder-test-job"

Note:
    Tests will be skipped if configuration is missing.
    The job lifecycle test does not wait for job completion. The started-build
    test waits up to POLL_TIMEOUT_S (120 s) for the build to finish.
"""

import time
import uuid

import pytest

from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES
from mcp_coder.utils.jenkins_operations.client import JenkinsClient, JenkinsError
from mcp_coder.utils.jenkins_operations.models import BuildInfo, JobStatus

POLL_INTERVAL_S = 2
POLL_TIMEOUT_S = 120


@pytest.mark.jenkins_integration
class TestJenkinsIntegration:
    """Integration tests for Jenkins operations with real server."""

    def test_job_lifecycle(
        self, jenkins_client: JenkinsClient, jenkins_test_setup: dict[str, str]
    ) -> None:
        """Verify job lifecycle operations work.

        This test verifies:
        1. Job can be started
        2. Queue ID is returned
        3. Job status can be retrieved
        4. Queue summary reflects the job

        Note: Does NOT wait for job completion.
        """
        test_job = jenkins_test_setup["test_job"]

        # Start job
        queue_id = jenkins_client.start_job(test_job)
        assert isinstance(queue_id, int), "Expected queue_id to be int"
        assert queue_id > 0, "Expected positive queue_id"
        print(f"\n[OK] Started job '{test_job}', queue_id={queue_id}")

        # Get job status (should be queued or running)
        status = jenkins_client.get_job_status(queue_id)
        assert isinstance(status, JobStatus), "Expected JobStatus instance"
        assert status.status in [
            "queued",
            "running",
            "SUCCESS",
            "FAILURE",
            "ABORTED",
            "UNSTABLE",
        ], f"Unexpected status: {status.status}"
        print(f"[OK] Job status: {status}")

    def test_get_recent_builds_returns_sorted_build_infos(
        self, jenkins_client: JenkinsClient
    ) -> None:
        """Recent builds are BuildInfo objects with valid statuses, newest first."""
        builds = jenkins_client.get_recent_builds(limit=5)

        assert len(builds) <= 5
        assert all(isinstance(b, BuildInfo) for b in builds)
        assert all(b.status in VALID_STATUSES for b in builds)
        timestamps = [b.timestamp for b in builds]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_started_build_appears_with_console_output(
        self, jenkins_client: JenkinsClient, jenkins_test_setup: dict[str, str]
    ) -> None:
        """A finished build is listed and its console output can be fetched."""
        test_job = jenkins_test_setup["test_job"]

        queue_id = jenkins_client.start_job(test_job)
        deadline = time.monotonic() + POLL_TIMEOUT_S
        status = jenkins_client.get_job_status(queue_id)
        while status.status in ("queued", "running"):
            if time.monotonic() > deadline:
                pytest.fail(
                    f"Build did not finish within {POLL_TIMEOUT_S}s; "
                    f"last status: {status}"
                )
            time.sleep(POLL_INTERVAL_S)
            status = jenkins_client.get_job_status(queue_id)

        parent = test_job.rpartition("/")[0] or None
        # Top level scans the whole server, so allow a wider window.
        limit = 100 if parent else 500
        match = next(
            (
                b
                for b in jenkins_client.get_recent_builds(limit=limit, path=parent)
                if b.job_path == test_job and b.number == status.build_number
            ),
            None,
        )

        assert match is not None, f"Build {status} not found in recent builds"
        assert match.status not in ("running", "unknown")
        assert jenkins_client.get_console_output(match.job_path, match.number).strip()

    def test_missing_folder_raises_jenkins_error(
        self, jenkins_client: JenkinsClient
    ) -> None:
        """Listing builds in a folder that does not exist raises JenkinsError."""
        with pytest.raises(JenkinsError):
            jenkins_client.get_recent_builds(
                path=f"mcp-coder-missing-{uuid.uuid4().hex}"
            )
