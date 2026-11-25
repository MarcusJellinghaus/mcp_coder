"""Core business logic for coordinator package.

This module contains:
- Configuration management functions
- Issue filtering functions (direct fetch, and a filter for cached issue lists)
- Executor capacity check (find_waiting_build)
- Workflow dispatch function
"""

import logging
from datetime import UTC, datetime, timedelta
from enum import Enum

from ....config.label_config import load_labels_config
from ....mcp_workspace_github import (
    IssueBranchManager,
    IssueData,
    IssueManager,
    RepoIdentifier,
)
from ....utils.jenkins_operations.client import JenkinsClient
from ....utils.jenkins_operations.diagnostics import job_url_path
from ....utils.jenkins_operations.models import BuildInfo
from ....utils.user_config import get_config_file_path, get_config_values
from ....workflow_utils.rate_limit import as_rate_limit
from .command_templates import PRIORITY_ORDER, WORKFLOW_TEMPLATES
from .workflow_constants import WORKFLOW_MAPPING

logger = logging.getLogger(__name__)


def load_repo_config(repo_name: str) -> dict[str, str | bool | int | list[str] | None]:
    """Load repository configuration from config file.

    Args:
        repo_name: Name of repository to load (e.g., "mcp_coder")

    Returns:
        Dictionary with repo_url, executor_job_path, github_credentials_id, executor_os
        Values may be None except executor_os which defaults to "linux" (normalized to lowercase)
        and update_issue_labels / post_issue_comments, which default to True unless
        the section sets them to false.
    """
    section = f"coordinator.repos.{repo_name}"

    # Batch fetch all config values in single disk read
    config = get_config_values(
        [
            (section, "repo_url", None),
            (section, "executor_job_path", None),
            (section, "github_credentials_id", None),
            (section, "executor_os", None),
            (section, "update_issue_labels", None),
            (section, "post_issue_comments", None),
        ]
    )

    repo_url = config[(section, "repo_url")]
    executor_job_path = config[(section, "executor_job_path")]
    github_credentials_id = config[(section, "github_credentials_id")]

    # Load executor_os with default and normalize to lowercase
    raw_executor_os = config[(section, "executor_os")]
    if isinstance(raw_executor_os, str):
        executor_os = raw_executor_os.lower()  # Normalize to lowercase
    else:
        executor_os = "linux"  # Default

    # Always return dict with field values (may be None except executor_os and bool flags)
    return {
        "repo_url": repo_url,
        "executor_job_path": executor_job_path,
        "github_credentials_id": github_credentials_id,
        "executor_os": executor_os,
        "update_issue_labels": config[(section, "update_issue_labels")] is not False,
        "post_issue_comments": config[(section, "post_issue_comments")] is not False,
    }


def validate_repo_config(
    repo_name: str, config: dict[str, str | bool | int | list[str] | None]
) -> None:
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
    # Batch fetch all Jenkins credentials in single disk read
    config = get_config_values(
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

    # Type narrowing: if we reach here, all values are non-None strings
    assert isinstance(server_url, str)  # noqa: S101
    assert isinstance(username, str)  # noqa: S101
    assert isinstance(api_token, str)  # noqa: S101

    return (server_url, username, api_token)


def stage_index(issue: IssueData) -> int:
    """Position of the issue's stage in PRIORITY_ORDER; lower is dispatched first.

    Returns:
        Index of the first label found in PRIORITY_ORDER, len(PRIORITY_ORDER) if none.
    """
    for label in issue["labels"]:
        if label in PRIORITY_ORDER:
            return PRIORITY_ORDER.index(label)
    return len(PRIORITY_ORDER)


def _filter_eligible_issues(issues: list[IssueData]) -> list[IssueData]:
    """Filter issues for eligibility (same logic as get_eligible_issues).

    Args:
        issues: List of issues to filter

    Returns:
        Eligible issues in input order; the coordinator sorts globally.
    """
    # Load label configuration
    from ....config.label_config import get_labels_config_path

    labels_config = load_labels_config(get_labels_config_path(None))

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

    return eligible_issues


def get_eligible_issues(
    issue_manager: IssueManager,
    log_level: str = "INFO",  # pylint: disable=unused-argument
) -> list[IssueData]:
    """Get issues ready for automation.

    Args:
        issue_manager: IssueManager instance for GitHub API calls
        log_level: Logging level for debug output

    Returns:
        Eligible issues in the order list_issues returned them; the
        coordinator sorts globally.

    """
    # Load label configuration
    # Uses bundled package config (coordinator operates without local project context)
    from ....config.label_config import get_labels_config_path

    labels_config = load_labels_config(get_labels_config_path(None))

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

    return eligible_issues


def build_jenkins_label(repo_name: str, identifier: str, action: str) -> str:
    """Build the Jenkins job LABEL parameter.

    Returns:
        Formatted label string.
    """
    return f"{repo_name} - {identifier} - {action}"


UNNAMED_WARNING_AFTER = timedelta(minutes=60)


def find_waiting_build(
    jenkins_client: JenkinsClient, job_path: str
) -> BuildInfo | None:
    """Return a running build of the executor job that is still waiting for an agent.

    The signal is the display name: the Executor pipeline sets currentBuild.displayName
    from LABEL right after it gets its agent executor (top-level ``agent`` in the
    Executor job's pipeline script), so a running build still named ``#<number>`` is
    waiting. If the pipeline ever renames before agent allocation, this check silently
    stops blocking. See docs/repository-setup/jenkins.md.

    Args:
        jenkins_client: Jenkins client used to list the job's running builds.
        job_path: Full path of the executor job, e.g. "Windows-Agents/Executor".

    Returns:
        The oldest waiting build, or None when the job has capacity.

    Raises:
        JenkinsError: If the build list cannot be read.
    """  # noqa: DOC502 - raised by get_recent_builds, part of this contract
    # Default limit (100) on purpose: the limit applies before the status
    # filter, so a small one could miss a long-running unnamed build.
    builds = jenkins_client.get_recent_builds(path=job_path, statuses=["running"])
    waiting = [b for b in builds if b.display_name in ("", f"#{b.number}")]

    now = datetime.now(UTC)
    for build in waiting:
        age = now - build.timestamp
        if age > UNNAMED_WARNING_AFTER:
            logger.warning(
                "Executor job '%s': build #%d still unnamed after %d min: "
                "waiting for an agent, or a manual build without LABEL (%s)",
                job_path,
                build.number,
                int(age.total_seconds() // 60),
                build.url,
            )

    if not waiting:
        return None

    oldest = waiting[-1]  # builds are listed newest first
    logger.info(
        "Executor job '%s' busy: build #%d is waiting for an agent (%s)",
        job_path,
        oldest.number,
        oldest.url,
    )
    return oldest


class DispatchResult(Enum):
    """Outcome of dispatch_workflow."""

    STARTED = "started"
    NOT_STARTED = "not_started"  # no linked branch, or invalid repo URL
    STARTED_LABEL_RATE_LIMITED = "started_label_rate_limited"


def dispatch_workflow(
    issue: IssueData,
    workflow_name: str,  # pylint: disable=unused-argument
    repo_config: dict[str, str],
    repo_name: str,
    jenkins_client: JenkinsClient,
    issue_manager: IssueManager,
    branch_manager: IssueBranchManager,
    log_level: str,
) -> DispatchResult:
    """Trigger Jenkins job for workflow and update issue label.

    Args:
        issue: GitHub issue data
        workflow_name: Workflow to execute ("create-plan", "implement", "create-pr")
        repo_config: Repository configuration with repo_url, executor_job_path, credentials
        repo_name: Repository name, used to build the Jenkins job's LABEL
        jenkins_client: Jenkins client for job triggering
        issue_manager: IssueManager for label updates
        branch_manager: IssueBranchManager for branch resolution
        log_level: Log level to pass to workflow command

    Returns:
        STARTED when the Jenkins job started and the label was swapped;
        NOT_STARTED when no job was started (no linked branch, or invalid
        repo URL); STARTED_LABEL_RATE_LIMITED when the job started but the
        label swap hit a GitHub rate limit.

    Raises:
        ValueError: If linked branch missing for implement/create-pr
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
        # Parse repo URL to extract owner and name for branch resolution
        try:
            repo_id = RepoIdentifier.from_repo_url(repo_config["repo_url"])
        except ValueError:
            logger.error(
                f"Invalid GitHub URL in repo config: {repo_config['repo_url']}"
            )
            return DispatchResult.NOT_STARTED

        repo_owner, issue_repo_name = repo_id.owner, repo_id.repo_name

        # Resolve branch with PR fallback (checks linkedBranches then draft/open PRs)
        resolved_branch = branch_manager.get_branch_with_pr_fallback(
            issue_number=issue["number"],
            repo_owner=repo_owner,
            repo_name=issue_repo_name,
        )

        if not resolved_branch:
            logger.error(
                f'No branch found for issue #{issue["number"]} "{issue["title"]}"\n'
                f"  Checked: linkedBranches, draft/open PRs\n"
                f"  Issue URL: {issue['url']}\n"
                f"  Requirement: Issue must have linked branch or draft/open PR"
            )
            return DispatchResult.NOT_STARTED

        branch_name = resolved_branch

    # Step 3: Select appropriate command template based on executor_os and build command
    # Data-driven lookup: an unknown workflow raises KeyError here instead of
    # silently misrouting. str.format() ignores extra kwargs, so all three
    # placeholders are passed uniformly (branch_name is always bound above).
    executor_os = repo_config.get("executor_os", "linux")
    linux_tpl, windows_tpl = WORKFLOW_TEMPLATES[workflow_config["workflow"]]
    template = windows_tpl if executor_os == "windows" else linux_tpl
    command = template.format(
        log_level=log_level, issue_number=issue["number"], branch_name=branch_name
    )

    # Step 4: Build Jenkins job parameters
    params = {
        "REPO_URL": repo_config["repo_url"],
        "BRANCH_NAME": branch_name,
        "COMMAND": command,
        "GITHUB_CREDENTIALS_ID": repo_config["github_credentials_id"],
        "LABEL": build_jenkins_label(
            repo_name, f"#{issue['number']}", workflow_config["workflow"]
        ),
    }

    # Step 5: Trigger Jenkins job
    queue_id = jenkins_client.start_job(repo_config["executor_job_path"], params)

    # Step 6: Get job status to retrieve build URL
    job_status = jenkins_client.get_job_status(queue_id)

    # Build Jenkins links: pipeline URL and build URL (if available)
    jenkins_base_url = jenkins_client.base_url
    pipeline_url = jenkins_base_url + job_url_path(repo_config["executor_job_path"])

    if job_status.url:
        # Build has started - show build URL
        jenkins_link = f"Build: {job_status.url}"
    else:
        # Build still queued - show pipeline URL only
        jenkins_link = f"Pipeline: {pipeline_url}"

    # Step 7: Update issue labels (remove old, add new)
    try:
        issue_manager.remove_labels(issue["number"], current_label)
        issue_manager.add_labels(issue["number"], workflow_config["next_label"])
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if as_rate_limit(exc) is None:
            raise
        logger.error(
            "Issue #%d: Jenkins job started, label not updated "
            "(old label '%s', intended label '%s'): %s",
            issue["number"],
            current_label,
            workflow_config["next_label"],
            exc,
        )
        return DispatchResult.STARTED_LABEL_RATE_LIMITED

    # Step 8: Log success with issue and Jenkins links
    issue_url = issue["url"]
    logger.info(
        f"Successfully dispatched {workflow_config['workflow']} workflow for issue #{issue['number']}: "
        f"removed '{current_label}', added '{workflow_config['next_label']}' | "
        f"Issue: {issue_url} | {jenkins_link}",
    )
    return DispatchResult.STARTED
