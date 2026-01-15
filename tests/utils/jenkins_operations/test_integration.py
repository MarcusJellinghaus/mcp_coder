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

import os
from typing import Generator

import pytest

from mcp_coder.utils.jenkins_operations.client import JenkinsClient
from mcp_coder.utils.jenkins_operations.models import JobStatus


@pytest.fixture
def jenkins_test_setup() -> Generator[dict[str, str], None, None]:
    """Provide Jenkins test configuration.

    Configuration sources (in priority order):
    1. Environment variables
    2. Config file
    3. Skip test if neither configured

    Yields:
        Dict with server_url, username, api_token, test_job

    Raises:
        pytest.skip: If required configuration missing
    """
    from mcp_coder.utils.user_config import get_config_value

    # Check environment variables first
    server_url = os.getenv("JENKINS_URL")
    username = os.getenv("JENKINS_USER")
    api_token = os.getenv("JENKINS_TOKEN")
    test_job = os.getenv("JENKINS_TEST_JOB")

    # Fall back to config file for missing values
    if not server_url:
        server_url = get_config_value("jenkins", "server_url")
    if not username:
        username = get_config_value("jenkins", "username")
    if not api_token:
        api_token = get_config_value("jenkins", "api_token")
    if not test_job:
        test_job = get_config_value("jenkins", "test_job")

    # Check required configuration and skip if missing
    if not server_url or not username or not api_token or not test_job:
        pytest.skip(
            "Jenkins not configured. Set JENKINS_URL, JENKINS_USER, JENKINS_TOKEN, JENKINS_TEST_JOB "
            "environment variables or configure in ~/.mcp_coder/config.toml [jenkins] section (including test_job)."
        )

    setup = {
        "server_url": server_url,
        "username": username,
        "api_token": api_token,
        "test_job": test_job,
    }
    yield setup


@pytest.fixture
def jenkins_client(jenkins_test_setup: dict[str, str]) -> JenkinsClient:
    """Create JenkinsClient instance for testing.

    Args:
        jenkins_test_setup: Jenkins configuration from fixture

    Returns:
        Configured JenkinsClient instance
    """
    return JenkinsClient(
        server_url=jenkins_test_setup["server_url"],
        username=jenkins_test_setup["username"],
        api_token=jenkins_test_setup["api_token"],
    )


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
