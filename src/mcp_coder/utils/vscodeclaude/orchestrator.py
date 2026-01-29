"""Session orchestration for vscodeclaude feature.

Main functions for preparing, launching, and managing sessions.
"""

import logging
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from ..github_operations.issue_branch_manager import IssueBranchManager
from ..github_operations.issue_manager import IssueData, IssueManager
from .config import get_github_username, load_repo_vscodeclaude_config
from .issues import get_eligible_vscodeclaude_issues, get_linked_branch_for_issue
from .sessions import (
    add_session,
    check_vscode_running,
    get_active_session_count,
    get_session_for_issue,
    load_sessions,
    update_session_pid,
)
from .status import is_session_stale
from .types import (
    STAGE_DISPLAY_NAMES,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
)
from .workspace import (
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


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


def launch_vscode(workspace_file: Path) -> int:
    """Launch VSCode with workspace file.

    Args:
        workspace_file: Path to .code-workspace file

    Returns:
        VSCode process PID

    Uses subprocess.Popen for non-blocking launch.
    On Windows, uses shell=True to find code.cmd in PATH.
    """
    is_windows = platform.system() == "Windows"

    if is_windows:
        # On Windows, 'code' is a .cmd file which requires shell=True
        process = subprocess.Popen(
            f'code "{workspace_file}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        process = subprocess.Popen(
            ["code", str(workspace_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return process.pid


def get_stage_display_name(status: str) -> str:
    """Get human-readable stage name for display.

    Args:
        status: Status label (e.g., "status-07:code-review")

    Returns:
        Display name (e.g., "CODE REVIEW")
    """
    return STAGE_DISPLAY_NAMES.get(status, status.upper())


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


def _get_repo_short_name(repo_config: dict[str, str]) -> str:
    """Extract short repo name from repo_url.

    Args:
        repo_config: Repository config dict with repo_url

    Returns:
        Short repo name (e.g., "mcp-coder" from the URL)
    """
    repo_url = repo_config.get("repo_url", "")
    # Extract from URLs like https://github.com/owner/repo.git
    if "/" in repo_url:
        name = repo_url.rstrip("/").rstrip(".git").split("/")[-1]
        return name
    return "repo"


def _get_repo_full_name(repo_config: dict[str, str]) -> str:
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
        parts = repo_url.rstrip("/").rstrip(".git").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    raise ValueError(f"Cannot parse repo URL: {repo_url}")


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


def _build_session(
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
        subprocess.CalledProcessError: If git or setup fails

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
    repo_short_name = _get_repo_short_name(repo_config)
    repo_full_name = _get_repo_full_name(repo_config)
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_url = issue.get("url", "")
    status = _get_issue_status(issue)

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
        session = _build_session(
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
            shutil.rmtree(folder_path, ignore_errors=True)
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
    coordinator = _get_coordinator()

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
    repo_full_name = _get_repo_full_name(repo_config)

    # Create managers using the classes from coordinator
    # Build repo_url from repo_full_name for proper instantiation
    repo_url = f"https://github.com/{repo_full_name}"
    logger.debug(
        "process_eligible_issues: processing repo %s (url: %s)",
        repo_full_name,
        repo_url,
    )
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
    branch_manager: IssueBranchManager = coordinator.IssueBranchManager(
        repo_url=repo_url
    )

    # Get eligible issues
    eligible_issues = get_eligible_vscodeclaude_issues(issue_manager, github_username)

    # Separate pr-created issues (handle separately)
    pr_created_issues: list[IssueData] = []
    actionable_issues: list[IssueData] = []

    for issue in eligible_issues:
        status = _get_issue_status(issue)
        if status == "status-10:pr-created":
            pr_created_issues.append(issue)
        else:
            actionable_issues.append(issue)

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

    # Handle pr-created issues (just display info)
    if pr_created_issues:
        handle_pr_created_issues(pr_created_issues)

    return started_sessions


def _get_repo_short_name_from_full(repo_full_name: str) -> str:
    """Extract short repo name from full name (owner/repo).

    Args:
        repo_full_name: Full repo name like "owner/repo"

    Returns:
        Short repo name (e.g., "repo")
    """
    if "/" in repo_full_name:
        return repo_full_name.split("/")[-1]
    return repo_full_name


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
    repo_short_name = _get_repo_short_name_from_full(repo_full_name)
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_url = issue.get("url", "")
    status = _get_issue_status(issue)
    is_intervention = session.get("is_intervention", False)

    # Get current branch from git
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=folder_path,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_name = result.stdout.strip()
    except subprocess.CalledProcessError:
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


def restart_closed_sessions() -> list[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.

    Finds sessions where:
    - VSCode PID no longer running
    - Issue status unchanged (not stale)
    - Folder still exists

    Before restarting, regenerates all session files with fresh issue data.

    Returns:
        List of restarted sessions
    """
    from .sessions import remove_session

    coordinator = _get_coordinator()
    store = load_sessions()
    restarted: list[VSCodeClaudeSession] = []

    for session in store["sessions"]:
        # Check if VSCode is still running
        if check_vscode_running(session.get("vscode_pid")):
            continue

        # Check if folder exists
        folder_path = Path(session["folder"])
        if not folder_path.exists():
            # Remove orphaned session
            remove_session(session["folder"])
            logger.info(
                "Removed orphaned session for issue #%d (folder missing)",
                session["issue_number"],
            )
            continue

        # Check if session is stale (issue status changed)
        if is_session_stale(session):
            logger.info(
                "Skipping stale session for issue #%d (status changed)",
                session["issue_number"],
            )
            continue

        # Fetch fresh issue data from GitHub
        repo_full_name = session["repo"]
        issue_number = session["issue_number"]
        repo_url = f"https://github.com/{repo_full_name}"

        try:
            issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
            issue = issue_manager.get_issue(issue_number)

            if issue["number"] == 0:
                logger.warning(
                    "Failed to fetch issue #%d, skipping file regeneration",
                    issue_number,
                )
            else:
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
