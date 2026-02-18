import logging
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

from ...utils.github_operations.issues import (
    IssueBranchManager,
    IssueData,
    IssueManager,
    get_all_cached_issues,
)
from ...utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    execute_subprocess,
)
from ...utils.user_config import get_cache_refresh_minutes
from .config import _get_configured_repos  # ← already in config.py after Step 2
from .helpers import get_issue_status, truncate_title
from .issues import (
    get_ignore_labels,
    get_linked_branch_for_issue,
    get_matching_ignore_label,
    is_status_eligible_for_session,
    status_requires_linked_branch,
)
from .session_launch import (  # ← cross-module import
    launch_vscode,
    regenerate_session_files,
)
from .sessions import (
    clear_vscode_process_cache,
    clear_vscode_window_cache,
    is_session_active,
    is_vscode_open_for_folder,
    load_sessions,
    update_session_pid,
    update_session_status,
)
from .status import get_folder_git_status
from .types import VSCodeClaudeSession

logger = logging.getLogger(__name__)


class BranchPrepResult(NamedTuple):
    """Result of branch preparation for session restart."""

    should_proceed: bool
    skip_reason: str | None = None
    branch_name: str | None = None


__all__ = [
    "restart_closed_sessions",
    "handle_pr_created_issues",
]


def _prepare_restart_branch(
    folder_path: Path,
    current_status: str,
    branch_manager: IssueBranchManager,
    issue_number: int,
) -> BranchPrepResult:
    """Prepare branch for session restart.

    Handles git fetch, branch verification, dirty check, and checkout.

    Args:
        folder_path: Path to the git repository
        current_status: Current issue status label
        branch_manager: IssueBranchManager for GitHub API calls
        issue_number: GitHub issue number

    Returns:
        BranchPrepResult with:
        - should_proceed: True if restart can continue
        - skip_reason: None if success, else "No branch"/"Dirty"/"Git error"/"Multi-branch"
        - branch_name: Branch name if switched, None if staying on current
    """
    # 1. Always run git fetch origin (fatal if fails)
    try:
        options = CommandOptions(cwd=str(folder_path), check=True)
        execute_subprocess(["git", "fetch", "origin"], options)
    except CalledProcessError as e:
        logger.error("git fetch failed for %s: %s", folder_path, e)
        return BranchPrepResult(False, "Git error", None)

    # 2. If status doesn't require branch, return success (stay on current branch)
    if not status_requires_linked_branch(current_status):
        return BranchPrepResult(True, None, None)

    # 3. Get linked branch from GitHub
    try:
        linked_branch = get_linked_branch_for_issue(branch_manager, issue_number)
    except ValueError:
        # Multiple branches linked to issue
        return BranchPrepResult(False, "Multi-branch", None)

    if not linked_branch:
        return BranchPrepResult(False, "No branch", None)

    # 4. Check if repo is dirty
    git_status = get_folder_git_status(folder_path)
    if git_status == "Dirty":
        return BranchPrepResult(False, "Dirty", None)

    # 5. Checkout and pull
    try:
        options = CommandOptions(cwd=str(folder_path), check=True)
        execute_subprocess(["git", "checkout", linked_branch], options)
        execute_subprocess(["git", "pull"], options)
    except CalledProcessError as e:
        logger.error("Git operation failed: %s", e)
        return BranchPrepResult(False, "Git error", None)

    return BranchPrepResult(True, None, linked_branch)


def _build_cached_issues_by_repo(
    sessions: list[VSCodeClaudeSession],
) -> dict[str, dict[int, IssueData]]:
    """Build cached issues dict for all repos with sessions.

    Fetches issues from cache with additional_issues parameter to ensure
    closed issues from existing sessions are included.

    Args:
        sessions: List of all sessions

    Returns:
        Dict mapping repo_full_name to dict of issues (issue_number -> IssueData)
        Returns empty dict if GitHub token is not configured (e.g., in test contexts)
    """
    # Early return if no sessions
    if not sessions:
        logger.debug("No sessions to build cache for")
        return {}

    logger.debug(
        "Building cache for %d sessions",
        len(sessions),
    )

    # Group sessions by repo
    sessions_by_repo: dict[str, list[int]] = defaultdict(list)
    for session in sessions:
        sessions_by_repo[session["repo"]].append(session["issue_number"])

    logger.debug(
        "Grouped sessions into %d repos: %s",
        len(sessions_by_repo),
        {repo: len(issues) for repo, issues in sessions_by_repo.items()},
    )

    # Fetch cached issues for each repo with session issue numbers
    cached_issues_by_repo: dict[str, dict[int, IssueData]] = {}
    for repo_full_name, issue_numbers in sessions_by_repo.items():
        logger.debug(
            "Fetching cache for %s with additional_issues=%s",
            repo_full_name,
            issue_numbers,
        )
        try:
            repo_url = f"https://github.com/{repo_full_name}"
            issue_manager = IssueManager(repo_url=repo_url)

            # Fetch with additional_issues to include closed session issues
            all_issues = get_all_cached_issues(
                repo_full_name=repo_full_name,
                issue_manager=issue_manager,
                force_refresh=False,
                cache_refresh_minutes=get_cache_refresh_minutes(),
                additional_issues=issue_numbers,  # ← KEY CHANGE
            )

            logger.debug(
                "Retrieved %d total issues for %s (including session issues)",
                len(all_issues),
                repo_full_name,
            )

            # Convert to dict for fast lookup
            cached_issues_by_repo[repo_full_name] = {
                issue["number"]: issue for issue in all_issues
            }
        except ValueError as e:
            # GitHub token not configured - return empty dict for this repo
            # This is expected in test contexts where token may not be set
            logger.warning(
                "Failed to build cache for %s (likely missing GitHub token): %s",
                repo_full_name,
                e,
            )
            # Return empty dict - tests will provide cached_issues_by_repo parameter
            return {}

    logger.debug(
        "Built cache for %d repos with session issues",
        len(cached_issues_by_repo),
    )

    return cached_issues_by_repo


def restart_closed_sessions(
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
) -> list[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.

    Args:
        cached_issues_by_repo: Dict mapping repo_full_name to issues dict.
                               If provided, avoids API calls for staleness checks
                               and file regeneration.

    Finds sessions where:
    - VSCode PID no longer running
    - Issue status unchanged (not stale)
    - Folder still exists
    - Repo is still configured in config file
    - Issue is still open (closed issues are skipped)

    Before restarting, regenerates all session files with fresh issue data.

    Returns:
        List of restarted sessions
    """
    from .sessions import remove_session

    store = load_sessions()

    # Early return if no sessions
    if not store["sessions"]:
        logger.debug("No sessions to restart")
        return []

    # Build cache with session issues if not provided
    if cached_issues_by_repo is None:
        cached_issues_by_repo = _build_cached_issues_by_repo(store["sessions"])

    restarted: list[VSCodeClaudeSession] = []

    # Refresh caches once for all sessions (window cache is fast, process cache is slow)
    clear_vscode_window_cache()
    clear_vscode_process_cache()

    # Load configured repos from config file (fresh read on each start)
    configured_repos = _get_configured_repos()
    logger.debug("Configured repos from config: %s", configured_repos)

    # Load ignore labels once for all sessions
    ignore_labels = get_ignore_labels()

    for session in store["sessions"]:
        folder_path = Path(session["folder"])

        # Use is_session_active() for consistent detection across all callers.
        # Also run cmdline check separately to update stored PID if it changed
        # (avoids slow scan on next run).
        if is_session_active(session):
            _, found_pid = is_vscode_open_for_folder(session["folder"])
            if found_pid and found_pid != session.get("vscode_pid"):
                update_session_pid(session["folder"], found_pid)
            continue

        # Check if folder exists
        if not folder_path.exists():
            # Remove orphaned session
            remove_session(session["folder"])
            logger.info(
                "Removed orphaned session for issue #%d (folder missing)",
                session["issue_number"],
            )
            continue

        # Check if repo is still configured (skip sessions for unconfigured repos)
        repo_full_name = session["repo"]
        if repo_full_name not in configured_repos:
            logger.info(
                "Skipping session for issue #%d: repo %s not in config",
                session["issue_number"],
                repo_full_name,
            )
            continue

        # Get cached issues for this repo (if available)
        repo_cached_issues: dict[int, IssueData] | None = None
        if cached_issues_by_repo is not None:
            repo_cached_issues = cached_issues_by_repo.get(repo_full_name)

        # Get issue data from cache or fetch through caching layer
        issue_number = session["issue_number"]
        repo_url = f"https://github.com/{repo_full_name}"

        try:
            if repo_cached_issues and issue_number in repo_cached_issues:
                issue = repo_cached_issues[issue_number]
            else:
                # Issue missing from cache — unexpected, since _build_cached_issues_by_repo
                # uses additional_issues to include all session issues.
                # Fetch through the caching layer to populate and avoid double API calls.
                logger.warning(
                    "Issue #%d missing from cache for %s, fetching individually",
                    issue_number,
                    repo_full_name,
                )
                issue_manager = IssueManager(repo_url=repo_url)
                fetched = get_all_cached_issues(
                    repo_full_name=repo_full_name,
                    issue_manager=issue_manager,
                    additional_issues=[issue_number],
                )
                fetched_dict: dict[int, IssueData] = {i["number"]: i for i in fetched}
                if cached_issues_by_repo is not None:
                    cached_issues_by_repo[repo_full_name] = fetched_dict
                repo_cached_issues = fetched_dict
                if issue_number not in fetched_dict:
                    logger.warning(
                        "Failed to fetch issue #%d, skipping restart",
                        issue_number,
                    )
                    continue
                issue = fetched_dict[issue_number]

            if issue["number"] == 0:
                logger.warning(
                    "Failed to fetch issue #%d, skipping file regeneration",
                    issue_number,
                )
                continue

            # Skip closed issues for restart (they shouldn't be restarted)
            # but they should still appear in status display with (Closed) marker
            if issue["state"] != "open":
                logger.info("Skipping closed issue #%d for restart", issue_number)
                continue

            # Check if status is eligible for session
            current_status = get_issue_status(issue)
            if not is_status_eligible_for_session(current_status):
                logger.info(
                    "Skipping issue #%d: status %s doesn't need session",
                    issue_number,
                    current_status,
                )
                continue

            # Check if issue has ignore label (blocked/wait)
            blocked_label = get_matching_ignore_label(issue["labels"], ignore_labels)
            if blocked_label:
                logger.info(
                    "Skipping blocked session for issue #%d (label: %s)",
                    issue_number,
                    blocked_label,
                )
                continue

            # Update session status if changed (current_status already computed above)
            if current_status != session["status"]:
                update_session_status(session["folder"], current_status)
                logger.debug(
                    "Updated session status for #%d: %s -> %s",
                    issue_number,
                    session["status"],
                    current_status,
                )

            # Branch preparation: fetch, check, switch if needed
            branch_manager = IssueBranchManager(repo_url=repo_url)
            branch_result = _prepare_restart_branch(
                folder_path=folder_path,
                current_status=current_status,
                branch_manager=branch_manager,
                issue_number=issue_number,
            )

            if not branch_result.should_proceed:
                logger.warning(
                    "Skipping restart for issue #%d: %s",
                    issue_number,
                    branch_result.skip_reason,
                )
                continue

            # Regenerate all session files with fresh data
            regenerate_session_files(session, issue)

        except Exception as e:
            logger.warning(
                "Failed to regenerate files for issue #%d: %s",
                issue_number,
                str(e),
            )

        # Find the workspace file
        workspace_base = folder_path.parent
        folder_name = folder_path.name
        workspace_file = workspace_base / f"{folder_name}.code-workspace"

        if not workspace_file.exists():
            logger.warning(
                "Workspace file missing for session #%d: %s",
                session["issue_number"],
                workspace_file,
            )
            continue

        # Relaunch VSCode
        try:
            new_pid = launch_vscode(workspace_file)
            update_session_pid(session["folder"], new_pid)
            logger.debug(
                "Restarted VSCode for issue #%d (PID: %d)",
                session["issue_number"],
                new_pid,
            )

            # Update session with new PID for return value
            updated_session: VSCodeClaudeSession = {
                "folder": session["folder"],
                "repo": session["repo"],
                "issue_number": session["issue_number"],
                "status": session["status"],
                "vscode_pid": new_pid,
                "started_at": session["started_at"],
                "is_intervention": session.get("is_intervention", False),
            }
            restarted.append(updated_session)

        except Exception as e:
            logger.error(
                "Failed to restart session for issue #%d: %s",
                session["issue_number"],
                str(e),
            )

    return restarted


def handle_pr_created_issues(issues: list[IssueData]) -> None:
    """Display PR URLs for status-10:pr-created issues.

    Args:
        issues: Issues with status-10:pr-created

    Prints issue URLs to stdout (no session created).
    The issue URL typically links to the PR for pr-created issues.
    """
    if not issues:
        return

    print("\n" + "=" * 60)
    print("PR-CREATED ISSUES (no session needed)")
    print("=" * 60)

    for issue in issues:
        issue_number = issue["number"]
        title = truncate_title(issue["title"], 40)
        issue_url = issue.get("url", "N/A")

        print(f"  #{issue_number}: {title}")
        print(f"    Issue: {issue_url}")

    print("=" * 60 + "\n")
