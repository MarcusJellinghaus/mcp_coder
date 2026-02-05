"""Session orchestration for vscodeclaude feature.

Main functions for preparing, launching, and managing sessions.
"""

import logging
import platform
import shutil
from pathlib import Path

from ...utils.github_operations.issue_branch_manager import IssueBranchManager
from ...utils.github_operations.issue_cache import get_all_cached_issues
from ...utils.github_operations.issue_manager import IssueData, IssueManager
from ...utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    execute_subprocess,
    launch_process,
)
from ...utils.user_config import get_cache_refresh_minutes, load_config
from .config import get_github_username, load_repo_vscodeclaude_config
from .helpers import (
    build_session,
    get_issue_status,
    get_repo_full_name,
    get_repo_short_name,
    get_repo_short_name_from_full,
    get_stage_display_name,
    truncate_title,
)
from .issues import (
    _filter_eligible_vscodeclaude_issues,
    get_ignore_labels,
    get_linked_branch_for_issue,
    get_matching_ignore_label,
)
from .sessions import (
    add_session,
    check_vscode_running,
    clear_vscode_process_cache,
    clear_vscode_window_cache,
    get_active_session_count,
    get_session_for_issue,
    is_vscode_open_for_folder,
    is_vscode_window_open_for_folder,
    load_sessions,
    update_session_pid,
    update_session_status,
)
from .status import is_session_stale
from .types import (
    DEFAULT_PROMPT_TIMEOUT,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
)
from .workspace import (
    _remove_readonly,
    create_startup_script,
    create_status_file,
    create_vscode_task,
    create_working_folder,
    create_workspace_file,
    get_working_folder_path,
    run_setup_commands,
    setup_git_repo,
    update_gitignore,
    validate_mcp_json,
    validate_setup_commands,
)

logger = logging.getLogger(__name__)

__all__ = [
    # Main orchestration functions
    "launch_vscode",
    "prepare_and_launch_session",
    "process_eligible_issues",
    "regenerate_session_files",
    "restart_closed_sessions",
    "handle_pr_created_issues",
    # Re-exported from helpers for backward compatibility
    "get_stage_display_name",
    "truncate_title",
]


def launch_vscode(workspace_file: Path) -> int:
    """Launch VSCode with workspace file.

    Args:
        workspace_file: Path to .code-workspace file

    Returns:
        VSCode process PID

    Uses launch_process for non-blocking launch.
    On Windows, uses shell=True to find code.cmd in PATH.
    """
    is_windows = platform.system() == "Windows"

    if is_windows:
        # On Windows, 'code' is a .cmd file which requires shell=True
        return launch_process(f'code "{workspace_file}"', shell=True)
    else:
        return launch_process(["code", str(workspace_file)])


def prepare_and_launch_session(
    issue: IssueData,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    repo_vscodeclaude_config: RepoVSCodeClaudeConfig,
    branch_name: str | None,
    is_intervention: bool = False,
) -> VSCodeClaudeSession:
    """Full session preparation and launch.

    Args:
        issue: GitHub issue data
        repo_config: Repository config (repo_url, etc.)
        vscodeclaude_config: VSCodeClaude config (workspace_base, etc.)
        repo_vscodeclaude_config: Per-repo setup commands
        branch_name: Branch to checkout (None = main)
        is_intervention: If True, intervention mode

    Returns:
        Created session data

    Raises:
        FileNotFoundError: If .mcp.json missing
        CalledProcessError: If git or setup fails

    Steps:
    1. Create working folder
    2. Setup git repo
    3. Validate .mcp.json
    4. Run setup commands (if configured) - validates commands first
    5. Update .gitignore
    6. Create workspace file
    7. Create startup script
    8. Create VSCode task
    9. Create status file
    10. Launch VSCode
    11. Create and save session

    On failure after folder creation: cleans up working folder.
    """
    workspace_base = vscodeclaude_config["workspace_base"]
    repo_url = repo_config.get("repo_url", "")
    repo_short_name = get_repo_short_name(repo_config)
    repo_full_name = get_repo_full_name(repo_config)
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_url = issue.get("url", "")
    status = get_issue_status(issue)

    # Build folder path
    folder_path = get_working_folder_path(workspace_base, repo_short_name, issue_number)
    folder_str = str(folder_path)

    # Create working folder
    create_working_folder(folder_path)

    try:
        # Setup git repo
        setup_git_repo(folder_path, repo_url, branch_name)

        # Validate .mcp.json
        validate_mcp_json(folder_path)

        # Run setup commands if configured
        is_windows = platform.system() == "Windows"
        if is_windows:
            setup_commands = repo_vscodeclaude_config.get("setup_commands_windows", [])
        else:
            setup_commands = repo_vscodeclaude_config.get("setup_commands_linux", [])

        if setup_commands:
            validate_setup_commands(setup_commands)
            run_setup_commands(folder_path, setup_commands)

        # Update .gitignore
        update_gitignore(folder_path)

        # Create workspace file
        folder_name = folder_path.name
        workspace_file = create_workspace_file(
            workspace_base=workspace_base,
            folder_name=folder_name,
            issue_number=issue_number,
            issue_title=issue_title,
            status=status,
            repo_name=repo_short_name,
        )

        # Create startup script
        script_path = create_startup_script(
            folder_path=folder_path,
            issue_number=issue_number,
            issue_title=issue_title,
            status=status,
            repo_name=repo_short_name,
            issue_url=issue_url,
            is_intervention=is_intervention,
            timeout=DEFAULT_PROMPT_TIMEOUT,
        )

        # Create VSCode task
        create_vscode_task(folder_path, script_path)

        # Create status file
        create_status_file(
            folder_path=folder_path,
            issue_number=issue_number,
            issue_title=issue_title,
            status=status,
            repo_full_name=repo_full_name,
            branch_name=branch_name or "main",
            issue_url=issue_url,
            is_intervention=is_intervention,
        )

        # Launch VSCode
        pid = launch_vscode(workspace_file)

        # Build and save session
        session = build_session(
            folder=folder_str,
            repo=repo_full_name,
            issue_number=issue_number,
            status=status,
            vscode_pid=pid,
            is_intervention=is_intervention,
        )
        add_session(session)

        logger.info(
            "Started session for issue #%d in %s",
            issue_number,
            folder_str,
        )

        return session

    except Exception:
        # Cleanup working folder on failure
        if folder_path.exists():
            try:
                shutil.rmtree(folder_path, onerror=_remove_readonly)
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to cleanup folder %s: %s",
                    folder_path,
                    cleanup_error,
                )
        raise


def process_eligible_issues(
    repo_name: str,
    repo_config: dict[str, str],
    vscodeclaude_config: VSCodeClaudeConfig,
    max_sessions: int,
    repo_filter: str | None = None,
) -> list[VSCodeClaudeSession]:
    """Process eligible issues for a repository.

    Args:
        repo_name: Repository config name
        repo_config: Repository config
        vscodeclaude_config: VSCodeClaude config
        max_sessions: Maximum concurrent sessions
        repo_filter: Optional repo filter (skip if doesn't match)

    Returns:
        List of sessions that were started

    Handles:
    - Checking current session count
    - Getting eligible issues
    - Skipping issues with existing sessions
    - Starting new sessions up to max
    """
    # Apply repo filter if provided
    if repo_filter and repo_name != repo_filter:
        return []

    # Check current session count
    current_count = get_active_session_count()
    if current_count >= max_sessions:
        logger.info(
            "Already at max sessions (%d/%d), skipping",
            current_count,
            max_sessions,
        )
        return []

    # Get GitHub username
    github_username = get_github_username()

    # Get repo full name for session lookup
    repo_full_name = get_repo_full_name(repo_config)

    # Create managers using direct imports
    # Build repo_url from repo_full_name for proper instantiation
    repo_url = f"https://github.com/{repo_full_name}"
    logger.debug(
        "process_eligible_issues: processing repo %s (url: %s)",
        repo_full_name,
        repo_url,
    )
    issue_manager = IssueManager(repo_url=repo_url)
    branch_manager = IssueBranchManager(repo_url=repo_url)

    # Get all cached issues and filter for vscodeclaude eligibility
    all_cached_issues = get_all_cached_issues(
        repo_full_name=repo_full_name,
        issue_manager=issue_manager,
        force_refresh=False,
        cache_refresh_minutes=get_cache_refresh_minutes(),
    )
    eligible_issues = _filter_eligible_vscodeclaude_issues(
        all_cached_issues, github_username
    )

    # Filter out pr-created issues (they don't need sessions)
    actionable_issues: list[IssueData] = [
        issue
        for issue in eligible_issues
        if get_issue_status(issue) != "status-10:pr-created"
    ]

    # Filter out issues that already have sessions
    issues_to_start: list[IssueData] = []
    for issue in actionable_issues:
        existing = get_session_for_issue(repo_full_name, issue["number"])
        if existing is None:
            issues_to_start.append(issue)

    # Load repo-specific config
    repo_vscodeclaude_config = load_repo_vscodeclaude_config(repo_name)

    # Start new sessions up to max
    started_sessions: list[VSCodeClaudeSession] = []
    available_slots = max_sessions - current_count

    for issue in issues_to_start[:available_slots]:
        try:
            # Get linked branch
            branch_name = get_linked_branch_for_issue(branch_manager, issue["number"])

            # Prepare and launch session
            session = prepare_and_launch_session(
                issue=issue,
                repo_config=repo_config,
                vscodeclaude_config=vscodeclaude_config,
                repo_vscodeclaude_config=repo_vscodeclaude_config,
                branch_name=branch_name,
                is_intervention=False,
            )
            started_sessions.append(session)
            current_count += 1

        except Exception as e:
            logger.error(
                "Failed to start session for issue #%d: %s",
                issue["number"],
                str(e),
            )

    return started_sessions


def regenerate_session_files(
    session: VSCodeClaudeSession,
    issue: IssueData,
) -> Path:
    """Regenerate all session files with fresh issue data.

    Args:
        session: Current session data
        issue: Fresh issue data from GitHub API

    Returns:
        Path to the startup script

    Regenerates:
    - Startup script (.bat/.sh) with current issue title/URL
    - VSCode task (.vscode/tasks.json)
    - Status file (.vscodeclaude_status.md)
    - Workspace file (.code-workspace)
    """
    folder_path = Path(session["folder"])
    repo_full_name = session["repo"]
    repo_short_name = get_repo_short_name_from_full(repo_full_name)
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_url = issue.get("url", "")
    status = get_issue_status(issue)
    is_intervention = session.get("is_intervention", False)

    # Get current branch from git
    try:
        options = CommandOptions(cwd=str(folder_path), check=True)
        result = execute_subprocess(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            options,
        )
        branch_name = result.stdout.strip()
    except CalledProcessError:
        branch_name = "main"

    # Regenerate startup script
    script_path = create_startup_script(
        folder_path=folder_path,
        issue_number=issue_number,
        issue_title=issue_title,
        status=status,
        repo_name=repo_short_name,
        issue_url=issue_url,
        is_intervention=is_intervention,
        timeout=DEFAULT_PROMPT_TIMEOUT,
    )

    # Regenerate VSCode task
    create_vscode_task(folder_path, script_path)

    # Regenerate status file
    create_status_file(
        folder_path=folder_path,
        issue_number=issue_number,
        issue_title=issue_title,
        status=status,
        repo_full_name=repo_full_name,
        branch_name=branch_name,
        issue_url=issue_url,
        is_intervention=is_intervention,
    )

    # Regenerate workspace file
    workspace_base = folder_path.parent
    folder_name = folder_path.name
    create_workspace_file(
        workspace_base=str(workspace_base),
        folder_name=folder_name,
        issue_number=issue_number,
        issue_title=issue_title,
        status=status,
        repo_name=repo_short_name,
    )

    logger.debug(
        "Regenerated session files for issue #%d",
        issue_number,
    )

    return script_path


def _get_configured_repos() -> set[str]:
    """Get set of repo full names from config.

    Reads config file and extracts repo_url values from
    [coordinator.repos.*] sections, converting them to "owner/repo" format.

    Returns:
        Set of repo full names in "owner/repo" format
    """
    config_data = load_config()
    repos_section = config_data.get("coordinator", {}).get("repos", {})

    configured_repos: set[str] = set()
    for repo_name, repo_config in repos_section.items():
        repo_url = repo_config.get("repo_url", "")
        if repo_url:
            try:
                repo_full_name = get_repo_full_name({"repo_url": repo_url})
                configured_repos.add(repo_full_name)
            except ValueError:
                # Skip invalid repo URLs
                pass

    return configured_repos


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

    Before restarting, regenerates all session files with fresh issue data.

    Returns:
        List of restarted sessions
    """
    from .sessions import remove_session

    store = load_sessions()
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

        # Check 1: PID-based check (quick but unreliable on Windows)
        if check_vscode_running(session.get("vscode_pid")):
            continue

        # Check 2: Window title check (Windows only, fast and reliable)
        if is_vscode_window_open_for_folder(
            session["folder"],
            issue_number=session["issue_number"],
            repo=session["repo"],
        ):
            logger.debug(
                "VSCode window open for issue #%d (detected via window title)",
                session["issue_number"],
            )
            continue

        # Check 3: Process cmdline check (slow fallback, rarely matches)
        is_open, found_pid = is_vscode_open_for_folder(session["folder"])
        if is_open:
            # VSCode is open but PID changed - update stored PID
            if found_pid:
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

        # Check if session is stale (issue status changed)
        if is_session_stale(session, cached_issues=repo_cached_issues):
            logger.info(
                "Skipping stale session for issue #%d (status changed)",
                session["issue_number"],
            )
            continue

        # Get issue data from cache or fetch from API
        issue_number = session["issue_number"]
        repo_url = f"https://github.com/{repo_full_name}"

        try:
            if repo_cached_issues and issue_number in repo_cached_issues:
                issue = repo_cached_issues[issue_number]
            else:
                issue_manager = IssueManager(repo_url=repo_url)
                issue = issue_manager.get_issue(issue_number)

            if issue["number"] == 0:
                logger.warning(
                    "Failed to fetch issue #%d, skipping file regeneration",
                    issue_number,
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

            # Update session status if changed
            current_status = get_issue_status(issue)
            if current_status != session["status"]:
                update_session_status(session["folder"], current_status)
                logger.debug(
                    "Updated session status for #%d: %s -> %s",
                    issue_number,
                    session["status"],
                    current_status,
                )

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
