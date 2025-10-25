"""Coordinator CLI command implementation.

This module provides the coordinator test command for triggering
Jenkins-based integration tests for MCP Coder repositories.
"""

import argparse
import logging
import os
from typing import Optional

from ...utils.user_config import get_config_value

logger = logging.getLogger(__name__)


def load_repo_config(repo_name: str) -> Optional[dict[str, str]]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, test_job_path, github_credentials_id
        or None if repository not found in config
    """
    section = f"coordinator.repos.{repo_name}"

    repo_url = get_config_value(section, "repo_url")
    test_job_path = get_config_value(section, "test_job_path")
    github_credentials_id = get_config_value(section, "github_credentials_id")

    # Return dict only if all values present
    if repo_url and test_job_path and github_credentials_id:
        return {
            "repo_url": repo_url,
            "test_job_path": test_job_path,
            "github_credentials_id": github_credentials_id,
        }

    return None


def validate_repo_config(repo_name: str, config: Optional[dict[str, str]]) -> None:
    """Validate repository configuration has all required fields.

    Args:
        repo_name: Name of repository being validated
        config: Repository configuration dict or None

    Raises:
        ValueError: If config is None or missing required fields
    """
    if config is None:
        raise ValueError(
            f"Repository '{repo_name}' not found in config\n"
            f"Add it to config file under [coordinator.repos.{repo_name}]"
        )

    required_fields = ["repo_url", "test_job_path", "github_credentials_id"]
    for field in required_fields:
        if field not in config or not config[field]:
            raise ValueError(
                f"Repository '{repo_name}' missing required field '{field}'"
            )


def get_jenkins_credentials() -> tuple[str, str, str]:
    """Get Jenkins credentials from environment or config file.

    Priority: Environment variables > Config file

    Returns:
        Tuple of (server_url, username, api_token)

    Raises:
        ValueError: If any required credential is missing
    """
    # Priority: env vars > config file
    server_url = os.getenv("JENKINS_URL") or get_config_value("jenkins", "server_url")
    username = os.getenv("JENKINS_USER") or get_config_value("jenkins", "username")
    api_token = os.getenv("JENKINS_TOKEN") or get_config_value("jenkins", "api_token")

    # Check for missing credentials
    missing = []
    if not server_url:
        missing.append("server_url")
    if not username:
        missing.append("username")
    if not api_token:
        missing.append("api_token")

    if missing:
        raise ValueError(
            f"Jenkins configuration incomplete. Missing: {', '.join(missing)}\n"
            f"Set via environment variables (JENKINS_URL, JENKINS_USER, JENKINS_TOKEN) "
            f"or config file [jenkins] section"
        )

    # Type narrowing: if we reach here, all values are non-None
    assert server_url is not None
    assert username is not None
    assert api_token is not None

    return (server_url, username, api_token)


def format_job_output(job_path: str, queue_id: int, url: Optional[str]) -> str:
    """Format job trigger output message.

    Args:
        job_path: Jenkins job path
        queue_id: Queue ID from Jenkins
        url: Job URL if available (may be None if not started yet)

    Returns:
        Formatted output string
    """
    output = f"Job triggered: {job_path} - test - queue: {queue_id}"

    if url:
        output += f"\n{url}"
    else:
        # Construct fallback message when job URL not available yet
        output += "\n(Job URL will be available once build starts)"

    return output
