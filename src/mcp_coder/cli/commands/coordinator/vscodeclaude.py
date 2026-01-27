"""VSCode Claude session management for interactive workflow stages."""

import json
import logging
import platform
import re
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
