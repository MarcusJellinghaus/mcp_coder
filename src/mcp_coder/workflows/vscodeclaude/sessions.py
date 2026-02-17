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

# Optional Windows-only imports for window title detection
try:
    import win32gui
    import win32process

    HAS_WIN32GUI = True
except ImportError:
    HAS_WIN32GUI = False

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


# Cache for VSCode window titles (Windows only)
_vscode_window_cache: list[str] | None = None


# Cache for VSCode process PIDs to avoid repeated lookups
_vscode_pids_cache: set[int] | None = None


def _get_vscode_pids() -> set[int]:
    """Get set of VSCode process IDs.

    Returns:
        Set of PIDs for Code.exe processes
    """
    global _vscode_pids_cache
    if _vscode_pids_cache is not None:
        return _vscode_pids_cache

    pids: set[int] = set()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc_name = proc.info.get("name", "") or ""
            if proc_name.lower() == "code.exe":
                pids.add(proc.info.get("pid"))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    _vscode_pids_cache = pids
    return pids


def _get_vscode_window_titles(refresh: bool = False) -> list[str]:
    """Get list of VSCode window titles (Windows only).

    Uses win32gui to enumerate windows owned by Code.exe processes.
    This catches all VSCode windows including integrated terminals
    that don't have "Visual Studio Code" in the title.

    Args:
        refresh: Force refresh of cached titles

    Returns:
        List of VSCode window titles, or empty list on non-Windows
    """
    global _vscode_window_cache, _vscode_pids_cache

    if not HAS_WIN32GUI:
        return []

    if _vscode_window_cache is not None and not refresh:
        return _vscode_window_cache

    # Refresh PID cache when refreshing window cache
    if refresh:
        _vscode_pids_cache = None

    vscode_pids = _get_vscode_pids()
    logger.debug("Found %d VSCode processes: %s", len(vscode_pids), vscode_pids)

    titles: list[str] = []

    def enum_callback(hwnd: int, _: Any) -> bool:
        """Callback for EnumWindows."""
        try:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    # Check if window belongs to a VSCode process
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid in vscode_pids:
                        titles.append(title)
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # Ignore errors for individual windows
        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to enumerate windows: %s", e)
        return []

    _vscode_window_cache = titles
    logger.debug("Found %d VSCode windows: %s", len(titles), titles)
    return titles


def clear_vscode_window_cache() -> None:
    """Clear the VSCode window title cache."""
    global _vscode_window_cache, _vscode_pids_cache
    _vscode_window_cache = None
    _vscode_pids_cache = None


def is_vscode_window_open_for_folder(
    folder_path: str,
    issue_number: int | None = None,
    repo: str | None = None,
) -> bool:
    """Check if VSCode has a window open for the folder (Windows only).

    For vscodeclaude sessions with issue numbers, only matches windows with
    the issue number pattern (e.g., '[#219 ...'). This prevents false positives
    from matching the main repo window instead of the issue workspace window.

    Args:
        folder_path: Full path to the workspace folder
        issue_number: Optional issue number (required for reliable matching)
        repo: Optional repo full name 'owner/repo' (used with issue_number)

    Returns:
        True if a VSCode window matching the session is found
    """
    if not HAS_WIN32GUI:
        return False

    titles = _get_vscode_window_titles()
    folder_name = Path(folder_path).name.lower()

    # For vscodeclaude sessions: Only match if issue number is in window title
    # Workspace windows have format: "[#N stage] title - repo - Visual Studio Code"
    # This prevents matching the main repo window ("repo - Visual Studio Code")
    if issue_number is not None and repo:
        repo_name = repo.split("/")[-1].lower() if "/" in repo else repo.lower()
        issue_pattern = f"#{issue_number}"

        for title in titles:
            title_lower = title.lower()
            # Both issue number AND repo name must be present
            if issue_pattern in title and repo_name in title_lower:
                logger.debug(
                    "Found VSCode window for issue #%d (%s): %s",
                    issue_number,
                    repo_name,
                    title,
                )
                return True

    logger.debug(
        "No VSCode window found for folder: %s (issue=#%s, repo=%s)",
        folder_name,
        issue_number,
        repo,
    )
    return False


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


def session_has_artifacts(folder: str) -> bool:
    """Check if session folder or workspace file still exist on disk.

    A session's artifacts are its working folder and its .code-workspace file.
    If both are gone, any still-running VSCode process is a zombie for this
    session (it was launched with artifacts that have since been deleted).

    Args:
        folder: Full path to the session's working folder

    Returns:
        True if the folder or workspace file exists
    """
    folder_path = Path(folder)
    workspace_file = folder_path.parent / f"{folder_path.name}.code-workspace"
    return folder_path.exists() or workspace_file.exists()


def get_active_session_count() -> int:
    """Count sessions with running VSCode processes and existing artifacts.

    Returns:
        Number of sessions where VSCode PID is still running AND the session
        folder or workspace file still exists. Sessions where both artifacts
        are gone are excluded even if a VSCode process with a matching PID
        exists (zombie VSCode from a deleted session).
    """
    store = load_sessions()
    count = 0
    for session in store["sessions"]:
        folder = session.get("folder", "")
        if session_has_artifacts(folder) and check_vscode_running(
            session.get("vscode_pid")
        ):
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
