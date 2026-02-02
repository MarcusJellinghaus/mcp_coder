"""Helper functions for vscodeclaude orchestration.

Contains utility functions for:
- Repo URL parsing (extracting owner/repo from URLs)
- Issue data extraction (status labels)
- Session building
- Display formatting (stage names, title truncation)
"""

from datetime import datetime, timezone

from ...utils.github_operations.issue_manager import IssueData
from .issues import _get_vscodeclaude_config
from .types import VSCodeClaudeSession


def get_repo_short_name(repo_config: dict[str, str]) -> str:
    """Extract short repo name from repo_url.

    Args:
        repo_config: Repository config dict with repo_url

    Returns:
        Short repo name (e.g., "mcp-coder" from the URL)
    """
    repo_url = repo_config.get("repo_url", "")
    # Extract from URLs like https://github.com/owner/repo.git
    if "/" in repo_url:
        # Use endswith check instead of rstrip to avoid stripping extra characters
        url_clean = repo_url.rstrip("/")
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
        name = url_clean.split("/")[-1]
        return name
    return "repo"


def get_repo_full_name(repo_config: dict[str, str]) -> str:
    """Extract full repo name (owner/repo) from repo_url.

    Args:
        repo_config: Repository config dict with repo_url

    Returns:
        Full repo name (e.g., "owner/repo")

    Raises:
        ValueError: If repo URL cannot be parsed
    """
    repo_url = repo_config.get("repo_url", "")
    # Extract from URLs like https://github.com/owner/repo.git
    if "/" in repo_url:
        # Use removesuffix instead of rstrip to avoid stripping extra characters
        # rstrip(".git") would strip chars {'.','g','i','t'} which corrupts names like "mcp-config"
        url_clean = repo_url.rstrip("/")
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
        parts = url_clean.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    raise ValueError(f"Cannot parse repo URL: {repo_url}")


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
    config = _get_vscodeclaude_config(status)
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
