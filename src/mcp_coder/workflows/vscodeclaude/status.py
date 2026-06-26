"""Status display and staleness checking for vscodeclaude feature."""

import logging
from pathlib import Path

from tabulate import tabulate

from ...mcp_workspace_github import IssueData, IssueManager
from ...utils.subprocess_runner import CommandOptions, execute_subprocess
from .helpers import get_issue_status, load_to_be_deleted
from .issues import is_status_eligible_for_session, status_requires_linked_branch
from .types import SessionAction, SessionAssessment, VSCodeClaudeSession

logger = logging.getLogger(__name__)

# Static mapping from a decided ``SessionAction`` to its status-table label.
# ``SKIP`` is excluded: it renders ``!! <reason>`` from ``decision.reason`` so the
# specific skip cause (dirty / unverified non-empty) is surfaced.
ACTION_DISPLAY: dict[SessionAction, str] = {
    SessionAction.KEEP_ACTIVE: "(active)",
    SessionAction.RESTART: "-> Restart",
    SessionAction.DELETE: "-> Delete (with --cleanup)",
    SessionAction.REMOVE_MISSING: "-> Remove",
    SessionAction.INVESTIGATE_ZOMBIE: "-> Investigate zombie",
}


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

    Raises:
        ValueError: If neither cached_issues nor issue_manager is provided.
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
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
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
    except (
        Exception
    ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        return "No Git"

    # Check for changes
    try:
        result = execute_subprocess(["git", "status", "--porcelain"], options)
        return "Dirty" if result.stdout.strip() else "Clean"
    except (
        Exception
    ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
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
    workspace_base: str,
    assessments: dict[str, SessionAssessment],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
) -> None:
    """Print status table to stdout.

    Status is the always-on transparency surface and the 5th consumer of the
    assessment pipeline. Each session row renders its prebuilt
    :class:`SessionAssessment` (verdict + decision) instead of recomputing
    liveness / staleness / closed / next-action (R1), so the enriched
    ``VSCode``/``Next Action`` columns cannot drift from cleanup, restart, audit,
    or ``--explain``. WRITE-FREE: this path performs no ``sessions.json`` writes
    (the PID refresh + ``last_active`` advance live in ``apply_assessments``).

    Args:
        sessions: Current sessions from JSON
        eligible_issues: Eligible issues not yet in sessions (repo_name, issue)
        workspace_base: Path to workspace directory (for soft-delete filtering)
        assessments: Folder-path -> :class:`SessionAssessment` map built once per
            run by ``build_assessments``. Session rows read this; the eligible
            issues below have no assessment and keep using ``get_next_action``.
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
    - VSCode (enriched with the winning liveness rule)
    - Next Action
    """
    # Load soft-delete registry to filter out deleted sessions
    to_be_deleted = load_to_be_deleted(workspace_base)

    # Build table rows
    headers = ["Repo", "Issue", "Status", "Folder", "Git", "VSCode", "Next Action"]
    rows: list[list[str]] = []

    # Track session issue keys to identify eligible issues not in sessions
    session_keys: set[tuple[str, int]] = set()

    # Print session rows
    for session in sessions:
        folder_path = Path(session["folder"])

        # Skip soft-deleted sessions
        if folder_path.name in to_be_deleted:
            continue

        # Read the prebuilt assessment; never recompute liveness/staleness here.
        assessment = assessments.get(session["folder"])
        if assessment is None:
            # No assessment was built for this session (e.g. status was invoked
            # without one) - nothing to render.
            continue

        is_open = assessment.issue_state.is_open
        is_running = assessment.verdict.active
        folder_exists = assessment.signals.folder_exists

        # Skip closed issues with missing folder UNLESS a process still claims
        # the slot (zombie state - surface it for diagnosis).
        if not is_open and not is_running and not folder_exists:
            logger.debug(
                "Skipping closed issue #%d with missing folder",
                session["issue_number"],
            )
            continue

        repo_full = session["repo"]
        repo_short = repo_full.split("/")[-1] if "/" in repo_full else repo_full

        # Apply repo filter
        if repo_filter and repo_short != repo_filter:
            continue

        folder_name = folder_path.name
        issue_num = f"#{session['issue_number']}"
        status = session["status"]

        # Status column: (Closed) prefix for closed issues, else show the current
        # GitHub status when the stored status is stale (status changed).
        if not is_open:
            status = f"(Closed) {status}"
        elif assessment.issue_state.is_stale:
            status = f"-> {assessment.issue_state.stale_target or status}"

        # Git column is informational only and stays write-free.
        git_status = get_folder_git_status(folder_path)

        decided_action = assessment.decision.action

        # VSCode column: enrich with the winning liveness rule.
        if decided_action == SessionAction.INVESTIGATE_ZOMBIE:
            vscode_status = "Running (zombie)"
        elif is_running:
            vscode_status = f"Running ({assessment.verdict.rule.value})"
        else:
            vscode_status = f"Closed ({assessment.verdict.rule.value})"

        # Next Action column: derived from the decided action; SKIP surfaces its
        # reason so the user sees why the session was held back.
        if decided_action == SessionAction.SKIP:
            next_action = f"!! {assessment.decision.reason}"
        else:
            next_action = ACTION_DISPLAY[decided_action]

        # Add row to table
        rows.append(
            [
                repo_short,
                issue_num,
                status,
                folder_name,
                git_status,
                vscode_status,
                next_action,
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
        elif not is_status_eligible_for_session(status):
            action = "(awaiting merge)"
        else:
            action = "-> Create and start"

        # Add row to table
        rows.append([repo_short, issue_num, status, "-", "-", "-", action])

    # Print table
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
        print("No sessions or eligible issues found.")
