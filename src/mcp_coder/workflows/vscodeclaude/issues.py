"""Issue filtering for vscodeclaude feature."""

import logging
import re
from importlib import resources
from pathlib import Path
from typing import Any, cast

from ...utils.github_operations.github_utils import RepoIdentifier
from ...utils.github_operations.issues import (
    IssueBranchManager,
    IssueData,
    IssueManager,
    get_all_cached_issues,
)
from ...utils.github_operations.label_config import load_labels_config
from ...utils.user_config import get_cache_refresh_minutes, load_config
from .config import load_vscodeclaude_config
from .helpers import get_issue_status

logger = logging.getLogger(__name__)


def _load_labels_config() -> dict[str, Any]:
    """Load labels configuration from bundled package config.

    Returns:
        Labels config dict with workflow_labels and ignore_labels
    """
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    result: dict[str, Any] = load_labels_config(config_path)
    return result


def get_human_action_labels() -> set[str]:
    """Get set of human_action status labels from labels.json.

    Returns:
        Set of label names with category="human_action"
    """
    labels_config = _load_labels_config()

    return {
        label["name"]
        for label in labels_config["workflow_labels"]
        if label["category"] == "human_action"
    }


def get_ignore_labels() -> set[str]:
    """Get set of ignore labels from labels.json (lowercase for case-insensitive matching).

    Returns:
        Set of lowercase label names to ignore
    """
    labels_config = _load_labels_config()
    ignore_labels: list[str] = labels_config.get("ignore_labels", [])
    return {label.lower() for label in ignore_labels}


def get_matching_ignore_label(
    issue_labels: list[str],
    ignore_labels: set[str],
) -> str | None:
    """Find first matching ignore label in issue's labels (case-insensitive).

    Args:
        issue_labels: List of label names from the issue
        ignore_labels: Set of lowercase ignore label names

    Returns:
        The original label name if match found, None otherwise
    """
    for label in issue_labels:
        if label.lower() in ignore_labels:
            return label
    return None


def _get_status_priority(label: str) -> int:
    """Extract numeric priority from status label.

    Args:
        label: Label name like "status-07:code-review"

    Returns:
        Numeric priority (e.g., 7) or 0 if not a status label
    """
    match = re.search(r"status-(\d+):", label)
    return int(match.group(1)) if match else 0


def get_vscodeclaude_config(status: str) -> dict[str, Any] | None:
    """Get vscodeclaude config for a status label.

    Shared helper used by workspace.py and helpers.py.

    Args:
        status: Status label like "status-07:code-review"

    Returns:
        vscodeclaude config dict or None if not found
    """
    labels_config = _load_labels_config()
    for label in labels_config["workflow_labels"]:
        if label["name"] == status and "vscodeclaude" in label:
            return cast(dict[str, Any], label["vscodeclaude"])
    return None


def is_status_eligible_for_session(status: str) -> bool:
    """Check if status should have a VSCodeClaude session.

    Returns True only for human_action statuses with non-null initial_command:
    - status-01:created
    - status-04:plan-review
    - status-07:code-review

    Returns False for:
    - bot_pickup statuses (02, 05, 08)
    - bot_busy statuses (03, 06, 09)
    - status-10:pr-created (null initial_command)
    - Unknown/invalid status strings

    Args:
        status: Status label like "status-07:code-review"

    Returns:
        True if status should have a VSCodeClaude session
    """
    config = get_vscodeclaude_config(status)
    if config is None:
        return False
    initial_command = config.get("initial_command")
    return initial_command is not None


def status_requires_linked_branch(status: str) -> bool:
    """Check if status requires a linked branch to start/restart session.

    Args:
        status: Status label like "status-04:plan-review"

    Returns:
        True if status requires linked branch (status-04, status-07)
        False for status-01 and all other statuses
    """
    return status in ("status-04:plan-review", "status-07:code-review")


def _is_issue_eligible(
    issue: IssueData,
    human_action_labels: set[str],
    ignore_labels_set: set[str],
    github_username: str,
) -> bool:
    """Check if an issue is eligible for vscodeclaude session.

    Args:
        issue: Issue to check
        human_action_labels: Set of human_action label names
        ignore_labels_set: Set of labels to ignore
        github_username: Username that must be assigned

    Returns:
        True if issue is eligible
    """
    issue_labels = set(issue["labels"])

    # Must have exactly one human_action label
    if len(issue_labels & human_action_labels) != 1:
        return False

    # Must not have any ignore_labels
    if issue_labels & ignore_labels_set:
        return False

    # Must be assigned to github_username
    return github_username in issue["assignees"]


def _filter_eligible_vscodeclaude_issues(
    all_issues: list[IssueData],
    github_username: str,
) -> list[IssueData]:
    """Filter issues for vscodeclaude eligibility from a pre-fetched list.

    This is a pure filtering function that works on already-fetched issues,
    enabling cache reuse across multiple operations.

    Filters for:
    - Open issues only (state == "open")
    - Exactly one human_action label
    - Assigned to github_username
    - No ignore_labels

    Args:
        all_issues: Pre-fetched list of issues to filter
        github_username: Username to filter assignments

    Returns:
        List of eligible issues sorted by priority (later stages first)
    """
    labels_config = _load_labels_config()

    # Extract human_action labels
    human_action_labels = {
        label["name"]
        for label in labels_config["workflow_labels"]
        if label["category"] == "human_action"
    }

    # Extract ignore_labels set
    ignore_labels_set: set[str] = set(labels_config.get("ignore_labels", []))

    # Filter issues - only open issues are eligible
    eligible_issues = [
        issue
        for issue in all_issues
        if issue["state"] == "open"
        and _is_issue_eligible(
            issue, human_action_labels, ignore_labels_set, github_username
        )
    ]

    # Sort by numeric prefix descending (higher number = higher priority)
    def get_issue_priority(issue: IssueData) -> int:
        """Get max priority from issue's status labels."""
        return max(
            (_get_status_priority(label) for label in issue["labels"]), default=0
        )

    eligible_issues.sort(key=get_issue_priority, reverse=True)

    return eligible_issues


def get_eligible_vscodeclaude_issues(
    issue_manager: IssueManager,
    github_username: str,
) -> list[IssueData]:
    """Get issues eligible for vscodeclaude sessions.

    This is a convenience function that fetches all open issues from the API
    and filters them. For better performance with multiple operations,
    consider using _filter_eligible_vscodeclaude_issues() with cached issues.

    Filters for:
    - Open issues only
    - Exactly one human_action label
    - Assigned to github_username
    - No ignore_labels

    Args:
        issue_manager: IssueManager for GitHub API
        github_username: Username to filter assignments

    Returns:
        List of eligible issues sorted by priority (later stages first)
    """
    # Get all open issues from API
    all_issues = issue_manager.list_issues(state="open", include_pull_requests=False)

    # Use shared filtering logic
    return _filter_eligible_vscodeclaude_issues(all_issues, github_username)


def get_cached_eligible_vscodeclaude_issues(
    repo_full_name: str,
    issue_manager: IssueManager,
    github_username: str,
    force_refresh: bool = False,
    cache_refresh_minutes: int = 1440,
) -> list[IssueData]:
    """Get eligible vscodeclaude issues using cache.

    Thin wrapper that:
    1. Calls get_all_cached_issues() for cache operations
    2. Filters results using _filter_eligible_vscodeclaude_issues()
    3. Falls back to get_eligible_vscodeclaude_issues() on cache errors

    Args:
        repo_full_name: Repository in "owner/repo" format
        issue_manager: IssueManager for GitHub API
        github_username: Username to filter assignments
        force_refresh: Bypass cache entirely (default: False)
        cache_refresh_minutes: Full refresh threshold (default: 1440 = 24 hours)

    Returns:
        List of eligible issues sorted by priority (later stages first)
    """
    try:
        # Get all issues from cache
        all_issues = get_all_cached_issues(
            repo_full_name=repo_full_name,
            issue_manager=issue_manager,
            force_refresh=force_refresh,
            cache_refresh_minutes=cache_refresh_minutes,
        )

        # Filter for vscodeclaude eligibility
        return _filter_eligible_vscodeclaude_issues(all_issues, github_username)

    except (ValueError, KeyError, TypeError) as e:
        # Fall back to direct API fetch on cache errors
        logger.warning(f"Cache error for {repo_full_name}: {e}, falling back to API")
        return get_eligible_vscodeclaude_issues(issue_manager, github_username)


def get_linked_branch_for_issue(
    branch_manager: IssueBranchManager,
    issue_number: int,
) -> str | None:
    """Get linked branch for issue, fail if multiple.

    Args:
        branch_manager: IssueBranchManager for GitHub API
        issue_number: GitHub issue number

    Returns:
        Branch name if exactly one linked, None if none

    Raises:
        ValueError: If multiple branches linked to issue
    """
    branches = branch_manager.get_linked_branches(issue_number)

    if not branches:
        return None

    if len(branches) > 1:
        raise ValueError(
            f"Issue #{issue_number} has multiple branches linked: {branches}"
        )

    return branches[0]


def build_eligible_issues_with_branch_check(
    repo_names: list[str],
) -> tuple[list[tuple[str, IssueData]], set[tuple[str, int]]]:
    """Build eligible issues list with branch requirement checking.

    Args:
        repo_names: List of repo config names from coordinator.repos

    Returns:
        Tuple of:
        - List of (repo_full_name, issue) tuples for eligible issues
        - Set of (repo_full_name, issue_number) tuples for issues
          that require but lack a linked branch

    This function:
    1. Loops through each repo
    2. Loads repo config and GitHub username
    3. Gets eligible vscodeclaude issues (cached)
    4. For status-04/07 issues, checks for linked branch
    5. Adds to issues_without_branch set if branch missing/multiple
    """
    eligible_issues_list: list[tuple[str, IssueData]] = []
    issues_without_branch: set[tuple[str, int]] = set()

    for repo_name in repo_names:
        try:
            # Load repo config
            config_data = load_config()
            repos_section = config_data.get("coordinator", {}).get("repos", {})
            repo_config = repos_section.get(repo_name, {})
            repo_url = repo_config.get("repo_url", "")
            if not repo_url:
                continue

            # Get repo_full_name from repo_url
            try:
                repo_identifier = RepoIdentifier.from_repo_url(repo_url)
                repo_full_name = repo_identifier.full_name
            except ValueError:
                # Fallback: extract from URL directly
                url_clean = repo_url.rstrip("/")
                if url_clean.endswith(".git"):
                    url_clean = url_clean[:-4]
                parts = url_clean.split("/")
                if len(parts) >= 2:
                    repo_full_name = f"{parts[-2]}/{parts[-1]}"
                else:
                    continue

            # Load vscodeclaude config for github_username
            vscodeclaude_config = load_vscodeclaude_config()
            github_username = str(vscodeclaude_config.get("github_username", ""))
            if not github_username:
                continue

            # Get eligible issues using cache
            issue_manager = IssueManager(repo_url=repo_url)
            eligible_issues = get_cached_eligible_vscodeclaude_issues(
                repo_full_name=repo_full_name,
                issue_manager=issue_manager,
                github_username=github_username,
                force_refresh=False,
                cache_refresh_minutes=get_cache_refresh_minutes(),
            )

            # Create branch manager for linked branch checks
            branch_manager = IssueBranchManager(repo_url=repo_url)

            # Add to result list and check branch requirements
            for issue in eligible_issues:
                eligible_issues_list.append((repo_full_name, issue))

                # Check if this issue needs branch but doesn't have one
                status = get_issue_status(issue)
                if status_requires_linked_branch(status):
                    try:
                        branch = get_linked_branch_for_issue(
                            branch_manager, issue["number"]
                        )
                        if branch is None:
                            issues_without_branch.add((repo_full_name, issue["number"]))
                    except ValueError:
                        # Multiple branches - also add to set
                        issues_without_branch.add((repo_full_name, issue["number"]))

        except Exception as e:
            logger.warning(f"Failed to process repo {repo_name}: {e}")
            continue

    return eligible_issues_list, issues_without_branch
