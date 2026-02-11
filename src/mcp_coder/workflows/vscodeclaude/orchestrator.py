"""Session orchestration for vscodeclaude feature.

Main functions for preparing, launching, and managing sessions.

Session Lifecycle Rules:
- Sessions are created for issues at human_action statuses with initial_command
- Eligible statuses: status-01:created, status-04:plan-review, status-07:code-review
- Ineligible: bot_pickup (02, 05, 08), bot_busy (03, 06, 09), pr-created (10)

Branch Handling Rules:
- status-01:created: Use linked branch if exists, fall back to 'main' if not
- status-04:plan-review: REQUIRE linked branch, skip if missing
- status-07:code-review: REQUIRE linked branch, skip if missing

Restart Behavior:
- Every restart runs 'git fetch origin' to sync with remote
- status-01 restarts: Stay on current branch, fetch only
- status-04/07 restarts: Verify linked branch, checkout if different, pull
- Status changes (01→04): Auto-switch to linked branch if repo is clean

Branch Verification on Restart:
1. git fetch origin (always, all statuses)
2. If status-04/07:
   a. Get linked branch from GitHub API
   b. If no linked branch → skip restart, show "!! No branch"
   c. Check repo dirty (git status --porcelain)
   d. If dirty → skip restart, show "!! Dirty"
   e. git checkout <linked_branch>
   f. git pull
   g. If git error → skip restart, show "!! Git error"
3. Update .vscodeclaude_status.txt with branch name
4. Regenerate session files
5. Launch VSCode

Cleanup Behavior:
- Stale sessions (status changed, closed, bot stage, pr-created) eligible for --cleanup
- Dirty folders (uncommitted changes) require manual cleanup, never auto-deleted

Dirty Folder Protection:
- Sessions with uncommitted git changes are never auto-deleted
- Display shows "!! Manual cleanup" for these cases
- Dirty detection: any output from 'git status --porcelain'

Status Table Indicators:
- (active): VSCode is running
- !! No branch: status-04/07 without linked branch
- !! Dirty: Repo has uncommitted changes, can't switch branch
- !! Git error: Git operation failed
- → Needs branch: Eligible issue at status-04/07 needs linked branch
- Blocked (label): Issue has ignore label
- → Delete (with --cleanup): Session is stale
- → Restart: Normal restart needed
- → Create and start: New session can be created

Intervention Sessions:
- Follow same branch rules as normal sessions
- is_intervention flag doesn't affect branch requirements

---

## Decision Matrix: Session Actions by State

### Launch Behavior (New Sessions)

| Status | Branch State | Action | Reason |
|--------|--------------|--------|--------|
| 01:created | No linked | Launch on `main` | Fallback allowed for status-01 |
| 01:created | Has linked | Launch on linked | Use linked branch if available |
| 04:plan-review | No linked | Skip, log error | Branch required for status-04 |
| 04:plan-review | Has linked | Launch on linked | Normal flow |
| 04:plan-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 07:code-review | No linked | Skip, log error | Branch required for status-07 |
| 07:code-review | Has linked | Launch on linked | Normal flow |
| 07:code-review | Multiple linked | Skip, log error | Ambiguous branch state |
| 10:pr-created | Any | No session | PR-created issues don't need sessions |

### Restart Behavior (Existing Sessions)

| Status | Branch | VSCode | Folder | Blocked | Git Fetch | Action | Indicator |
|--------|--------|--------|--------|---------|-----------|--------|-----------|
| 01 | Any | Running | Any | No | - | No action | (active) |
| 01 | Any | Closed | Clean | No | Success | Restart, stay on branch | → Restart |
| 01 | Any | Closed | Dirty | No | Success | Skip | !! Dirty |
| 01 | Any | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 01 | Any | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 04 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 04 | Has linked | Running | Any | No | - | No action | (active) |
| 04 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 04 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 04 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 04 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |
| 07 | No linked | Closed | Clean | No | Success | Skip | !! No branch |
| 07 | Multiple | Closed | Clean | No | Success | Skip | !! Multi-branch |
| 07 | Has linked | Running | Any | No | - | No action | (active) |
| 07 | Has linked | Closed | Dirty | No | Success | Skip | !! Dirty |
| 07 | Has linked | Closed | Clean | No | Failed | Skip | !! Git error |
| 07 | Has linked | Closed | Clean | No | Success | Checkout + pull + restart | → Restart |
| 07 | Has linked | Closed | Clean | Yes | - | Skip | Blocked (label) |

**Priority Order for Restart Decisions:**
1. VSCode running → (active)
2. Skip reason (no branch/dirty/git error/multi-branch) → !! indicators
3. Blocked label → Blocked (label)
4. Stale (status changed to ineligible) → → Delete (with --cleanup)
5. Normal flow → → Restart

### Status Display (No Existing Session)

| Status | Branch State | Issue State | Indicator |
|--------|--------------|-------------|-----------|
| 01 | Any | Open, eligible | → Create and start |
| 04 | No linked | Open, eligible | → Needs branch |
| 04 | Multiple linked | Open, eligible | → Needs branch |
| 04 | Has linked | Open, eligible | → Create and start |
| 07 | No linked | Open, eligible | → Needs branch |
| 07 | Multiple linked | Open, eligible | → Needs branch |
| 07 | Has linked | Open, eligible | → Create and start |
| 10:pr-created | Any | Open | (No session row) |

---

## Common Scenarios

### Scenario 1: Fresh Planning Session
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout feature/issue-123, launch VSCode
```

### Scenario 2: Planning Approved, Status Changed
```
Initial: Status 04:plan-review on feature/issue-123
User approves plan, status changes to 05:bot-pickup
VSCode: Running
Action: No restart (bot status ineligible), marked stale for cleanup
Display: "→ Delete (with --cleanup)"
```

### Scenario 3: Restart After VSCode Closed
```
Status: 07:code-review
Branch: feature/issue-123 (linked)
VSCode: Closed (user closed it)
Folder: Clean (no uncommitted changes)
Restart flow:
  1. git fetch origin
  2. Get linked branch: feature/issue-123
  3. Check dirty: Clean
  4. git checkout feature/issue-123
  5. git pull
  6. Regenerate session files
  7. Launch VSCode
```

### Scenario 4: Restart Blocked by Uncommitted Work
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Dirty (user made changes)
Action: Skip restart
Display: "!! Dirty"
Reason: Can't switch branches with uncommitted changes
```

### Scenario 5: Issue Moved to Code Review, No Branch
```
Status: 07:code-review
Branch: None linked (forgot to link in GitHub)
VSCode: Closed
Action: Skip restart
Display: "!! No branch"
Reason: Status-07 requires linked branch
```

### Scenario 6: Multiple Branches Linked
```
Status: 04:plan-review
Branch: Multiple branches linked to issue in GitHub
VSCode: Closed
Action: Skip restart
Display: "!! Multi-branch"
Reason: Ambiguous which branch to use
Fix: Unlink all but one branch in GitHub
```

### Scenario 7: Status-01 Without Branch
```
Status: 01:created
Branch: No linked branch
VSCode: Not running
Folder: Does not exist
Action: Create folder, clone, checkout main, launch VSCode
Display: "→ Create and start"
Reason: Status-01 allows fallback to main
```

### Scenario 8: Network Failure on Restart
```
Status: 04:plan-review
Branch: feature/issue-123 (linked)
VSCode: Closed
Folder: Clean
git fetch origin: FAILS (network down)
Action: Skip restart
Display: "!! Git error"
Reason: Can't proceed without fetch
```

---

## State Transitions

```
NEW ISSUE (status-01:created)
    ├─► Has linked branch → Launch on linked branch
    └─► No linked branch → Launch on main

PLANNING PHASE (status-04:plan-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

CODE REVIEW (status-07:code-review)
    ├─► Has linked branch + clean → Launch/restart
    ├─► Has linked branch + dirty → Skip (!! Dirty)
    ├─► No linked branch → Skip (!! No branch)
    └─► Multiple branches → Skip (!! Multi-branch)

PR CREATED (status-10:pr-created)
    └─► No session created (displayed separately)
```
"""

import logging
import platform
import shutil
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
    is_status_eligible_for_session,
    status_requires_linked_branch,
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
from .status import get_folder_git_status
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


class BranchPrepResult(NamedTuple):
    """Result of branch preparation for session restart."""

    should_proceed: bool
    skip_reason: str | None = None
    branch_name: str | None = None


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
    for _repo_name, repo_config in repos_section.items():
        repo_url = repo_config.get("repo_url", "")
        if repo_url:
            try:
                repo_full_name = get_repo_full_name({"repo_url": repo_url})
                configured_repos.add(repo_full_name)
            except ValueError:
                # Skip invalid repo URLs
                pass

    return configured_repos


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
    """
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

            # Check if issue is closed
            if issue["state"] != "open":
                logger.info("Skipping closed issue #%d", issue_number)
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
