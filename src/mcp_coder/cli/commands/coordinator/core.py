"""Core business logic for coordinator package.

This module contains:
- Configuration management functions
- Issue filtering functions (including cached version via issue_cache)
- Workflow dispatch function
"""

import logging
from pathlib import Path

# Lazy imports from coordinator package to enable test patching
# Tests can patch at 'mcp_coder.cli.commands.coordinator.<name>'
from types import ModuleType
from typing import List, Optional
from urllib.parse import quote

from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_cache import (
    CacheData,
    _update_issue_labels_in_cache,
    get_all_cached_issues,
)
from ....utils.github_operations.issue_manager import IssueData, IssueManager
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.user_config import get_config_file_path
from .command_templates import (
    CREATE_PLAN_COMMAND_TEMPLATE,
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_TEMPLATE,
    CREATE_PR_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_TEMPLATE,
    IMPLEMENT_COMMAND_WINDOWS,
    PRIORITY_ORDER,
)
from .workflow_constants import WORKFLOW_MAPPING


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


logger = logging.getLogger(__name__)


def load_repo_config(repo_name: str) -> dict[str, Optional[str]]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, executor_job_path, github_credentials_id, executor_os
        Values may be None except executor_os which defaults to "linux" (normalized to lowercase)
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    section = f"coordinator.repos.{repo_name}"

    # Batch fetch all config values in single disk read
    config = coordinator.get_config_values(
        [
            (section, "repo_url", None),
            (section, "executor_job_path", None),
            (section, "github_credentials_id", None),
            (section, "executor_os", None),
        ]
    )

    repo_url = config[(section, "repo_url")]
    executor_job_path = config[(section, "executor_job_path")]
    github_credentials_id = config[(section, "github_credentials_id")]

    # Load executor_os with default and normalize to lowercase
    executor_os = config[(section, "executor_os")]
    if executor_os:
        executor_os = executor_os.lower()  # Normalize to lowercase
    else:
        executor_os = "linux"  # Default

    # Always return dict with field values (may be None except executor_os)
    return {
        "repo_url": repo_url,
        "executor_job_path": executor_job_path,
        "github_credentials_id": github_credentials_id,
        "executor_os": executor_os,
    }


def validate_repo_config(repo_name: str, config: dict[str, Optional[str]]) -> None:
    """Validate repository configuration has all required fields.

    Args:
        repo_name: Name of repository being validated
        config: Repository configuration dict with possibly None values

    Raises:
        ValueError: If any required fields are missing or invalid with detailed error message
    """
    required_fields = ["repo_url", "executor_job_path", "github_credentials_id"]
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

    # Validate executor_os field (already normalized to lowercase by load_repo_config)
    executor_os = config.get("executor_os", "linux")
    if executor_os not in ["windows", "linux"]:
        config_path = get_config_file_path()
        section_name = f"coordinator.repos.{repo_name}"
        error_msg = (
            f"Config file: {config_path} - "
            f"section [{section_name}] - "
            f"value for field 'executor_os' invalid: got '{executor_os}'. "
            f"Must be 'windows' or 'linux' (case-insensitive)"
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
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # Batch fetch all Jenkins credentials in single disk read
    config = coordinator.get_config_values(
        [
            ("jenkins", "server_url", None),
            ("jenkins", "username", None),
            ("jenkins", "api_token", None),
        ]
    )
    server_url = config[("jenkins", "server_url")]
    username = config[("jenkins", "username")]
    api_token = config[("jenkins", "api_token")]

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


def _filter_eligible_issues(issues: List[IssueData]) -> List[IssueData]:
    """Filter issues for eligibility (same logic as get_eligible_issues).

    Args:
        issues: List of issues to filter

    Returns:
        List of eligible issues sorted by priority
    """
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # Load label configuration
    from importlib import resources

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = coordinator.load_labels_config(config_path)

    # Extract bot_pickup labels and ignore_labels
    bot_pickup_labels = set()
    for label in labels_config["workflow_labels"]:
        if label["category"] == "bot_pickup":
            bot_pickup_labels.add(label["name"])

    ignore_labels_set = set(labels_config.get("ignore_labels", []))

    # Filter issues (only open state)
    eligible_issues = []
    for issue in issues:
        # Skip if not open
        if issue.get("state") != "open":
            continue

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

    # Sort by priority
    priority_map = {label: i for i, label in enumerate(PRIORITY_ORDER)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        return len(PRIORITY_ORDER)  # Lowest priority

    eligible_issues.sort(key=get_priority)
    return eligible_issues


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
    # Use late binding for patchable function access
    coordinator = _get_coordinator()

    # Load label configuration
    # Uses bundled package config (coordinator operates without local project context)
    from importlib import resources

    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    labels_config = coordinator.load_labels_config(config_path)

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


def get_cached_eligible_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> List[IssueData]:
    """Get eligible issues using cache for performance and duplicate protection.

    Thin wrapper that:
    1. Calls get_all_cached_issues() for cache operations
    2. Filters results using _filter_eligible_issues()
    3. Falls back to get_eligible_issues() on cache errors

    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_manager: IssueManager for GitHub API calls
        force_refresh: Bypass cache entirely
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)

    Returns:
        List of eligible issues (filtered by bot_pickup labels, sorted by priority)
    """
    try:
        all_issues = get_all_cached_issues(
            repo_full_name=repo_full_name,
            issue_manager=issue_manager,
            force_refresh=force_refresh,
            cache_refresh_minutes=cache_refresh_minutes,
        )
        return _filter_eligible_issues(all_issues)
    except (ValueError, KeyError, TypeError) as e:
        logger.warning(
            f"Cache error for {repo_full_name}: {e}, falling back to direct fetch"
        )
        return get_eligible_issues(issue_manager)


def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,
    repo_config: dict[str, str],
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> None:
    """Trigger Jenkins job for workflow and update issue label.

    Args:
        issue: GitHub issue data
        workflow_name: Workflow to execute ("create-plan", "implement", "create-pr")
        repo_config: Repository configuration with repo_url, executor_test_path, credentials
        jenkins_client: Jenkins client for job triggering
        issue_manager: IssueManager for label updates
        branch_manager: IssueBranchManager for branch resolution
        log_level: Log level to pass to workflow command

    Raises:
        ValueError: If linked branch missing for implement/create-pr
        JenkinsError: If job trigger or status check fails
    """
    # Step 1: Find current workflow label from issue
    current_label = None
    for label in issue["labels"]:
        if label in WORKFLOW_MAPPING:
            current_label = label
            break

    if not current_label:
        raise ValueError(f"No workflow label found on issue #{issue['number']}")

    workflow_config = WORKFLOW_MAPPING[current_label]

    # Step 2: Determine branch name based on branch_strategy
    if workflow_config["branch_strategy"] == "main":
        branch_name = "main"
    else:  # from_issue
        branches = branch_manager.get_linked_branches(issue["number"])
        if not branches:
            logger.warning(
                f"No linked branch found for issue #{issue['number']}, skipping workflow dispatch"
            )
            return
        branch_name = branches[0]

    # Step 3: Select appropriate command template based on executor_os and build command
    executor_os = repo_config.get("executor_os", "linux")

    if executor_os == "windows":
        # Windows templates
        if workflow_config["workflow"] == "create-plan":
            command = CREATE_PLAN_COMMAND_WINDOWS.format(
                log_level=log_level, issue_number=issue["number"]
            )
        elif workflow_config["workflow"] == "implement":
            command = IMPLEMENT_COMMAND_WINDOWS.format(
                log_level=log_level, branch_name=branch_name
            )
        else:  # create-pr
            command = CREATE_PR_COMMAND_WINDOWS.format(
                log_level=log_level, branch_name=branch_name
            )
    else:
        # Linux templates (default)
        if workflow_config["workflow"] == "create-plan":
            command = CREATE_PLAN_COMMAND_TEMPLATE.format(
                log_level=log_level, issue_number=issue["number"]
            )
        elif workflow_config["workflow"] == "implement":
            command = IMPLEMENT_COMMAND_TEMPLATE.format(
                log_level=log_level, branch_name=branch_name
            )
        else:  # create-pr
            command = CREATE_PR_COMMAND_TEMPLATE.format(
                log_level=log_level, branch_name=branch_name
            )

    # Step 4: Build Jenkins job parameters
    params = {
        "REPO_URL": repo_config["repo_url"],
        "BRANCH_NAME": branch_name,
        "COMMAND": command,
        "GITHUB_CREDENTIALS_ID": repo_config["github_credentials_id"],
    }

    # Step 5: Trigger Jenkins job
    queue_id = jenkins_client.start_job(repo_config["executor_job_path"], params)

    # Step 6: Get job status to retrieve build URL
    job_status = jenkins_client.get_job_status(queue_id)

    # Build Jenkins links: pipeline URL and build URL (if available)
    jenkins_base_url = jenkins_client._client.server.rstrip("/")
    # Convert job path to URL format: "Tests/mcp-coder-test" -> "Tests/job/mcp-coder-test"
    # URL-encode each part to handle spaces and special characters
    job_path_parts = repo_config["executor_job_path"].split("/")
    encoded_parts = [quote(part, safe="") for part in job_path_parts]
    pipeline_url = f"{jenkins_base_url}/job/" + "/job/".join(encoded_parts)

    if job_status.url:
        # Build has started - show build URL
        jenkins_link = f"Build: {job_status.url}"
    else:
        # Build still queued - show pipeline URL only
        jenkins_link = f"Pipeline: {pipeline_url}"

    # Step 7: Update issue labels (remove old, add new)
    issue_manager.remove_labels(issue["number"], current_label)
    issue_manager.add_labels(issue["number"], workflow_config["next_label"])

    # Step 8: Log success with issue and Jenkins links
    issue_url = issue["url"]
    logger.info(
        f"Successfully dispatched {workflow_config['workflow']} workflow for issue #{issue['number']}: "
        f"removed '{current_label}', added '{workflow_config['next_label']}' | "
        f"Issue: {issue_url} | {jenkins_link}"
    )
