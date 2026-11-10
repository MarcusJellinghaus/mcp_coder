"""Session management for vscodeclaude feature.

Handles JSON file I/O for session tracking.
"""

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from ...utils.user_app_data import get_user_app_data_dir
from .config import sanitize_folder_name
from .detection import get_pid_create_time
from .helpers import load_to_be_deleted
from .types import VSCodeClaudeSession, VSCodeClaudeSessionStore

logger = logging.getLogger(__name__)


def get_sessions_file_path() -> Path:
    """Get path to sessions JSON file.

    Returns:
        Path to ~/.mcp_coder/coordinator_cache/vscodeclaude_sessions.json.
    """
    return (
        get_user_app_data_dir("mcp_coder")
        / "coordinator_cache"
        / "vscodeclaude_sessions.json"
    )


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
        for session in data["sessions"]:
            session.setdefault("vscode_pid_create_time", None)
            session.setdefault("last_active", None)
            session.setdefault("last_active_rule", None)
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
    store["last_updated"] = datetime.now(UTC).isoformat()
    sessions_file.write_text(json.dumps(store, indent=2), encoding="utf-8")


def get_session_for_issue(
    repo_full_name: str,
    issue_number: int,
    workspace_base: str,
) -> VSCodeClaudeSession | None:
    """Find existing session for an issue.

    Excludes sessions whose folder is in the .to_be_deleted registry.
    Returns None with an error log if multiple active sessions match.

    Args:
        repo_full_name: "owner/repo" format
        issue_number: GitHub issue number
        workspace_base: Path to workspace directory

    Returns:
        Session dict if found, None otherwise
    """
    store = load_sessions()
    to_be_deleted = load_to_be_deleted(workspace_base)

    matches: list[VSCodeClaudeSession] = []
    for session in store["sessions"]:
        if (
            session["repo"] == repo_full_name
            and session["issue_number"] == issue_number
        ) and Path(session["folder"]).name not in to_be_deleted:
            matches.append(session)

    if len(matches) > 1:
        logger.error("Multiple active folders for %s #%d", repo_full_name, issue_number)
        return None
    return matches[0] if matches else None


def warn_orphan_folders(
    workspace_base: str,
    repo_full_name: str,
    issue_number: int,
    session_folders: set[str],
    to_be_deleted: set[str],
) -> None:
    r"""Scan disk for folders matching the issue that aren't tracked.

    Checks for {base} and {base}-folder\d+ folders on disk that are
    not in sessions.json and not in .to_be_deleted. Logs a warning
    for each orphan found.

    Note: repo_full_name is "owner/repo" format. The short repo name
    is extracted via split("/")[-1] before calling sanitize_folder_name.

    Args:
        workspace_base: Path to workspace directory
        repo_full_name: "owner/repo" format
        issue_number: GitHub issue number
        session_folders: Set of folder names from active sessions
        to_be_deleted: Set of folder names from soft-delete registry
    """
    short_repo_name = repo_full_name.split("/")[-1]
    sanitized_repo = sanitize_folder_name(short_repo_name)
    base_name = f"{sanitized_repo}_{issue_number}"
    pattern = re.compile(rf"^{re.escape(base_name)}(-folder\d+)?$")

    workspace_path = Path(workspace_base)
    if not workspace_path.exists():
        return

    for entry in workspace_path.iterdir():
        if (
            entry.is_dir()
            and pattern.match(entry.name)
            and entry.name not in to_be_deleted
            and entry.name not in session_folders
        ):
            logger.warning("Orphan folder detected: %s", entry.name)


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


def update_session_pid(folder: str, pid: int) -> None:
    """Atomically writes both vscode_pid and vscode_pid_create_time.

    Captures ``psutil.Process(pid).create_time()`` and stores it alongside
    ``vscode_pid`` in the same persistence step. This is the only populator
    of ``vscode_pid_create_time``.

    Args:
        folder: Session folder path
        pid: New VSCode process ID
    """
    create_time = get_pid_create_time(pid)
    store = load_sessions()
    for session in store["sessions"]:
        if session["folder"] == folder:
            session["vscode_pid"] = pid
            session["vscode_pid_create_time"] = create_time
            break
    save_sessions(store)


def update_session_status(folder: str, new_status: str) -> bool:
    """Update the status field for an existing session.

    Args:
        folder: Session folder path (used as session identifier)
        new_status: New status label to set

    Returns:
        True if session was found and updated, False otherwise
    """
    store = load_sessions()
    for session in store["sessions"]:
        if session["folder"] == folder:
            session["status"] = new_status
            save_sessions(store)
            return True
    return False
