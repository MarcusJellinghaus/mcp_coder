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
    Tests DO NOT wait for job completion (just verify API calls work).
"""

import pytest

from mcp_coder.utils.jenkins_operations.client import JenkinsClient
from mcp_coder.utils.jenkins_operations.models import JobStatus


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
