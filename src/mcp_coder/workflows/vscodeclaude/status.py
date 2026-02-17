"""Status display and staleness checking for vscodeclaude feature."""

import logging
from pathlib import Path

from tabulate import tabulate

from ...utils.github_operations.issues import IssueData, IssueManager
from ...utils.subprocess_runner import CommandOptions, execute_subprocess
from .helpers import get_issue_status
from .issues import is_status_eligible_for_session, status_requires_linked_branch
from .sessions import (
    clear_vscode_process_cache,
    clear_vscode_window_cache,
    is_session_active,
    load_sessions,
)
from .types import VSCodeClaudeSession

logger = logging.getLogger(__name__)


def get_issue_current_status(
    issue_number: int,
    cached_issues: dict[int, IssueData] | None = None,
    issue_manager: IssueManager | None = None,
) -> tuple[str | None, bool]:
    """Get current status label and open/closed state for an issue.

    Args:
        issue_number: GitHub issue number
        cached_issues: Pre-fetched issues dict (preferred, avoids API call)
        issue_manager: IssueManager for fallback API call (required if cached_issues missing)

    Returns:
        Tuple of (status_label, is_open) where:
        - status_label: Current status label or None if no status found
        - is_open: True if issue is open, False if closed
    """
    # Try cache first
    if cached_issues is not None and issue_number in cached_issues:
        issue = cached_issues[issue_number]
        is_open = issue["state"] == "open"
        for label in issue["labels"]:
            if label.startswith("status-"):
                return label, is_open
        return None, is_open

    # Fallback to API call
    if issue_manager is None:
        raise ValueError("Either cached_issues or issue_manager must be provided")

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


def is_issue_closed(
    session: VSCodeClaudeSession,
    cached_issues: dict[int, IssueData] | None = None,
) -> bool:
    """Check if session's issue is closed.

    Args:
        session: Session to check
        cached_issues: Pre-fetched issues dict (avoids API call if provided)

    Returns:
        True if issue is closed
    """
    repo_full_name = session["repo"]
    issue_number = session["issue_number"]

    logger.debug(
        "is_issue_closed: checking #%d in repo %s",
        issue_number,
        repo_full_name,
    )

    # Use cache if available, otherwise create manager for fallback
    if cached_issues is not None:
        _, is_open = get_issue_current_status(issue_number, cached_issues=cached_issues)
    else:
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        _, is_open = get_issue_current_status(issue_number, issue_manager=issue_manager)

    return not is_open


def is_session_stale(
    session: VSCodeClaudeSession,
    cached_issues: dict[int, IssueData] | None = None,
) -> bool:
    """Check if session's issue status has changed.

    Args:
        session: Session to check
        cached_issues: Pre-fetched issues dict (avoids API call if provided)

    Returns:
        True if issue status differs from session status

    Note:
        Closed issues should be filtered out before calling this function.
        Open issues without status labels log a warning but are NOT marked stale.
    """
    repo_full_name = session["repo"]
    issue_number = session["issue_number"]
    session_status = session["status"]

    logger.debug(
        "is_session_stale: checking #%d in repo %s",
        issue_number,
        repo_full_name,
    )

    # Use cache if available, otherwise create manager for fallback
    if cached_issues is not None:
        current_status, is_open = get_issue_current_status(
            issue_number, cached_issues=cached_issues
        )
    else:
        repo_url = f"https://github.com/{repo_full_name}"
        issue_manager = IssueManager(repo_url=repo_url)
        current_status, is_open = get_issue_current_status(
            issue_number, issue_manager=issue_manager
        )

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


def get_folder_git_status(folder_path: Path) -> str:
    """Get git working directory status for display.

    Args:
        folder_path: Path to check

    Returns:
        One of: "Clean", "Dirty", "Missing", "No Git", "Error"
    """
    if not folder_path.exists():
        return "Missing"

    options = CommandOptions(cwd=str(folder_path), check=True)

    # Check if git repo
    try:
        execute_subprocess(["git", "rev-parse", "--git-dir"], options)
    except Exception:
        return "No Git"

    # Check for changes
    try:
        result = execute_subprocess(["git", "status", "--porcelain"], options)
        return "Dirty" if result.stdout.strip() else "Clean"
    except Exception:
        return "Error"


def check_folder_dirty(folder_path: Path) -> bool:
    """Check if folder has uncommitted changes.

    Args:
        folder_path: Path to git repository

    Returns:
        True if there are uncommitted changes OR if status cannot be determined
        (conservative approach for backward compatibility)
    """
    status = get_folder_git_status(folder_path)
    # Only "Clean" means definitely not dirty
    # All other states (Dirty, Missing, No Git, Error) return True
    return status != "Clean"


def get_next_action(
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
    blocked_label: str | None = None,
    skip_reason: str | None = None,
) -> str:
    """Determine next action for a session.

    Args:
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running
        blocked_label: If set, the ignore label blocking this issue (e.g., "blocked", "wait")
        skip_reason: If set, reason session cannot restart:
                     "No branch", "Dirty", "Git error", "Multi-branch"

    Returns:
        Action string like "(active)", "-> Restart", "!! No branch"
    """
    if is_vscode_running:
        return "(active)"

    # Check for skip reason (takes priority over blocked and stale)
    if skip_reason:
        return f"!! {skip_reason}"

    # Check for blocked label (takes priority over stale)
    if blocked_label is not None:
        if is_dirty:
            return "!! Manual"
        return f"Blocked ({blocked_label})"

    if is_stale:
        if is_dirty:
            return "!! Manual cleanup"
        return "-> Delete (with --cleanup)"

    return "-> Restart"


def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
) -> None:
    """Print status table to stdout.

    Args:
        sessions: Current sessions from JSON
        eligible_issues: Eligible issues not yet in sessions (repo_name, issue)
        repo_filter: Optional repo name filter
        cached_issues_by_repo: Dict mapping repo_full_name to issues dict.
                               If provided, avoids API calls for staleness checks.
        issues_without_branch: Set of (repo_full_name, issue_number) tuples
                               for issues that require but lack a linked branch.
                               Used to show "-> Needs branch" indicator.

    Columns:
    - Repo
    - Issue
    - Status
    - Folder
    - Git (Clean/Dirty/Missing/No Git/Error)
    - VSCode
    - Next Action
    """
    # Refresh caches once for all sessions (window cache is fast, process cache is slow)
    clear_vscode_window_cache()
    clear_vscode_process_cache()

    # Build table rows
    headers = ["Repo", "Issue", "Status", "Folder", "Git", "VSCode", "Next Action"]
    rows: list[list[str]] = []

    # Track session issue keys to identify eligible issues not in sessions
    session_keys: set[tuple[str, int]] = set()

    # Print session rows
    for session in sessions:
        repo_full = session["repo"]

        # Get cached issues for this repo (if available)
        repo_cached_issues: dict[int, IssueData] | None = None
        if cached_issues_by_repo:
            repo_cached_issues = cached_issues_by_repo.get(repo_full)

        # Check closed state and folder existence
        folder_path = Path(session["folder"])
        is_closed = is_issue_closed(session, cached_issues=repo_cached_issues)

        # Skip closed issues if folder doesn't exist (nothing to clean up)
        if is_closed and not folder_path.exists():
            logger.debug(
                "Skipping closed issue #%d with missing folder",
                session["issue_number"],
            )
            continue

        repo_short = repo_full.split("/")[-1] if "/" in repo_full else repo_full

        # Apply repo filter
        if repo_filter and repo_short != repo_filter:
            continue

        folder_name = folder_path.name
        issue_num = f"#{session['issue_number']}"
        status = session["status"]

        # Add "(Closed)" prefix for closed issues
        if is_closed:
            status = f"(Closed) {status}"

        is_running = is_session_active(session)

        is_dirty = check_folder_dirty(folder_path) if folder_path.exists() else False
        git_status = (
            get_folder_git_status(folder_path) if folder_path.exists() else "Missing"
        )

        # Get current status for eligibility check
        # Use cached status if available, fall back to session status
        if repo_cached_issues is not None:
            current_status, _ = get_issue_current_status(
                session["issue_number"], cached_issues=repo_cached_issues
            )
            status_for_eligibility = current_status or session["status"]
        else:
            # No cache available - use session's recorded status
            status_for_eligibility = session["status"]
        is_eligible = is_status_eligible_for_session(status_for_eligibility)

        # Compute is_stale: closed OR ineligible OR status changed
        # Only check status_changed for open issues to avoid warning
        if is_closed:
            stale = True
        else:
            status_changed = is_session_stale(session, cached_issues=repo_cached_issues)
            stale = not is_eligible or status_changed

        vscode_status = "Running" if is_running else "Closed"
        action = get_next_action(stale, is_dirty, is_running)

        # Show status change indicator (but not for closed issues which already have prefix)
        if stale and not is_closed:
            status = f"-> {status}"

        # Add row to table
        rows.append(
            [
                repo_short,
                issue_num,
                status,
                folder_name,
                git_status,
                vscode_status,
                action,
            ]
        )

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
        status = get_issue_status(issue)

        # Check if issue needs branch but doesn't have one
        # Must check BOTH: status requires branch AND issue lacks one
        needs_branch = (
            status_requires_linked_branch(status)
            and issues_without_branch is not None
            and (repo_name, issue["number"]) in issues_without_branch
        )

        if needs_branch:
            action = "-> Needs branch"
        else:
            action = "-> Create and start"

        # Add row to table
        rows.append([repo_short, issue_num, status, "-", "-", "-", action])

    # Print table
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
        print("No sessions or eligible issues found.")
