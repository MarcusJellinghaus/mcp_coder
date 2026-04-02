"""Helper functions for vscodeclaude orchestration.

Contains utility functions for:
- Repo URL parsing (extracting owner/repo from URLs)
- Issue data extraction (status labels)
- Session building
- Display formatting (stage names, title truncation)
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from ...utils.github_operations.issues import IssueData
from .config import get_vscodeclaude_config
from .types import VSCodeClaudeSession

TO_BE_DELETED_FILENAME = ".to_be_deleted"

__all__ = [
    "TO_BE_DELETED_FILENAME",
    "add_to_be_deleted",
    "build_session",
    "get_issue_status",
    "get_repo_short_name_from_full",
    "get_stage_display_name",
    "load_to_be_deleted",
    "remove_from_to_be_deleted",
    "truncate_title",
]


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
    install_from_github: bool = False,
) -> VSCodeClaudeSession:
    """Build a session dictionary.

    Args:
        folder: Full path to working folder
        repo: "owner/repo" format
        issue_number: GitHub issue number
        status: Status label
        vscode_pid: VSCode process ID
        is_intervention: If True, intervention mode
        install_from_github: If True, install MCP packages from GitHub repos instead of PyPI

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
        "install_from_github": install_from_github,
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


def load_to_be_deleted(workspace_base: str) -> set[str]:
    """Load soft-delete registry.

    Args:
        workspace_base: Path to workspace directory.

    Returns:
        Set of folder names listed in the registry.
    """
    path = Path(workspace_base) / TO_BE_DELETED_FILENAME
    try:
        return {line.strip() for line in path.read_text().splitlines() if line.strip()}
    except FileNotFoundError:
        return set()
    except (OSError, UnicodeDecodeError) as e:
        logging.getLogger(__name__).warning("Failed to read %s: %s", path, e)
        return set()


def add_to_be_deleted(workspace_base: str, folder_name: str) -> None:
    """Add folder name to soft-delete registry.

    No-op if already present.

    Args:
        workspace_base: Path to workspace directory.
        folder_name: Folder name to add.
    """
    existing = load_to_be_deleted(workspace_base)
    if folder_name in existing:
        return
    path = Path(workspace_base) / TO_BE_DELETED_FILENAME
    with path.open("a") as f:
        f.write(folder_name + "\n")


def remove_from_to_be_deleted(workspace_base: str, folder_name: str) -> None:
    """Remove folder name from registry.

    Deletes the file if the registry becomes empty.

    Args:
        workspace_base: Path to workspace directory.
        folder_name: Folder name to remove.
    """
    existing = load_to_be_deleted(workspace_base)
    existing.discard(folder_name)
    path = Path(workspace_base) / TO_BE_DELETED_FILENAME
    if not existing:
        path.unlink(missing_ok=True)
        return
    path.write_text("\n".join(sorted(existing)) + "\n")
