"""Coordinator CLI command implementation.

This module provides the coordinator test command for triggering
Jenkins-based integration tests for MCP Coder repositories.
"""

import argparse
import logging
import os
import sys
from typing import Optional

from workflows.label_config import load_labels_config

from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.jenkins_operations.client import JenkinsClient
from ...utils.jenkins_operations.models import JobStatus
from ...utils.user_config import (
    create_default_config,
    get_config_file_path,
    get_config_value,
)

logger = logging.getLogger(__name__)


# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-code-checker && mcp-code-checker --help
which mcp-server-filesystem && mcp-server-filesystem --help
mcp-coder verify
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
uv sync --extra dev
# Claude CLI verification
which claude
claude mcp list
claude -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level debug prompt "What is 1 + 1?"
# Project environment verification
source .venv/bin/activate
which mcp-coder && mcp-coder --version
"""


# Priority order for processing issues (highest to lowest)
PRIORITY_ORDER = [
    "status-08:ready-pr",
    "status-05:plan-ready",
    "status-02:awaiting-planning",
]


# Workflow configuration mapping
WORKFLOW_MAPPING = {
    "status-02:awaiting-planning": {
        "workflow": "create-plan",
        "branch_strategy": "main",
        "next_label": "status-03:planning",
    },
    "status-05:plan-ready": {
        "workflow": "implement",
        "branch_strategy": "from_issue",
        "next_label": "status-06:implementing",
    },
    "status-08:ready-pr": {
        "workflow": "create-pr",
        "branch_strategy": "from_issue",
        "next_label": "status-09:pr-creating",
    },
}


# Workflow command templates
CREATE_PLAN_COMMAND_TEMPLATE = """git checkout main
git pull
which mcp-coder && mcp-coder --version
which claude && claude --version
uv sync --extra dev
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo
"""


def get_eligible_issues(
    issue_manager: IssueManager, log_level: str = "INFO"
) -> list[IssueData]:
    """Get issues ready for automation, sorted by priority.

    Args:
        issue_manager: IssueManager instance for GitHub API calls
        log_level: Logging level for debug output

    Returns:
        List of IssueData sorted by priority:
        1. status-08:ready-pr (highest priority)
        2. status-05:plan-ready
        3. status-02:awaiting-planning (lowest priority)

    Raises:
        GithubException: If GitHub API errors occur
    """
    # Load label configuration
    # Get project_dir from issue_manager (inherited from BaseGitHubManager)
    if issue_manager.project_dir is None:
        raise ValueError("IssueManager must be initialized with project_dir")

    config_path = issue_manager.project_dir / "workflows" / "config" / "labels.json"
    labels_config = load_labels_config(config_path)

    # Extract bot_pickup labels (labels with category="bot_pickup")
    bot_pickup_labels = set()
    for label in labels_config["workflow_labels"]:
        if label["category"] == "bot_pickup":
            bot_pickup_labels.add(label["name"])

    # Extract ignore_labels set for filtering
    ignore_labels_set = set(labels_config.get("ignore_labels", []))

    # Query all open issues (exclude pull requests)
    all_issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    logger.debug(f"Found {len(all_issues)} open issues")

    # Filter issues
    eligible_issues = []
    for issue in all_issues:
        issue_labels = set(issue["labels"])

        # Count bot_pickup labels on this issue
        bot_pickup_count = len(issue_labels & bot_pickup_labels)

        # Skip if not exactly one bot_pickup label
        if bot_pickup_count != 1:
            continue

        # Skip if has any ignore_labels
        if issue_labels & ignore_labels_set:
            continue

        # Issue is eligible
        eligible_issues.append(issue)

    logger.debug(f"Filtered to {len(eligible_issues)} eligible issues")

    # Sort by priority
    priority_map = {label: i for i, label in enumerate(PRIORITY_ORDER)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        # Should not happen if filtering worked correctly
        return len(PRIORITY_ORDER)  # Lowest priority

    eligible_issues.sort(key=get_priority)

    return eligible_issues


def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, executor_test_path, github_credentials_id
        Values may be None if not found in config
    """
    section = f"coordinator.repos.{repo_name}"

    repo_url = get_config_value(section, "repo_url")
    executor_test_path = get_config_value(section, "executor_test_path")
    github_credentials_id = get_config_value(section, "github_credentials_id")

    # Always return dict with field values (may be None)
    return {
        "repo_url": repo_url,
        "executor_test_path": executor_test_path,
        "github_credentials_id": github_credentials_id,
    }


def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None:
    """Validate repository configuration has all required fields.

    Args:
        repo_name: Name of repository being validated
        config: Repository configuration dict with possibly None values

    Raises:
        ValueError: If any required fields are missing with detailed error message
    """
    required_fields = ["repo_url", "executor_test_path", "github_credentials_id"]
    missing_fields = []

    for field in required_fields:
        if field not in config or not config[field]:
            missing_fields.append(field)

    if missing_fields:
        config_path = get_config_file_path()
        section_name = f"coordinator.repos.{repo_name}"

        # Build concise one-line error message for each missing field
        if len(missing_fields) == 1:
            field = missing_fields[0]
            error_msg = (
                f"Config file: {config_path} - "
                f"section [{section_name}] - "
                f"value for field '{field}' missing"
            )
        else:
            # Multiple missing fields
            fields_str = "', '".join(missing_fields)
            error_msg = (
                f"Config file: {config_path} - "
                f"section [{section_name}] - "
                f"values for fields '{fields_str}' missing"
            )

        raise ValueError(error_msg)


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


def execute_coordinator_test(args: argparse.Namespace) -> int:
    """Execute coordinator test command.

    Args:
        args: Parsed command line arguments with:
            - repo_name: Repository name to test
            - branch_name: Git branch to test

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Auto-create config on first run
        created = create_default_config()
        if created:
            config_path = get_config_file_path()
            logger.info(
                "Created default config file. Please update with your credentials."
            )
            print(f"Created default config file at {config_path}")
            print("Please update it with your Jenkins and repository information.")
            return 1  # Exit to let user configure

        # Load and validate repository config
        repo_config = load_repo_config(args.repo_name)
        validate_repo_config(args.repo_name, repo_config)

        # Type narrowing: validate_repo_config raises if any fields are None
        # After validation, we can safely cast to non-optional dict
        validated_config: dict[str, str] = {
            "repo_url": repo_config["repo_url"],  # type: ignore[dict-item]
            "executor_test_path": repo_config["executor_test_path"],  # type: ignore[dict-item]
            "github_credentials_id": repo_config["github_credentials_id"],  # type: ignore[dict-item]
        }

        # Get Jenkins credentials
        server_url, username, api_token = get_jenkins_credentials()

        # Create Jenkins client
        client = JenkinsClient(server_url, username, api_token)

        # Build job parameters
        params = {
            "REPO_URL": validated_config["repo_url"],
            "BRANCH_NAME": args.branch_name,
            "COMMAND": DEFAULT_TEST_COMMAND,
            "GITHUB_CREDENTIALS_ID": validated_config["github_credentials_id"],
        }

        # Start job (API token in Basic Auth bypasses CSRF)
        queue_id = client.start_job(validated_config["executor_test_path"], params)

        # Try to get job URL (may not be available immediately)
        try:
            status = client.get_job_status(queue_id)
            job_url = status.url
        except Exception as e:
            logger.debug(f"Could not get job status: {e}")
            job_url = None

        # Format and print output
        output = format_job_output(
            validated_config["executor_test_path"], queue_id, job_url
        )
        print(output)

        return 0

    except ValueError as e:
        # User-facing errors (config issues)
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1

    except Exception as e:
        # Let all other exceptions bubble up with full traceback
        # (per issue spec: "Let exceptions bubble up naturally for debugging")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
