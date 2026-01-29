"""Issue filtering for vscodeclaude feature."""

import logging
from importlib import resources
from pathlib import Path
from types import ModuleType
from typing import Any

from ..github_operations.issue_branch_manager import IssueBranchManager
from ..github_operations.issue_manager import IssueData, IssueManager
from .types import VSCODECLAUDE_PRIORITY

logger = logging.getLogger(__name__)


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


def _load_labels_config() -> dict[str, Any]:
    """Load labels configuration from bundled package config.

    Returns:
        Labels config dict with workflow_labels and ignore_labels
    """
    coordinator = _get_coordinator()
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    result: dict[str, Any] = coordinator.load_labels_config(config_path)
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


def get_eligible_vscodeclaude_issues(
    issue_manager: IssueManager,
    github_username: str,
) -> list[IssueData]:
    """Get issues eligible for vscodeclaude sessions.

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
    labels_config = _load_labels_config()

    # Extract human_action labels
    human_action_labels = {
        label["name"]
        for label in labels_config["workflow_labels"]
        if label["category"] == "human_action"
    }

    # Extract ignore_labels set
    ignore_labels_set: set[str] = set(labels_config.get("ignore_labels", []))

    # Get all open issues and filter
    all_issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    eligible_issues = [
        issue
        for issue in all_issues
        if _is_issue_eligible(
            issue, human_action_labels, ignore_labels_set, github_username
        )
    ]

    # Sort by VSCODECLAUDE_PRIORITY (lower index = higher priority)
    priority_map = {label: i for i, label in enumerate(VSCODECLAUDE_PRIORITY)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        return len(VSCODECLAUDE_PRIORITY)  # Lowest priority

    eligible_issues.sort(key=get_priority)

    return eligible_issues


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
