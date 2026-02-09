"""Issue filtering for vscodeclaude feature."""

import logging
import re
from importlib import resources
from pathlib import Path
from typing import Any, cast

from ...utils.github_operations.issues import (
    IssueBranchManager,
    IssueData,
    IssueManager,
    get_all_cached_issues,
)
from ...utils.github_operations.label_config import load_labels_config

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
