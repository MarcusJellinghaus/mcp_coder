import logging
import platform
import shutil
from pathlib import Path

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
    launch_process,
)
from ...utils.user_config import get_cache_refresh_minutes
from .config import (
    get_github_username,
    get_repo_full_name,
    get_repo_short_name,
    load_repo_vscodeclaude_config,
)
from .helpers import (
    build_session,
    get_issue_status,
    get_repo_short_name_from_full,
    get_stage_display_name,
    truncate_title,
)
from .issues import (
    _filter_eligible_vscodeclaude_issues,
    get_linked_branch_for_issue,
    is_status_eligible_for_session,
    status_requires_linked_branch,
)
from .sessions import (
    add_session,
    get_active_session_count,
    get_session_for_issue,
)
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
    "launch_vscode",
    "prepare_and_launch_session",
    "process_eligible_issues",
    "regenerate_session_files",
]


def launch_vscode(workspace_file: Path, session_working_dir: Path | None = None) -> int:
    """Launch VSCode with workspace file.

    Args:
        workspace_file: Path to .code-workspace file
        session_working_dir: Session working directory (passed to startup script for MCP configuration)

    Returns:
        VSCode process PID

    Uses launch_process for non-blocking launch.
    On Windows, uses shell=True to find code.cmd in PATH.
    MCP environment variables are now set directly in the startup script.
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

        # Create startup script with session folder path for MCP environment variables
        script_path = create_startup_script(
            folder_path=folder_path,
            issue_number=issue_number,
            issue_title=issue_title,
            status=status,
            repo_name=repo_short_name,
            issue_url=issue_url,
            is_intervention=is_intervention,
            timeout=DEFAULT_PROMPT_TIMEOUT,
            session_folder_path=folder_path,
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

        # Launch VSCode (MCP environment variables are now set directly in startup script)
        # This ensures MCP_CODER_PROJECT_DIR and MCP_CODER_VENV_DIR point to the session's
        # working directory, not the mcp-coder installation directory
        pid = launch_vscode(workspace_file, folder_path)

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
    all_cached_issues: list[IssueData] | None = None,
) -> list[VSCodeClaudeSession]:
    """Process eligible issues for a repository.

    Args:
        repo_name: Repository config name used to load per-repo VSCodeClaude config.
        repo_config: Repository config dict containing at minimum ``repo_url``.
        vscodeclaude_config: Global VSCodeClaude config (workspace_base, max_sessions, etc.).
        max_sessions: Maximum number of concurrent sessions allowed across all repos.
        all_cached_issues: Pre-fetched list of all issues for the repo. When provided,
            ``get_all_cached_issues`` is not called, avoiding a duplicate-protection
            cache miss. Defaults to ``None``, in which case issues are fetched from
            cache as before (backward-compatible).

    Returns:
        List of sessions that were started during this call.

    The function:
    - Skips immediately if max sessions are reached.
    - Fetches issues from cache only when ``all_cached_issues`` is not supplied.
    - Filters eligible issues, skips those with existing sessions or missing branches.
    - Starts new sessions up to the remaining available slot count.
    """
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
    if all_cached_issues is None:
        logger.debug(
            "process_eligible_issues: no pre-fetched issues provided, fetching from cache"
        )
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
            # Get issue status
            status = get_issue_status(issue)

            # Get linked branch (handle multiple branches case)
            try:
                branch_name = get_linked_branch_for_issue(
                    branch_manager, issue["number"]
                )
            except ValueError:
                # Multiple branches linked to issue
                logger.error(
                    "Issue #%d at %s has multiple branches linked - skipping",
                    issue["number"],
                    status,
                )
                continue

            # Check if status requires linked branch
            if status_requires_linked_branch(status) and branch_name is None:
                logger.error(
                    "Issue #%d at %s has no linked branch - skipping",
                    issue["number"],
                    status,
                )
                continue

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
    - Status file (.vscodeclaude_status.txt)
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

    # Regenerate startup script with session folder path for MCP environment variables
    script_path = create_startup_script(
        folder_path=folder_path,
        issue_number=issue_number,
        issue_title=issue_title,
        status=status,
        repo_name=repo_short_name,
        issue_url=issue_url,
        is_intervention=is_intervention,
        timeout=DEFAULT_PROMPT_TIMEOUT,
        session_folder_path=folder_path,
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
