"""Helper functions for vscodeclaude orchestration.

Contains utility functions for:
- Repo URL parsing (extracting owner/repo from URLs)
- Issue data extraction (status labels)
- Session building
- Display formatting (stage names, title truncation)
"""

from datetime import datetime, timezone

from ...utils.github_operations.issues import IssueData
from .config import get_repo_full_name, get_repo_short_name, get_vscodeclaude_config
from .types import VSCodeClaudeSession


def get_repo_short_name_from_full(repo_full_name: str) -> str:
    """Extract short repo name from full name (owner/repo).

    Args:
        repo_full_name: Full repo name like "owner/repo"

    Returns:
        Short repo name (e.g., "repo")
    """
    if "/" in repo_full_name:
        return repo_full_name.split("/")[-1]
    return repo_full_name


def get_issue_status(issue: IssueData) -> str:
    """Get the status label from an issue.

    Args:
        issue: Issue data dict

    Returns:
        Status label string or empty string if none found
    """
    for label in issue["labels"]:
        if label.startswith("status-"):
            return label
    return ""


def build_session(
    folder: str,
    repo: str,
    issue_number: int,
    status: str,
    vscode_pid: int,
    is_intervention: bool,
) -> VSCodeClaudeSession:
    """Build a session dictionary.

    Args:
        folder: Full path to working folder
        repo: "owner/repo" format
        issue_number: GitHub issue number
        status: Status label
        vscode_pid: VSCode process ID
        is_intervention: If True, intervention mode

    Returns:
        VSCodeClaudeSession dict
    """
    return {
        "folder": folder,
        "repo": repo,
        "issue_number": issue_number,
        "status": status,
        "vscode_pid": vscode_pid,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "is_intervention": is_intervention,
    }


def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display.

    Args:
        status: Status label (e.g., "status-07:code-review")

    Returns:
        Display name (e.g., "CODE REVIEW")
    """
    config = get_vscodeclaude_config(status)
    return config["display_name"] if config else status.upper()


def truncate_title(title: str, max_length: int = 50) -> str:
    """Truncate title for display, adding ellipsis if needed.

    Args:
        title: Original title
        max_length: Maximum length

    Returns:
        Truncated title with "..." if needed
    """
    if len(title) <= max_length:
        return title
    # Subtract 3 for the ellipsis
    return title[: max_length - 3] + "..."
