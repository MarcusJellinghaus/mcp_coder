"""Session management for vscodeclaude feature.

Handles JSON file I/O for session tracking and VSCode process checking.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import psutil

from ...utils.user_app_data import get_user_app_data_dir
from .config import sanitize_folder_name
from .helpers import load_to_be_deleted
from .types import VSCodeClaudeSession, VSCodeClaudeSessionStore

# Optional Windows-only imports for window title detection
try:
    import win32gui
    import win32process

    HAS_WIN32GUI = True
except ImportError:
    HAS_WIN32GUI = False

logger = logging.getLogger(__name__)

# Exact process names for VSCode on each platform.
# Using exact match prevents false positives from processes whose names
# contain "code" as a substring (e.g. "my-code-tool.exe").
VSCODE_PROCESS_NAMES = {"code.exe", "code"}  # Windows / Linux+macOS


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


def check_vscode_running(
    pid: int | None,
    expected_create_time: float | None,
) -> bool:
    """Check if VSCode process is still running and is the expected process.

    Args:
        pid: Process ID to check (None returns False)
        expected_create_time: Stored ``create_time`` for the process. When
            provided, must match the live process's ``create_time`` within
            one second; otherwise the PID has been reused by a different
            process and this returns False. Pass ``None`` to skip the
            identity check (loose name-only behaviour).

    Returns:
        True if process exists, is a running VSCode process, and (when
        expected_create_time is provided) has a matching create_time.
    """
    if pid is None:
        logger.debug("check_vscode_running: pid=None -> False")
        return False

    if not psutil.pid_exists(pid):
        logger.debug("check_vscode_running: pid=%d does not exist -> False", pid)
        return False
    try:
        process = psutil.Process(pid)
        if process.name().lower() not in VSCODE_PROCESS_NAMES:
            logger.debug(
                "check_vscode_running: pid=%d name=%s -> False",
                pid,
                process.name(),
            )
            return False
        if expected_create_time is not None:
            actual_create_time = process.create_time()
            if abs(actual_create_time - expected_create_time) > 1.0:
                logger.debug(
                    "check_vscode_running: pid=%d create_time mismatch "
                    "(expected=%.3f actual=%.3f) -> False",
                    pid,
                    expected_create_time,
                    actual_create_time,
                )
                return False
        logger.debug(
            "check_vscode_running: pid=%d name=%s -> True",
            pid,
            process.name(),
        )
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        logger.debug("check_vscode_running: pid=%d access error -> False", pid)
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
    global _vscode_process_cache  # pylint: disable=global-statement  # module-level singleton

    if _vscode_process_cache is not None and not refresh:
        return _vscode_process_cache.get("processes", [])

    logger.debug("Scanning VSCode processes (this may be slow on Windows)...")
    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            proc_name = proc.info.get("name", "") or ""
            if proc_name.lower() not in VSCODE_PROCESS_NAMES:
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
    global _vscode_process_cache  # pylint: disable=global-statement  # module-level singleton
    _vscode_process_cache = None


# Cache for VSCode window titles (Windows only).
# Each entry is (pid, title) where pid is the PID of the process that owns
# the window. Storing the PID is what lets is_vscode_window_open_for_folder
# bind a title match to the specific VSCode that has the folder open.
_vscode_window_cache: list[tuple[int, str]] | None = None


# Cache for VSCode process PIDs to avoid repeated lookups
_vscode_pids_cache: set[int] | None = None


def _get_vscode_pids() -> set[int]:
    """Get set of VSCode process IDs.

    Returns:
        Set of PIDs for Code.exe processes
    """
    global _vscode_pids_cache  # pylint: disable=global-statement  # module-level singleton
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


def _get_vscode_window_titles(refresh: bool = False) -> list[tuple[int, str]]:
    """Return list of (pid, title) pairs for visible VSCode windows.

    Uses win32gui to enumerate windows owned by Code.exe processes.
    This catches all VSCode windows including integrated terminals
    that don't have "Visual Studio Code" in the title.

    The PID is the owning process so callers can bind a title match to
    the specific VSCode instance that has the folder open, eliminating
    cross-process title-leak false positives.

    Args:
        refresh: Force refresh of cached titles

    Returns:
        List of (pid, title) tuples for visible VSCode-owned windows,
        or empty list on non-Windows.
    """
    global _vscode_window_cache, _vscode_pids_cache  # pylint: disable=global-statement  # module-level singleton

    if not HAS_WIN32GUI:
        return []

    if _vscode_window_cache is not None and not refresh:
        return _vscode_window_cache

    # Refresh PID cache when refreshing window cache
    if refresh:
        _vscode_pids_cache = None

    vscode_pids = _get_vscode_pids()
    logger.debug("Found %d VSCode processes: %s", len(vscode_pids), vscode_pids)

    entries: list[tuple[int, str]] = []

    def enum_callback(hwnd: int, _: Any) -> bool:
        """Callback for EnumWindows.

        Returns:
            Always True to continue enumeration.
        """
        try:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    # Check if window belongs to a VSCode process
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if pid in vscode_pids:
                        entries.append((pid, title))
        except (
            Exception
        ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            pass  # Ignore errors for individual windows
        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.warning("Failed to enumerate windows: %s", e)
        return []

    _vscode_window_cache = entries
    logger.debug("Found %d VSCode windows: %s", len(entries), entries)
    return entries


def clear_vscode_window_cache() -> None:
    """Clear the VSCode window title cache."""
    global _vscode_window_cache, _vscode_pids_cache  # pylint: disable=global-statement  # module-level singleton
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

    The title's owning PID must also belong to a VSCode process whose cmdline
    references ``folder_path``. This eliminates cross-process title-leak where
    an unrelated VSCode window's title happens to contain the issue number and
    repo name.

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
    folder_str = str(folder_path).lower()
    folder_name = Path(folder_path).name.lower()

    # For vscodeclaude sessions: Only match if issue number is in window title
    # Workspace windows have format: "[#N stage] title - repo - Visual Studio Code"
    # This prevents matching the main repo window ("repo - Visual Studio Code")
    if issue_number is not None and repo:
        repo_name = repo.split("/")[-1].lower() if "/" in repo else repo.lower()
        # Require "[#N" bracket prefix to match vscodeclaude workspace title format:
        # "[#N stage_short] title - repo_name"
        # This avoids false positives from GitHub extension or other tools
        # that may show issue numbers without the bracket (e.g. "#458 - mcp_coder")
        issue_pattern = f"[#{issue_number}"

        # Bind the title match to the VSCode process that actually has the
        # folder open: only accept a title from a PID whose cmdline references
        # the folder.
        matching_pids = {
            proc["pid"]
            for proc in _get_vscode_processes()
            if folder_str in proc.get("cmdline_lower", "")
            or folder_name in proc.get("cmdline_lower", "")
        }

        for pid, title in titles:
            if pid not in matching_pids:
                continue
            title_lower = title.lower()
            # Both issue number (with bracket) AND repo name must be present
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
        ):
            if Path(session["folder"]).name not in to_be_deleted:
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
        if entry.is_dir() and pattern.match(entry.name):
            if entry.name not in to_be_deleted and entry.name not in session_folders:
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


def session_has_artifacts(folder: str) -> bool:
    """Check if the session working folder still exists on disk.

    A session's only meaningful artifact is its working folder. The
    `.code-workspace` file is a launcher that points at the folder; without
    the folder it points at nothing. If the folder is gone, any still-running
    VSCode process is a zombie for this session and any lingering workspace
    file is an orphan to be cleaned up.

    Args:
        folder: Full path to the session's working folder

    Returns:
        True if the folder exists.
    """
    return Path(folder).exists()


def is_session_active(session: VSCodeClaudeSession) -> bool:
    """Check if a session's VSCode is currently running.

    Single entry point for all VSCode detection logic. Callers should always
    use this instead of assembling individual checks themselves.

    Uses a fallback chain that prefers false-positives (skip cleanup) over
    false-negatives (delete live folder):

    1. On Windows with issue_num + repo: window-title match -> active.
    2. Stored PID still alive -> active.
    3. Cmdline match on folder -> active (and refresh stored PID if the
       found PID differs from the stored one, so subsequent calls can hit
       the fast PID path).
    4. Otherwise -> inactive.

    Pre-condition: only runs checks if session artifacts exist. If both the
    folder and workspace file are gone, any matching process is a zombie
    and this short-circuits to False with a DEBUG line.

    Every other call emits exactly one INFO line naming the deciding
    criterion. Windows fallback paths carry a ``window-title not found —
    potentially stale`` note so silent title-detection degradation surfaces
    in logs even when a later check succeeds.

    Side effect: on cmdline match where the found PID differs from the
    stored ``vscode_pid``, calls ``update_session_pid(folder, found_pid)``,
    which writes ``sessions.json``.

    Args:
        session: Session to check

    Returns:
        True if any evidence of a live VSCode session for this folder.
    """
    folder = session.get("folder", "")
    issue_num = session.get("issue_number")
    repo = session.get("repo")
    if not session_has_artifacts(folder):
        logger.debug("is_session_active #%s: no artifacts -> False", issue_num)
        return False

    title_checked = False
    if HAS_WIN32GUI and issue_num is not None and repo is not None:
        title_checked = True
        if is_vscode_window_open_for_folder(
            folder,
            issue_number=issue_num,
            repo=repo,
        ):
            logger.info("is_session_active #%s: active (window-title match)", issue_num)
            return True

    stale = ", window-title not found \u2014 potentially stale" if title_checked else ""
    stored_pid = session.get("vscode_pid")
    stored_create_time = session["vscode_pid_create_time"]

    if check_vscode_running(stored_pid, stored_create_time):
        logger.info(
            "is_session_active #%s: active (PID %s alive%s)",
            issue_num,
            stored_pid,
            stale,
        )
        return True

    is_open, found_pid = is_vscode_open_for_folder(folder)
    if is_open:
        if found_pid is not None and found_pid != stored_pid:
            logger.debug(
                "is_session_active #%s: refreshing stored PID %s -> %s",
                issue_num,
                stored_pid,
                found_pid,
            )
            update_session_pid(folder, found_pid)
        logger.info(
            "is_session_active #%s: active (cmdline match PID=%s%s)",
            issue_num,
            found_pid,
            stale,
        )
        return True

    prefix = "no window / " if title_checked else ""
    logger.info(
        "is_session_active #%s: inactive (%sPID %s gone / no cmdline match)",
        issue_num,
        prefix,
        stored_pid,
    )
    return False


def build_active_session_set(
    sessions: list[VSCodeClaudeSession],
) -> dict[str, bool]:
    """Build active-set snapshot.

    Side effects: clears VSCode window/process caches, may call
    update_session_pid for active sessions whose stored PID differs
    from the currently-detected PID.

    Returns:
        Mapping of each session's folder path to a boolean indicating
        whether that session is currently active.
    """
    clear_vscode_window_cache()
    clear_vscode_process_cache()
    logger.info("Checking %d session(s)...", len(sessions))
    active_set: dict[str, bool] = {}
    for session in sessions:
        is_active = is_session_active(session)
        active_set[session["folder"]] = is_active
        if is_active:
            _, found_pid = is_vscode_open_for_folder(session["folder"])
            if found_pid is not None and found_pid != session.get("vscode_pid"):
                update_session_pid(session["folder"], found_pid)
    return active_set


def update_session_pid(folder: str, pid: int) -> None:
    """Atomically writes both vscode_pid and vscode_pid_create_time.

    Captures ``psutil.Process(pid).create_time()`` and stores it alongside
    ``vscode_pid`` in the same persistence step. This is the only populator
    of ``vscode_pid_create_time``; the field self-populates on the first
    cmdline-match refresh after launch.

    Args:
        folder: Session folder path
        pid: New VSCode process ID
    """
    try:
        create_time: float | None = psutil.Process(pid).create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        create_time = None
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
