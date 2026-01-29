"""Session management for vscodeclaude feature.

Handles JSON file I/O for session tracking and VSCode process checking.
"""

import json
import logging
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from .types import VSCodeClaudeSession, VSCodeClaudeSessionStore

logger = logging.getLogger(__name__)


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


def check_vscode_running(pid: int | None) -> bool:
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
) -> VSCodeClaudeSession | None:
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
