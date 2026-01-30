"""Session management for vscodeclaude feature.

Handles JSON file I/O for session tracking and VSCode process checking.
"""

import json
import logging
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import psutil

from .types import VSCodeClaudeSession, VSCodeClaudeSessionStore

logger = logging.getLogger(__name__)

VSCODE_PROCESS_NAME = "code"


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
    Note: On Windows, the PID from launch may be a launcher that exits.
          Use is_vscode_open_for_folder() for more reliable folder-based check.
    """
    if pid is None:
        return False

    if not psutil.pid_exists(pid):
        return False
    try:
        process = psutil.Process(pid)
        return VSCODE_PROCESS_NAME in process.name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


# Cache for VSCode processes to avoid repeated slow process iteration
_vscode_process_cache: dict[str, list[dict[str, Any]]] | None = None


def _get_vscode_processes(refresh: bool = False) -> list[dict[str, Any]]:
    """Get list of VSCode processes with their command lines.

    Caches results to avoid repeated slow process iteration.
    Call with refresh=True at the start of operations to refresh the cache.

    Returns:
        List of dicts with 'pid' and 'cmdline_lower' keys
    """
    global _vscode_process_cache

    if _vscode_process_cache is not None and not refresh:
        return _vscode_process_cache.get("processes", [])

    logger.debug("Scanning VSCode processes (this may be slow on Windows)...")
    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_name = proc.info.get("name", "") or ""
            if VSCODE_PROCESS_NAME not in proc_name.lower():
                continue

            cmdline = proc.info.get("cmdline") or []
            # Store lowercase cmdline for fast matching
            cmdline_lower = " ".join(str(arg).lower() for arg in cmdline)
            processes.append(
                {
                    "pid": proc.info.get("pid"),
                    "cmdline_lower": cmdline_lower,
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    _vscode_process_cache = {"processes": processes}
    logger.debug("Cached %d VSCode processes", len(processes))
    # Log first cmdline for debugging (truncated)
    if processes:
        sample = processes[0].get("cmdline_lower", "")[:200]
        logger.debug("Sample VSCode cmdline: %s...", sample)
    return processes


def clear_vscode_process_cache() -> None:
    """Clear the VSCode process cache.

    Call this at the start of operations to ensure fresh data.
    """
    global _vscode_process_cache
    _vscode_process_cache = None


def is_vscode_open_for_folder(folder_path: str) -> tuple[bool, int | None]:
    """Check if any VSCode process has the folder open.

    More reliable than PID-based check on Windows where the launcher
    process exits immediately after spawning VSCode.

    Uses cached process list for performance - call clear_vscode_process_cache()
    at the start of batch operations to refresh.

    Args:
        folder_path: Full path to the workspace folder

    Returns:
        Tuple of (is_open, pid) where:
        - is_open: True if VSCode has this folder open
        - pid: The VSCode process PID if found, None otherwise
    """
    folder_str = str(folder_path).lower()
    # Also check for workspace file pattern
    folder_name = Path(folder_path).name.lower()

    for proc_info in _get_vscode_processes():
        cmdline_lower = proc_info.get("cmdline_lower", "")
        # Check if folder path or folder name appears in command line
        if folder_str in cmdline_lower or folder_name in cmdline_lower:
            logger.debug(
                "Found VSCode with folder %s (pid=%s)",
                folder_name,
                proc_info.get("pid"),
            )
            return True, proc_info.get("pid")

    logger.debug(
        "No VSCode process found for folder: %s (checked %d processes)",
        folder_name,
        len(_get_vscode_processes()),
    )
    return False, None


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
