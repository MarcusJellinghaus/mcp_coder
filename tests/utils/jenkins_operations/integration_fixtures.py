"""Shared Jenkins integration-test fixtures.

Imported by the conftests that need them, not by the root conftest, so Jenkins
setup stays out of unrelated test directories.
"""

import os
from collections.abc import Generator
from typing import Any, cast

import pytest

from mcp_coder.utils.jenkins_operations.client import JenkinsClient


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
    from mcp_coder.utils.user_config import get_config_values

    # Check environment variables first
    server_url = os.getenv("JENKINS_URL")
    username = os.getenv("JENKINS_USER")
    api_token = os.getenv("JENKINS_TOKEN")
    test_job = os.getenv("JENKINS_TEST_JOB")

    # Get any missing values from config file in one batch
    missing_keys: list[tuple[str, str, str | None]] = []
    if not server_url:
        missing_keys.append(("jenkins", "server_url", None))
    if not username:
        missing_keys.append(("jenkins", "username", None))
    if not api_token:
        missing_keys.append(("jenkins", "api_token", None))
    if not test_job:
        missing_keys.append(("jenkins", "test_job", None))

    if missing_keys:
        config: dict[tuple[str, str], str | bool | int | list[Any] | None] = (
            get_config_values(missing_keys)
        )
        if not server_url:
            server_url = cast("str | None", config[("jenkins", "server_url")])
        if not username:
            username = cast("str | None", config[("jenkins", "username")])
        if not api_token:
            api_token = cast("str | None", config[("jenkins", "api_token")])
        if not test_job:
            test_job = cast("str | None", config[("jenkins", "test_job")])

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
