"""Status display and staleness checking for vscodeclaude feature."""

import logging
import subprocess
from pathlib import Path
from types import ModuleType

from ..github_operations.issue_manager import IssueData, IssueManager
from .sessions import check_vscode_running, load_sessions
from .types import VSCodeClaudeSession

logger = logging.getLogger(__name__)


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


def get_issue_current_status(
    issue_manager: IssueManager,
    issue_number: int,
) -> tuple[str | None, bool]:
    """Get current status label and open/closed state for an issue.

    Args:
        issue_manager: IssueManager for GitHub API
        issue_number: GitHub issue number

    Returns:
        Tuple of (status_label, is_open) where:
        - status_label: Current status label or None if no status found
        - is_open: True if issue is open, False if closed
    """
    try:
        issue = issue_manager.get_issue(issue_number)
        is_open = issue["state"] == "open"
        for label in issue["labels"]:
            if label.startswith("status-"):
                return label, is_open
        return None, is_open
    except Exception as e:
        logger.warning("Failed to get issue #%d status: %s", issue_number, e)
        return None, False  # Assume closed on error (conservative)


def is_issue_closed(session: VSCodeClaudeSession) -> bool:
    """Check if session's issue is closed.

    Args:
        session: Session to check

    Returns:
        True if issue is closed
    """
    coordinator = _get_coordinator()

    repo_full_name = session["repo"]
    issue_number = session["issue_number"]

    # Create issue manager for the repo
    repo_url = f"https://github.com/{repo_full_name}"
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)

    # Get current status and open/closed state
    _, is_open = get_issue_current_status(issue_manager, issue_number)

    return not is_open


def is_session_stale(session: VSCodeClaudeSession) -> bool:
    """Check if session's issue status has changed.

    Args:
        session: Session to check

    Returns:
        True if issue status differs from session status

    Note:
        Closed issues should be filtered out before calling this function.
        Open issues without status labels log a warning but are NOT marked stale.
    """
    coordinator = _get_coordinator()

    repo_full_name = session["repo"]
    issue_number = session["issue_number"]
    session_status = session["status"]

    # Create issue manager for the repo
    repo_url = f"https://github.com/{repo_full_name}"
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)

    # Get current status and open/closed state
    current_status, is_open = get_issue_current_status(issue_manager, issue_number)

    # Closed issues should be filtered out before this function is called
    if not is_open:
        logger.warning(
            "is_session_stale called on closed issue #%d - filter these out first",
            issue_number,
        )
        return True

    # If no status found on open issue, log warning but don't mark as stale
    if current_status is None:
        logger.warning(
            "Issue #%d is open but has no status label",
            issue_number,
        )
        return False

    return current_status != session_status


def check_folder_dirty(folder_path: Path) -> bool:
    """Check if folder has uncommitted changes.

    Args:
        folder_path: Path to git repository

    Returns:
        True if there are uncommitted changes

    Uses: git status --porcelain
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=folder_path,
            capture_output=True,
            text=True,
            check=True,
        )
        # If output is empty, the folder is clean
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        # On error, assume dirty to be safe
        return True
    except Exception:
        # On any other error, assume dirty to be safe
        return True


def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
) -> str:
    """Determine next action for a session.

    Args:
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running

    Returns:
        Action string like "(active)", "→ Restart", "→ Delete", "⚠️ Manual cleanup"
    """
    if is_vscode_running:
        return "(active)"

    if is_stale:
        if is_dirty:
            return "⚠️ Manual cleanup"
        return "→ Delete (with --cleanup)"

    return "→ Restart"


def _get_issue_status(issue: IssueData) -> str:
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


def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    repo_filter: str | None = None,
) -> None:
    """Print status table to stdout.

    Args:
        sessions: Current sessions from JSON
        eligible_issues: Eligible issues not yet in sessions (repo_name, issue)
        repo_filter: Optional repo name filter

    Columns:
    - Folder
    - Issue
    - Status
    - VSCode
    - Repo
    - Next Action
    """
    # Column widths
    col_folder = 20
    col_issue = 6
    col_status = 16
    col_vscode = 10
    col_repo = 15
    col_action = 25

    # Print header
    header = (
        f"{'Folder':<{col_folder}} "
        f"{'Issue':<{col_issue}} "
        f"{'Status':<{col_status}} "
        f"{'VSCode':<{col_vscode}} "
        f"{'Repo':<{col_repo}} "
        f"{'Next Action':<{col_action}}"
    )
    print(header)
    print("-" * len(header))

    # Track session issue keys to identify eligible issues not in sessions
    session_keys: set[tuple[str, int]] = set()

    # Print session rows
    for session in sessions:
        # Skip sessions for closed issues - they're no longer relevant
        if is_issue_closed(session):
            logger.debug(
                "Skipping session for closed issue #%d", session["issue_number"]
            )
            continue

        repo_full = session["repo"]
        repo_short = repo_full.split("/")[-1] if "/" in repo_full else repo_full

        # Apply repo filter
        if repo_filter and repo_short != repo_filter:
            continue

        folder_name = Path(session["folder"]).name
        issue_num = f"#{session['issue_number']}"
        status = session["status"]

        # Truncate folder name if too long
        if len(folder_name) > col_folder - 1:
            folder_name = folder_name[: col_folder - 4] + "..."

        # Truncate status if too long
        if len(status) > col_status - 1:
            status = status[: col_status - 4] + "..."

        # Check VSCode and stale status
        is_running = check_vscode_running(session.get("vscode_pid"))
        folder_path = Path(session["folder"])
        is_dirty = check_folder_dirty(folder_path) if folder_path.exists() else False
        stale = is_session_stale(session)

        vscode_status = "Running" if is_running else "Closed"
        action = get_next_action(stale, is_dirty, is_running)

        # Show status change indicator
        if stale:
            status = (
                f"→ {status[:col_status - 4]}"
                if len(status) > col_status - 3
                else f"→ {status}"
            )

        row = (
            f"{folder_name:<{col_folder}} "
            f"{issue_num:<{col_issue}} "
            f"{status:<{col_status}} "
            f"{vscode_status:<{col_vscode}} "
            f"{repo_short:<{col_repo}} "
            f"{action:<{col_action}}"
        )
        print(row)

        session_keys.add((session["repo"], session["issue_number"]))

    # Print eligible issues not in sessions
    for repo_name, issue in eligible_issues:
        # Skip if session exists for this issue
        # Use repo_name from the tuple since IssueData doesn't include repo
        if (repo_name, issue["number"]) in session_keys:
            continue

        # Extract short repo name for display
        repo_short = repo_name.split("/")[-1] if "/" in repo_name else repo_name

        # Apply repo filter
        if repo_filter and repo_short != repo_filter:
            continue

        issue_num = f"#{issue['number']}"
        status = _get_issue_status(issue)

        # Truncate status if too long
        if len(status) > col_status - 1:
            status = status[: col_status - 4] + "..."

        row = (
            f"{'-':<{col_folder}} "
            f"{issue_num:<{col_issue}} "
            f"{status:<{col_status}} "
            f"{'-':<{col_vscode}} "
            f"{repo_short:<{col_repo}} "
            f"{'→ Create and start':<{col_action}}"
        )
        print(row)

    # Handle empty case
    if not sessions and not eligible_issues:
        print("No sessions or eligible issues found.")
