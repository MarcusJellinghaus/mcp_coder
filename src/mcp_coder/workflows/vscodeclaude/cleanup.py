"""Cleanup functions for vscodeclaude feature."""

import logging
from pathlib import Path

from ...utils.folder_deletion import (
    DeletionFailureReason,
    DeletionResult,
    _is_directory_empty,
    safe_delete_folder,
)
from ...utils.github_operations.issues import IssueData, IssueManager
from ...utils.github_operations.issues.cache import get_all_cached_issues
from .issues import (
    get_ignore_labels,
    get_matching_ignore_label,
    is_status_eligible_for_session,
)
from .orchestrator import _get_configured_repos
from .sessions import (
    is_session_active,
    load_sessions,
    remove_session,
)
from .status import get_folder_git_status, is_session_stale
from .types import VSCodeClaudeSession

logger = logging.getLogger(__name__)


def get_stale_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[tuple[VSCodeClaudeSession, str]]:
    """Get stale sessions with git status.

    Only checks sessions for repos that are still configured.
    Includes sessions that are:
    - Stale (status changed)
    - Blocked (has ignore labels like blocked/wait)
    - Closed (issue state is closed)
    - Ineligible (bot statuses or pr-created - no initial_command)

    Args:
        cached_issues_by_repo: Optional cache of issues for state/blocked/eligibility detection

    Returns:
        List of (session, git_status) tuples where git_status is one of:
        "Clean", "Dirty", "Missing", "No Git", "Error"
    """
    store = load_sessions()
    stale_sessions: list[tuple[VSCodeClaudeSession, str]] = []

    # Load configured repos (skip sessions for repos no longer in config)
    configured_repos = _get_configured_repos()

    # Load ignore labels for blocked detection
    ignore_labels = get_ignore_labels()

    for session in store["sessions"]:
        # Skip sessions with running VSCode, but only when session artifacts exist.
        # If both the folder and workspace file are gone, the VSCode process is a
        # zombie (launched for this session but kept running after its files were
        # deleted). Don't let a zombie process block cleanup.
        if is_session_active(session):
            continue

        # Skip sessions for unconfigured repos
        repo_full_name = session["repo"]
        if repo_full_name not in configured_repos:
            logger.debug(
                "Skipping stale check for issue #%d: repo %s not in config",
                session["issue_number"],
                repo_full_name,
            )
            continue

        # Check issue state, blocked label, and eligibility from cache
        is_blocked = False
        is_closed = False
        is_ineligible = False
        issue_number = session["issue_number"]
        cached_for_stale_check: dict[int, IssueData] | None = None
        if cached_issues_by_repo:
            repo_issues = cached_issues_by_repo.get(repo_full_name, {})
            if issue_number not in repo_issues:
                # Issue missing from cache — unexpected, since _build_cached_issues_by_repo
                # uses additional_issues to include all session issues.
                # Fetch through the caching layer to populate and avoid double API calls.
                logger.warning(
                    "Issue #%d missing from cache for %s, fetching individually",
                    issue_number,
                    repo_full_name,
                )
                try:
                    repo_url = f"https://github.com/{repo_full_name}"
                    issue_manager = IssueManager(repo_url=repo_url)
                    fetched = get_all_cached_issues(
                        repo_full_name=repo_full_name,
                        issue_manager=issue_manager,
                        additional_issues=[issue_number],
                    )
                    fetched_dict: dict[int, IssueData] = {
                        i["number"]: i for i in fetched
                    }
                    cached_issues_by_repo[repo_full_name] = fetched_dict
                    repo_issues = fetched_dict
                except Exception:
                    logger.debug(
                        "Failed to fetch issue #%d individually; skipping eligibility checks",
                        issue_number,
                    )
            if issue_number in repo_issues:
                issue = repo_issues[issue_number]
                # Check if issue is closed
                is_closed = issue["state"] == "closed"
                # Check for blocked label
                blocked_label = get_matching_ignore_label(
                    issue["labels"], ignore_labels
                )
                if blocked_label:
                    is_blocked = True
                # Check if current status is eligible for session
                # Get status from issue labels (most current)
                status_labels = [
                    lbl for lbl in issue["labels"] if lbl.startswith("status-")
                ]
                if status_labels:
                    current_status = status_labels[0]
                    is_ineligible = not is_status_eligible_for_session(current_status)
                # Only pass cache to is_session_stale when issue is in it
                # (passing cache with a missing issue causes ValueError in fallback)
                cached_for_stale_check = repo_issues

        # Check if session is stale, blocked, closed, or ineligible
        # Check is_closed first to short-circuit and avoid calling is_session_stale
        # on closed issues (which would trigger a spurious warning)
        if (
            is_closed
            or is_blocked
            or is_ineligible
            or is_session_stale(session, cached_issues=cached_for_stale_check)
        ):
            folder_path = Path(session["folder"])
            git_status = get_folder_git_status(folder_path)
            stale_sessions.append((session, git_status))

    return stale_sessions


def delete_session_folder(session: VSCodeClaudeSession) -> bool:
    """Delete session folder and remove from session store.

    Args:
        session: Session to delete

    Returns:
        True if successfully deleted

    Uses safe_delete_folder for robust folder deletion.
    """
    folder_path = Path(session["folder"])

    try:
        # Use safe_delete_folder for robust folder deletion
        if folder_path.exists():
            deletion = safe_delete_folder(folder_path)
            if not deletion.success:
                if deletion.reason == DeletionFailureReason.LOCKED_EMPTY_DIR:
                    logger.error(
                        "Failed to delete session folder - directory is empty "
                        "but locked by Windows (close Explorer or any app with "
                        "a window open to this folder, then retry): %s",
                        deletion.detail or folder_path,
                    )
                else:
                    reason_label = (
                        deletion.reason.value if deletion.reason else "unknown"
                    )
                    logger.error(
                        "Failed to delete session folder (%s): %s",
                        reason_label,
                        deletion.detail or folder_path,
                    )
                return False
            logger.info("Deleted folder: %s", folder_path)

        # Also delete the workspace file if it exists
        workspace_base = folder_path.parent
        workspace_file = workspace_base / f"{folder_path.name}.code-workspace"
        if workspace_file.exists():
            workspace_file.unlink()
            logger.info("Deleted workspace file: %s", workspace_file)

        # Remove session from store
        remove_session(session["folder"])

        return True
    except Exception as e:
        logger.error("Failed to delete session folder %s: %s", folder_path, e)
        return False


def cleanup_stale_sessions(
    dry_run: bool = True,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> dict[str, list[str]]:
    """Clean up stale session folders.

    Args:
        dry_run: If True, only report what would be deleted
        cached_issues_by_repo: Optional cache for blocked detection

    Returns:
        Dict with "deleted" and "skipped" folder lists

    Behavior by status:
    - Clean: delete folder and session
    - Dirty: skip with warning (uncommitted changes)
    - Missing: remove session only (folder already gone)
    - No Git / Error: skip with warning (investigate manually)
    """
    result: dict[str, list[str]] = {"deleted": [], "skipped": []}

    stale_sessions = get_stale_sessions(cached_issues_by_repo=cached_issues_by_repo)

    for session, git_status in stale_sessions:
        folder = session["folder"]

        if git_status == "Clean":
            # Clean folder - delete or report
            if dry_run:
                print(f"Add --cleanup to delete: {folder}")
                # Don't add to deleted list in dry run - it wasn't actually deleted
            else:
                if delete_session_folder(session):
                    print(f"Deleted: {folder}")
                    result["deleted"].append(folder)
                else:
                    print(f"Failed to delete: {folder}")
                    result["skipped"].append(folder)

        elif git_status == "Missing":
            # Folder gone, just remove session record
            if dry_run:
                print(f"Would remove session (folder missing): {folder}")
            else:
                remove_session(folder)
                print(f"Removed session (folder missing): {folder}")
                result["deleted"].append(folder)

        elif git_status == "Dirty":
            # Skip - has uncommitted changes
            logger.warning("Skipping dirty folder: %s", folder)
            print(f"[WARN] Skipping (dirty): {folder}")
            result["skipped"].append(folder)

        else:  # "No Git" or "Error"
            folder_path = Path(folder)
            if _is_directory_empty(folder_path):
                # Empty folder — safe to delete regardless of git status
                if dry_run:
                    print(f"Add --cleanup to delete: {folder}")
                else:
                    if delete_session_folder(session):
                        print(f"Deleted: {folder}")
                        result["deleted"].append(folder)
                    else:
                        print(f"Failed to delete: {folder}")
                        result["skipped"].append(folder)
            else:
                # Non-empty — needs manual investigation
                logger.warning("Skipping folder (%s): %s", git_status.lower(), folder)
                print(f"[WARN] Skipping ({git_status.lower()}): {folder}")
                result["skipped"].append(folder)

    if not stale_sessions:
        print("No stale sessions to clean up.")

    return result
