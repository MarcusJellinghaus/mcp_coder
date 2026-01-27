"""VSCode Claude session management for interactive workflow stages."""

import json
import logging
import platform
import re
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from types import ModuleType
from typing import Any, List, Optional, TypedDict, cast

from ....utils.github_operations.issue_branch_manager import IssueBranchManager
from ....utils.github_operations.issue_manager import IssueData, IssueManager

logger = logging.getLogger(__name__)


def _get_coordinator() -> ModuleType:
    """Get coordinator package for late binding of patchable functions."""
    from mcp_coder.cli.commands import coordinator

    return coordinator


class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""

    folder: str  # Full path to working folder
    repo: str  # "owner/repo" format
    issue_number: int
    status: str  # e.g., "status-07:code-review"
    vscode_pid: Optional[int]
    started_at: str  # ISO 8601
    is_intervention: bool


class VSCodeClaudeSessionStore(TypedDict):
    """Session storage file structure."""

    sessions: List[VSCodeClaudeSession]
    last_updated: str  # ISO 8601


class VSCodeClaudeConfig(TypedDict):
    """Configuration for vscodeclaude feature."""

    workspace_base: str
    max_sessions: int


class RepoVSCodeClaudeConfig(TypedDict, total=False):
    """Per-repo vscodeclaude config (extends existing repo config)."""

    setup_commands_windows: List[str]
    setup_commands_linux: List[str]


# Priority order for human_action statuses (later stages first)
VSCODECLAUDE_PRIORITY: List[str] = [
    "status-10:pr-created",
    "status-07:code-review",
    "status-04:plan-review",
    "status-01:created",
]

# Mapping of status to slash commands
HUMAN_ACTION_COMMANDS: dict[str, tuple[Optional[str], Optional[str]]] = {
    # status: (initial_command, followup_command)
    "status-01:created": ("/issue_analyse", "/discuss"),
    "status-04:plan-review": ("/plan_review", "/discuss"),
    "status-07:code-review": ("/implementation_review", "/discuss"),
    "status-10:pr-created": (None, None),  # Show PR URL only
}

# Status emoji mapping for banners
STATUS_EMOJI: dict[str, str] = {
    "status-01:created": "📝",
    "status-04:plan-review": "📋",
    "status-07:code-review": "🔍",
    "status-10:pr-created": "🎉",
}

# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3


def get_sessions_file_path() -> Path:
    """Get path to sessions JSON file.

    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json
        on Windows, or ~/.config/mcp_coder/coordinator_cache/vscodeclaude_sessions.json
        on Linux/macOS.
    """
    if platform.system() == "Windows":
        base = Path.home() / ".mcp_coder"
    else:
        base = Path.home() / ".config" / "mcp_coder"
    return base / "coordinator_cache" / "vscodeclaude_sessions.json"


def load_sessions() -> VSCodeClaudeSessionStore:
    """Load sessions from JSON file.

    Returns:
        Session store dict. Empty sessions list if file doesn't exist.
    """
    sessions_file = get_sessions_file_path()
    if not sessions_file.exists():
        return {"sessions": [], "last_updated": ""}

    try:
        content = sessions_file.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(content)
        # Validate structure
        if "sessions" not in data:
            data["sessions"] = []
        if "last_updated" not in data:
            data["last_updated"] = ""
        return cast(VSCodeClaudeSessionStore, data)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load sessions file: %s", e)
        return {"sessions": [], "last_updated": ""}


def save_sessions(store: VSCodeClaudeSessionStore) -> None:
    """Save sessions to JSON file.

    Args:
        store: Session store to save

    Creates parent directories if needed.
    """
    sessions_file = get_sessions_file_path()
    sessions_file.parent.mkdir(parents=True, exist_ok=True)
    store["last_updated"] = datetime.now(timezone.utc).isoformat()
    sessions_file.write_text(json.dumps(store, indent=2), encoding="utf-8")


def check_vscode_running(pid: Optional[int]) -> bool:
    """Check if VSCode process is still running.

    Args:
        pid: Process ID to check (None returns False)

    Returns:
        True if process exists and is running

    Uses psutil for cross-platform compatibility.
    """
    if pid is None:
        return False

    try:
        import psutil

        if not psutil.pid_exists(pid):
            return False
        try:
            process = psutil.Process(pid)
            name = process.name().lower()
            return "code" in name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    except ImportError:
        logger.warning("psutil not available, cannot check process status")
        return False


def get_session_for_issue(
    repo_full_name: str,
    issue_number: int,
) -> Optional[VSCodeClaudeSession]:
    """Find existing session for an issue.

    Args:
        repo_full_name: "owner/repo" format
        issue_number: GitHub issue number

    Returns:
        Session dict if found, None otherwise
    """
    store = load_sessions()
    for session in store["sessions"]:
        if (
            session["repo"] == repo_full_name
            and session["issue_number"] == issue_number
        ):
            return session
    return None


def add_session(session: VSCodeClaudeSession) -> None:
    """Add new session to store.

    Args:
        session: Session to add

    Automatically updates last_updated timestamp.
    """
    store = load_sessions()
    store["sessions"].append(session)
    save_sessions(store)


def remove_session(folder: str) -> bool:
    """Remove session by folder path.

    Args:
        folder: Full path to working folder

    Returns:
        True if session was found and removed
    """
    store = load_sessions()
    original_count = len(store["sessions"])
    store["sessions"] = [s for s in store["sessions"] if s["folder"] != folder]
    if len(store["sessions"]) < original_count:
        save_sessions(store)
        return True
    return False


def get_active_session_count() -> int:
    """Count sessions with running VSCode processes.

    Returns:
        Number of sessions where VSCode PID is still running
    """
    store = load_sessions()
    count = 0
    for session in store["sessions"]:
        if check_vscode_running(session.get("vscode_pid")):
            count += 1
    return count


def update_session_pid(folder: str, pid: int) -> None:
    """Update VSCode PID for existing session.

    Args:
        folder: Session folder path
        pid: New VSCode process ID
    """
    store = load_sessions()
    for session in store["sessions"]:
        if session["folder"] == folder:
            session["vscode_pid"] = pid
            break
    save_sessions(store)


# =============================================================================
# Configuration Functions
# =============================================================================


def load_vscodeclaude_config() -> VSCodeClaudeConfig:
    """Load vscodeclaude configuration from config.toml.

    Returns:
        VSCodeClaudeConfig with workspace_base and max_sessions

    Raises:
        ValueError: If workspace_base not configured or doesn't exist
    """
    coordinator = _get_coordinator()

    # Batch fetch config values
    config = coordinator.get_config_values(
        [
            ("coordinator.vscodeclaude", "workspace_base", None),
            ("coordinator.vscodeclaude", "max_sessions", None),
        ]
    )

    workspace_base = config[("coordinator.vscodeclaude", "workspace_base")]
    max_sessions_str = config[("coordinator.vscodeclaude", "max_sessions")]

    # Validate workspace_base is configured
    if not workspace_base:
        raise ValueError(
            "workspace_base not configured in config.toml "
            "[coordinator.vscodeclaude] section"
        )

    # Validate workspace_base path exists
    workspace_path = Path(workspace_base)
    if not workspace_path.exists():
        raise ValueError(f"workspace_base path does not exist: {workspace_base}")

    # Parse max_sessions with default fallback
    max_sessions = DEFAULT_MAX_SESSIONS
    if max_sessions_str:
        try:
            max_sessions = int(max_sessions_str)
        except ValueError:
            logger.warning(
                f"Invalid max_sessions value '{max_sessions_str}', "
                f"using default {DEFAULT_MAX_SESSIONS}"
            )

    return VSCodeClaudeConfig(
        workspace_base=workspace_base,
        max_sessions=max_sessions,
    )


def load_repo_vscodeclaude_config(repo_name: str) -> RepoVSCodeClaudeConfig:
    """Load repo-specific vscodeclaude config (setup commands).

    Args:
        repo_name: Repository name from config (e.g., "mcp_coder")

    Returns:
        RepoVSCodeClaudeConfig with optional setup_commands_windows/linux
    """
    coordinator = _get_coordinator()

    section = f"coordinator.repos.{repo_name}"

    # Batch fetch config values
    config = coordinator.get_config_values(
        [
            (section, "setup_commands_windows", None),
            (section, "setup_commands_linux", None),
        ]
    )

    result: RepoVSCodeClaudeConfig = {}

    # Parse setup_commands_windows if present
    windows_commands = config[(section, "setup_commands_windows")]
    if windows_commands:
        # Config value might be a JSON-encoded list or comma-separated string
        try:
            parsed = json.loads(windows_commands)
            if isinstance(parsed, list):
                result["setup_commands_windows"] = parsed
        except json.JSONDecodeError:
            # Treat as single command
            result["setup_commands_windows"] = [windows_commands]

    # Parse setup_commands_linux if present
    linux_commands = config[(section, "setup_commands_linux")]
    if linux_commands:
        try:
            parsed = json.loads(linux_commands)
            if isinstance(parsed, list):
                result["setup_commands_linux"] = parsed
        except json.JSONDecodeError:
            result["setup_commands_linux"] = [linux_commands]

    return result


def get_github_username() -> str:
    """Get authenticated GitHub username via PyGithub API.

    Returns:
        GitHub username string

    Raises:
        ValueError: If GitHub authentication fails
    """
    coordinator = _get_coordinator()

    # Get GitHub token from config
    config = coordinator.get_config_values([("github", "token", None)])
    token = config[("github", "token")]

    if not token:
        raise ValueError(
            "GitHub token not configured. Set via GITHUB_TOKEN environment "
            "variable or config file [github] section"
        )

    try:
        from github import Github

        github_client = Github(token)
        user = github_client.get_user()
        return user.login
    except Exception as e:
        raise ValueError(f"Failed to authenticate with GitHub: {e}") from e


def sanitize_folder_name(name: str) -> str:
    """Sanitize string for use in folder names.

    Args:
        name: Input string (e.g., repo name)

    Returns:
        String with only alphanumeric, dash, underscore chars
    """
    # Replace any non-alphanumeric character (except dash and underscore) with dash
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", name)
    # Collapse multiple dashes
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    # Strip leading/trailing dashes
    sanitized = sanitized.strip("-")
    return sanitized


# =============================================================================
# Issue Filtering Functions
# =============================================================================


def _load_labels_config() -> dict[str, Any]:
    """Load labels configuration from bundled package config.

    Returns:
        Labels config dict with workflow_labels and ignore_labels
    """
    coordinator = _get_coordinator()
    config_resource = resources.files("mcp_coder.config") / "labels.json"
    config_path = Path(str(config_resource))
    result: dict[str, Any] = coordinator.load_labels_config(config_path)
    return result


def get_human_action_labels() -> set[str]:
    """Get set of human_action status labels from labels.json.

    Returns:
        Set of label names with category="human_action"
    """
    labels_config = _load_labels_config()

    return {
        label["name"]
        for label in labels_config["workflow_labels"]
        if label["category"] == "human_action"
    }


def _is_issue_eligible(
    issue: IssueData,
    human_action_labels: set[str],
    ignore_labels_set: set[str],
    github_username: str,
) -> bool:
    """Check if an issue is eligible for vscodeclaude session.

    Args:
        issue: Issue to check
        human_action_labels: Set of human_action label names
        ignore_labels_set: Set of labels to ignore
        github_username: Username that must be assigned

    Returns:
        True if issue is eligible
    """
    issue_labels = set(issue["labels"])

    # Must have exactly one human_action label
    if len(issue_labels & human_action_labels) != 1:
        return False

    # Must not have any ignore_labels
    if issue_labels & ignore_labels_set:
        return False

    # Must be assigned to github_username
    return github_username in issue["assignees"]


def get_eligible_vscodeclaude_issues(
    issue_manager: IssueManager,
    github_username: str,
) -> List[IssueData]:
    """Get issues eligible for vscodeclaude sessions.

    Filters for:
    - Open issues only
    - Exactly one human_action label
    - Assigned to github_username
    - No ignore_labels

    Args:
        issue_manager: IssueManager for GitHub API
        github_username: Username to filter assignments

    Returns:
        List of eligible issues sorted by priority (later stages first)
    """
    labels_config = _load_labels_config()

    # Extract human_action labels
    human_action_labels = {
        label["name"]
        for label in labels_config["workflow_labels"]
        if label["category"] == "human_action"
    }

    # Extract ignore_labels set
    ignore_labels_set: set[str] = set(labels_config.get("ignore_labels", []))

    # Get all open issues and filter
    all_issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    eligible_issues = [
        issue
        for issue in all_issues
        if _is_issue_eligible(
            issue, human_action_labels, ignore_labels_set, github_username
        )
    ]

    # Sort by VSCODECLAUDE_PRIORITY (lower index = higher priority)
    priority_map = {label: i for i, label in enumerate(VSCODECLAUDE_PRIORITY)}

    def get_priority(issue: IssueData) -> int:
        """Get priority index for an issue (lower = higher priority)."""
        for label in issue["labels"]:
            if label in priority_map:
                return priority_map[label]
        return len(VSCODECLAUDE_PRIORITY)  # Lowest priority

    eligible_issues.sort(key=get_priority)

    return eligible_issues


def get_linked_branch_for_issue(
    branch_manager: IssueBranchManager,
    issue_number: int,
) -> Optional[str]:
    """Get linked branch for issue, fail if multiple.

    Args:
        branch_manager: IssueBranchManager for GitHub API
        issue_number: GitHub issue number

    Returns:
        Branch name if exactly one linked, None if none

    Raises:
        ValueError: If multiple branches linked to issue
    """
    branches = branch_manager.get_linked_branches(issue_number)

    if not branches:
        return None

    if len(branches) > 1:
        raise ValueError(
            f"Issue #{issue_number} has multiple branches linked: {branches}"
        )

    return branches[0]


# =============================================================================
# Workspace Setup Functions
# =============================================================================


def get_working_folder_path(
    workspace_base: str,
    repo_name: str,
    issue_number: int,
) -> Path:
    """Get full path for working folder.

    Args:
        workspace_base: Base directory from config
        repo_name: Repository short name (sanitized)
        issue_number: GitHub issue number

    Returns:
        Path like: workspace_base/mcp-coder_123
    """
    sanitized_repo = sanitize_folder_name(repo_name)
    folder_name = f"{sanitized_repo}_{issue_number}"
    return Path(workspace_base) / folder_name


def create_working_folder(folder_path: Path) -> bool:
    """Create working folder if it doesn't exist.

    Args:
        folder_path: Full path to create

    Returns:
        True if created, False if already existed
    """
    if folder_path.exists():
        return False
    folder_path.mkdir(parents=True, exist_ok=True)
    return True


def setup_git_repo(
    folder_path: Path,
    repo_url: str,
    branch_name: Optional[str],
) -> None:
    """Clone repo or checkout branch and pull.

    Args:
        folder_path: Working folder path
        repo_url: Git clone URL
        branch_name: Branch to checkout (None = use main)

    Steps:
    1. If folder empty: git clone
    2. If folder has .git: checkout branch, pull
    3. Uses system git credentials
    4. Logs progress using logger.info()

    Raises:
        subprocess.CalledProcessError: If git command fails
    """
    # Check if folder is empty or doesn't have .git
    is_empty = not any(folder_path.iterdir()) if folder_path.exists() else True
    has_git = (folder_path / ".git").exists()

    if is_empty:
        # Clone into folder
        logger.info("Cloning %s into %s", repo_url, folder_path)
        subprocess.run(
            ["git", "clone", repo_url, str(folder_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    elif not has_git:
        # Folder has content but no .git - error
        raise ValueError(
            f"Folder {folder_path} exists with content but is not a git repository"
        )

    # Checkout and pull
    branch = branch_name or "main"
    logger.info("Checking out branch %s", branch)
    subprocess.run(
        ["git", "checkout", branch],
        cwd=folder_path,
        check=True,
        capture_output=True,
        text=True,
    )

    logger.info("Pulling latest changes")
    subprocess.run(
        ["git", "pull"],
        cwd=folder_path,
        check=True,
        capture_output=True,
        text=True,
    )


def validate_mcp_json(folder_path: Path) -> None:
    """Validate .mcp.json exists in repo.

    Args:
        folder_path: Working folder path

    Raises:
        FileNotFoundError: If .mcp.json missing
    """
    mcp_json_path = folder_path / ".mcp.json"
    if not mcp_json_path.exists():
        raise FileNotFoundError(
            f".mcp.json not found in {folder_path}. "
            "This file is required for Claude Code integration."
        )


def validate_setup_commands(commands: List[str]) -> None:
    """Validate that setup commands exist in PATH.

    Args:
        commands: List of shell commands to validate

    Raises:
        FileNotFoundError: If any command not found in PATH
    """
    for command in commands:
        # Extract the executable (first word) from the command
        executable = command.split()[0] if command.strip() else ""
        if not executable:
            continue

        # Check if executable exists in PATH
        if shutil.which(executable) is None:
            raise FileNotFoundError(
                f"Command '{executable}' not found in PATH. "
                f"Full command: '{command}'"
            )


def run_setup_commands(
    folder_path: Path,
    commands: List[str],
) -> None:
    """Run platform-specific setup commands.

    Args:
        folder_path: Working directory for commands
        commands: List of shell commands to run

    Raises:
        subprocess.CalledProcessError: If any command fails

    Logs progress for each command using logger.info().
    """
    for command in commands:
        logger.info("Running: %s", command)
        subprocess.run(
            command,
            cwd=folder_path,
            check=True,
            shell=True,
            capture_output=True,
            text=True,
        )


def update_gitignore(folder_path: Path) -> None:
    """Append vscodeclaude entries to .gitignore.

    Args:
        folder_path: Working folder path

    Idempotent: won't duplicate entries.
    """
    from .vscodeclaude_templates import GITIGNORE_ENTRY

    gitignore_path = folder_path / ".gitignore"

    # Read existing content
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")

    # Check if already present
    if ".vscodeclaude_status.md" in existing_content:
        return

    # Append entry
    with gitignore_path.open("a", encoding="utf-8") as f:
        f.write(GITIGNORE_ENTRY)


def _get_stage_short(status: str) -> str:
    """Extract short stage name from status label.

    Args:
        status: Full status label like "status-07:code-review"

    Returns:
        Short name like "review" for window titles
    """
    # Extract the part after the colon and simplify
    if ":" in status:
        stage = status.split(":")[1]
        # Map to short names
        stage_map = {
            "created": "new",
            "plan-review": "plan",
            "code-review": "review",
            "pr-created": "pr",
        }
        return stage_map.get(stage, stage[:6])
    return status[:6]


def _get_stage_name(status: str) -> str:
    """Get display name for status.

    Args:
        status: Full status label

    Returns:
        Human-readable stage name
    """
    stage_names = {
        "status-01:created": "Issue Created",
        "status-04:plan-review": "Plan Review",
        "status-07:code-review": "Code Review",
        "status-10:pr-created": "PR Created",
    }
    return stage_names.get(status, status)


def create_workspace_file(
    workspace_base: str,
    folder_name: str,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
) -> Path:
    """Create .code-workspace file in workspace_base.

    Args:
        workspace_base: Base directory for workspace files
        folder_name: Working folder name (e.g., "mcp-coder_123")
        issue_number: GitHub issue number
        issue_title: Issue title for window title
        status: Status label for window title
        repo_name: Repo short name for window title

    Returns:
        Path to created workspace file
    """
    from .vscodeclaude_templates import WORKSPACE_FILE_TEMPLATE

    # Truncate title if too long
    title_short = issue_title[:30] + "..." if len(issue_title) > 30 else issue_title
    stage_short = _get_stage_short(status)

    # Format the workspace file
    content = WORKSPACE_FILE_TEMPLATE.format(
        folder_path=f"./{folder_name}",
        issue_number=issue_number,
        stage_short=stage_short,
        title_short=title_short,
        repo_name=repo_name,
    )

    # Write to workspace_base
    workspace_file = Path(workspace_base) / f"{folder_name}.code-workspace"
    workspace_file.write_text(content, encoding="utf-8")

    return workspace_file


def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    is_intervention: bool,
) -> Path:
    """Create platform-specific startup script.

    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title for banner
        status: Status label
        repo_name: Repo short name
        is_intervention: If True, use intervention mode (no automation)

    Returns:
        Path to created script (.bat or .sh)
    """
    from .vscodeclaude_templates import (
        AUTOMATED_SECTION_LINUX,
        AUTOMATED_SECTION_WINDOWS,
        INTERACTIVE_SECTION_LINUX,
        INTERACTIVE_SECTION_WINDOWS,
        INTERVENTION_SECTION_LINUX,
        INTERVENTION_SECTION_WINDOWS,
        STARTUP_SCRIPT_LINUX,
        STARTUP_SCRIPT_WINDOWS,
    )

    is_windows = platform.system() == "Windows"

    # Get commands for this status
    initial_cmd, followup_cmd = HUMAN_ACTION_COMMANDS.get(status, (None, None))

    # Get emoji and stage name
    emoji = STATUS_EMOJI.get(status, "📋")
    stage_name = _get_stage_name(status)

    # Truncate title if too long
    title_display = issue_title[:56] if len(issue_title) > 56 else issue_title

    # Build sections based on intervention mode
    if is_intervention:
        if is_windows:
            automated_section = ""
            interactive_section = INTERVENTION_SECTION_WINDOWS
        else:
            automated_section = ""
            interactive_section = INTERVENTION_SECTION_LINUX
    else:
        if is_windows:
            automated_section = (
                AUTOMATED_SECTION_WINDOWS.format(initial_command=initial_cmd)
                if initial_cmd
                else ""
            )
            interactive_section = (
                INTERACTIVE_SECTION_WINDOWS.format(followup_command=followup_cmd or "")
                if initial_cmd
                else INTERVENTION_SECTION_WINDOWS
            )
        else:
            automated_section = (
                AUTOMATED_SECTION_LINUX.format(initial_command=initial_cmd)
                if initial_cmd
                else ""
            )
            interactive_section = (
                INTERACTIVE_SECTION_LINUX.format(followup_command=followup_cmd or "")
                if initial_cmd
                else INTERVENTION_SECTION_LINUX
            )

    # Format main script
    if is_windows:
        script_content = STARTUP_SCRIPT_WINDOWS.format(
            emoji=emoji,
            stage_name=stage_name,
            issue_number=issue_number,
            title=title_display,
            repo=repo_name,
            status=status,
            automated_section=automated_section,
            interactive_section=interactive_section,
        )
        script_path = folder_path / ".vscodeclaude_start.bat"
    else:
        script_content = STARTUP_SCRIPT_LINUX.format(
            emoji=emoji,
            stage_name=stage_name,
            issue_number=issue_number,
            title=title_display,
            repo=repo_name,
            status=status,
            automated_section=automated_section,
            interactive_section=interactive_section,
        )
        script_path = folder_path / ".vscodeclaude_start.sh"

    # Write script
    script_path.write_text(script_content, encoding="utf-8")

    # Make executable on Linux
    if not is_windows:
        current_mode = script_path.stat().st_mode
        script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return script_path


def create_vscode_task(folder_path: Path, script_path: Path) -> None:
    """Create .vscode/tasks.json with runOn: folderOpen.

    Args:
        folder_path: Working folder path
        script_path: Path to startup script
    """
    from .vscodeclaude_templates import TASKS_JSON_TEMPLATE

    # Create .vscode directory
    vscode_dir = folder_path / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    # Format tasks.json
    content = TASKS_JSON_TEMPLATE.format(script_path=script_path.name)

    # Write tasks.json
    tasks_file = vscode_dir / "tasks.json"
    tasks_file.write_text(content, encoding="utf-8")


def create_status_file(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_full_name: str,
    branch_name: str,
    issue_url: str,
    is_intervention: bool,
) -> None:
    """Create .vscodeclaude_status.md in project root.

    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title
        status: Status label
        repo_full_name: Full repo name (owner/repo)
        branch_name: Git branch name
        issue_url: GitHub issue URL
        is_intervention: If True, add intervention warning
    """
    from .vscodeclaude_templates import (
        INTERVENTION_ROW,
        STATUS_FILE_TEMPLATE,
    )

    # Get emoji for status
    status_emoji = STATUS_EMOJI.get(status, "📋")

    # Build intervention row if needed
    intervention_row = INTERVENTION_ROW if is_intervention else ""

    # Format status file
    content = STATUS_FILE_TEMPLATE.format(
        issue_number=issue_number,
        title=issue_title,
        status_emoji=status_emoji,
        status_name=status,
        repo=repo_full_name,
        branch=branch_name,
        started_at=datetime.now(timezone.utc).isoformat(),
        intervention_row=intervention_row,
        issue_url=issue_url,
    )

    # Write status file
    status_file = folder_path / ".vscodeclaude_status.md"
    status_file.write_text(content, encoding="utf-8")


# =============================================================================
# Launch Functions
# =============================================================================


def launch_vscode(workspace_file: Path) -> int:
    """Launch VSCode with workspace file.

    Args:
        workspace_file: Path to .code-workspace file

    Returns:
        VSCode process PID

    Uses subprocess.Popen for non-blocking launch.
    """
    process = subprocess.Popen(
        ["code", str(workspace_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process.pid


# Stage display name mapping
STAGE_DISPLAY_NAMES: dict[str, str] = {
    "status-01:created": "ISSUE ANALYSIS",
    "status-04:plan-review": "PLAN REVIEW",
    "status-07:code-review": "CODE REVIEW",
    "status-10:pr-created": "PR CREATED",
}


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


# =============================================================================
# Session Orchestration Functions
# =============================================================================


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
    """
    repo_url = repo_config.get("repo_url", "")
    # Extract from URLs like https://github.com/owner/repo.git
    if "/" in repo_url:
        parts = repo_url.rstrip("/").rstrip(".git").split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return "unknown/repo"


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
    branch_name: Optional[str],
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
    repo_filter: Optional[str] = None,
) -> List[VSCodeClaudeSession]:
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
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)
    branch_manager: IssueBranchManager = coordinator.IssueBranchManager(
        repo_url=repo_url
    )

    # Get eligible issues
    eligible_issues = get_eligible_vscodeclaude_issues(issue_manager, github_username)

    # Separate pr-created issues (handle separately)
    pr_created_issues: List[IssueData] = []
    actionable_issues: List[IssueData] = []

    for issue in eligible_issues:
        status = _get_issue_status(issue)
        if status == "status-10:pr-created":
            pr_created_issues.append(issue)
        else:
            actionable_issues.append(issue)

    # Filter out issues that already have sessions
    issues_to_start: List[IssueData] = []
    for issue in actionable_issues:
        existing = get_session_for_issue(repo_full_name, issue["number"])
        if existing is None:
            issues_to_start.append(issue)

    # Load repo-specific config
    repo_vscodeclaude_config = load_repo_vscodeclaude_config(repo_name)

    # Start new sessions up to max
    started_sessions: List[VSCodeClaudeSession] = []
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
        handle_pr_created_issues(pr_created_issues, issue_manager)

    return started_sessions


def restart_closed_sessions() -> List[VSCodeClaudeSession]:
    """Restart sessions where VSCode was closed.

    Finds sessions where:
    - VSCode PID no longer running
    - Issue status unchanged (not stale)
    - Folder still exists

    Returns:
        List of restarted sessions
    """
    store = load_sessions()
    restarted: List[VSCodeClaudeSession] = []

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
            logger.info(
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
                "is_intervention": session["is_intervention"],
            }
            restarted.append(updated_session)

        except Exception as e:
            logger.error(
                "Failed to restart session for issue #%d: %s",
                session["issue_number"],
                str(e),
            )

    return restarted


def handle_pr_created_issues(
    issues: List[IssueData],
    issue_manager: IssueManager,  # noqa: ARG001 - kept for API compatibility
) -> None:
    """Display PR URLs for status-10:pr-created issues.

    Args:
        issues: Issues with status-10:pr-created
        issue_manager: IssueManager (kept for API compatibility)

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


# =============================================================================
# Status Display Functions
# =============================================================================


def get_issue_current_status(
    issue_manager: IssueManager,
    issue_number: int,
) -> Optional[str]:
    """Get current status label for an issue.

    Args:
        issue_manager: IssueManager for GitHub API
        issue_number: GitHub issue number

    Returns:
        Current status label or None if no status found
    """
    try:
        issue = issue_manager.get_issue(issue_number)
        if issue is None:
            return None  # type: ignore[unreachable]

        for label in issue["labels"]:
            if label.startswith("status-"):
                return label
        return None
    except Exception as e:
        logger.warning("Failed to get issue #%d status: %s", issue_number, e)
        return None


def is_session_stale(session: VSCodeClaudeSession) -> bool:
    """Check if session's issue status has changed.

    Args:
        session: Session to check

    Returns:
        True if issue status differs from session status
    """
    coordinator = _get_coordinator()

    repo_full_name = session["repo"]
    issue_number = session["issue_number"]
    session_status = session["status"]

    # Create issue manager for the repo
    # Build repo_url from repo_full_name for proper instantiation
    repo_url = f"https://github.com/{repo_full_name}"
    issue_manager: IssueManager = coordinator.IssueManager(repo_url=repo_url)

    # Get current status
    current_status = get_issue_current_status(issue_manager, issue_number)

    # If no status found, consider it stale (conservative approach)
    if current_status is None:
        return True

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
    session: VSCodeClaudeSession,
    is_stale: bool,
    is_dirty: bool,
    is_vscode_running: bool,
) -> str:
    """Determine next action for a session.

    Args:
        session: Session data (unused but kept for API consistency)
        is_stale: Whether issue status changed
        is_dirty: Whether folder has uncommitted changes
        is_vscode_running: Whether VSCode is still running

    Returns:
        Action string like "(active)", "→ Restart", "→ Delete", "⚠️ Manual cleanup"
    """
    # Suppress unused argument warning
    _ = session

    if is_vscode_running:
        return "(active)"

    if is_stale:
        if is_dirty:
            return "⚠️ Manual cleanup"
        return "→ Delete (with --cleanup)"

    return "→ Restart"


def display_status_table(
    sessions: List[VSCodeClaudeSession],
    eligible_issues: List[tuple[str, IssueData]],
    repo_filter: Optional[str] = None,
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
        action = get_next_action(session, stale, is_dirty, is_running)

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


# =============================================================================
# Cleanup Functions
# =============================================================================


def get_stale_sessions() -> List[tuple[VSCodeClaudeSession, bool]]:
    """Get stale sessions with dirty status.

    Returns:
        List of (session, is_dirty) tuples for stale sessions
    """
    store = load_sessions()
    stale_sessions: List[tuple[VSCodeClaudeSession, bool]] = []

    for session in store["sessions"]:
        # Skip sessions with running VSCode
        if check_vscode_running(session.get("vscode_pid")):
            continue

        # Check if session is stale
        if is_session_stale(session):
            folder_path = Path(session["folder"])
            is_dirty = (
                check_folder_dirty(folder_path) if folder_path.exists() else False
            )
            stale_sessions.append((session, is_dirty))

    return stale_sessions


def delete_session_folder(session: VSCodeClaudeSession) -> bool:
    """Delete session folder and remove from session store.

    Args:
        session: Session to delete

    Returns:
        True if successfully deleted

    Uses shutil.rmtree for folder deletion.
    """
    folder_path = Path(session["folder"])

    try:
        # Delete the folder if it exists
        if folder_path.exists():
            shutil.rmtree(folder_path)
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


def cleanup_stale_sessions(dry_run: bool = True) -> dict[str, List[str]]:
    """Clean up stale session folders.

    Args:
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with "deleted" and "skipped" folder lists

    Behavior:
    - Stale + clean: delete folder and session
    - Stale + dirty: skip with warning
    """
    result: dict[str, List[str]] = {"deleted": [], "skipped": []}

    stale_sessions = get_stale_sessions()

    for session, is_dirty in stale_sessions:
        folder = session["folder"]

        if is_dirty:
            # Skip dirty folders with warning
            logger.warning(
                "Skipping dirty folder (has uncommitted changes): %s", folder
            )
            print(f"⚠️  Skipping (dirty): {folder}")
            result["skipped"].append(folder)
        else:
            # Clean folder - delete or report
            if dry_run:
                print(f"Would delete: {folder}")
                # Don't add to deleted list in dry run - it wasn't actually deleted
            else:
                if delete_session_folder(session):
                    print(f"Deleted: {folder}")
                    result["deleted"].append(folder)
                else:
                    print(f"Failed to delete: {folder}")
                    result["skipped"].append(folder)

    if not stale_sessions:
        print("No stale sessions to clean up.")

    return result
