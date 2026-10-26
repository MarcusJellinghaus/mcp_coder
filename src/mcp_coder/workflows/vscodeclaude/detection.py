"""Detection snapshot + signal gathering for vscodeclaude session state.

This module is the ``detect`` stage of the detect -> assess -> decide ->
render/apply pipeline and is the **only** place that touches psutil/win32. It
produces :class:`DetectionSignals`; everything downstream is pure.

The whole point of :class:`DetectionSnapshot` is R4 (no age-skew): all three
module caches (processes, window titles, PIDs) are populated in immediate
succession so no signal ages relative to another. ``gather_signals`` then reads
only the frozen snapshot + the session dict + ``Path`` existence + the stored
PID, computing the seven raw signals plus ``directory_empty`` / ``within_grace``
as plain bools.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from .types import DetectionSignals, VSCodeClaudeSession

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


# Seconds after launch during which a negative window-title check is not
# trusted (covers VSCode cold-start and extension reinstall delays). Beyond
# this window the title check is authoritative on Windows.
LAUNCH_GRACE_SECONDS = 60.0


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
        except (  # noqa: S110 -- one bad window must not abort the enumeration
            Exception
        ):  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            pass  # Ignore errors for individual windows
        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
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


def get_pid_create_time(pid: int) -> float | None:
    """Return a process's ``create_time`` for identity matching, or None.

    Captures ``psutil.Process(pid).create_time()``; returns None when the process
    is gone or inaccessible (the loose name-only fallback used by callers that
    skip the create_time identity check).

    Args:
        pid: Process ID to query.

    Returns:
        The process ``create_time`` in Unix epoch seconds, or None on failure.
    """
    try:
        create_time: float = psutil.Process(pid).create_time()
        return create_time
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


@dataclass(frozen=True)
class DetectionSnapshot:
    """Immutable snapshot of all VSCode detection state at one instant.

    Capturing processes, window titles, and PIDs together (R4) means no raw
    signal can age relative to another across a single run.
    """

    processes: tuple[dict[str, Any], ...]  # each: pid + cmdline_lower
    window_titles: tuple[tuple[int, str], ...]  # (owning_pid, title)
    pids: frozenset[int]
    captured_at: datetime


def capture_detection_snapshot() -> DetectionSnapshot:
    """Populate ALL THREE caches at one instant and freeze the result.

    Refreshes the process cache, then the window-title cache (which also
    refreshes the PID cache), then reads the PID cache. Capturing them in
    immediate succession is what guarantees R4 (no age-skew between signals).

    Returns:
        A frozen :class:`DetectionSnapshot` over the just-refreshed caches.
    """
    processes = _get_vscode_processes(refresh=True)
    window_titles = _get_vscode_window_titles(refresh=True)
    pids = _get_vscode_pids()
    return DetectionSnapshot(
        processes=tuple(processes),
        window_titles=tuple(window_titles),
        pids=frozenset(pids),
        captured_at=datetime.now(UTC),
    )


def _title_binds(
    snapshot: DetectionSnapshot,
    issue_number: int | None,
    repo: str | None,
) -> bool:
    """Whether a VSCode window title binds to this session's issue + repo.

    Ports the ``[#N`` bracket + repo-name matching from
    ``is_vscode_window_open_for_folder``, reading window titles from the frozen
    snapshot. A workspace window has the format
    ``[#N stage] title - repo_name - Visual Studio Code``; requiring the
    ``[#N`` bracket avoids false positives from tools that show bare issue
    numbers (e.g. ``#458 - mcp_coder``). Title-positive is authoritative; it is
    intentionally independent of cmdline/PID so a restored window (no folder in
    cmdline) still reports ``title_match=True``.

    Returns:
        ``True`` when a snapshot window title binds to this issue + repo,
        ``False`` otherwise.
    """
    if not HAS_WIN32GUI:
        return False
    if issue_number is None or not repo:
        return False

    repo_name = repo.split("/")[-1].lower() if "/" in repo else repo.lower()
    issue_pattern = f"[#{issue_number}"
    for _pid, title in snapshot.window_titles:
        if issue_pattern in title and repo_name in title.lower():
            return True
    return False


def _cmdline_scan(
    snapshot: DetectionSnapshot, folder_path: str
) -> tuple[bool, int | None]:
    """Scan snapshot processes for one referencing the folder by path or name.

    Returns:
        ``(matched, pid)`` where ``pid`` is the first matching VSCode PID, or
        ``(False, None)`` when no process references the folder.
    """
    folder_str = str(folder_path).lower()
    folder_name = Path(folder_path).name.lower()
    for proc in snapshot.processes:
        cmdline_lower = proc.get("cmdline_lower", "")
        if folder_str in cmdline_lower or folder_name in cmdline_lower:
            return True, proc.get("pid")
    return False, None


def _session_age_seconds(session: VSCodeClaudeSession, now: datetime) -> float:
    """Age of the session in seconds, or ``inf`` if ``started_at`` is unusable.

    Returns:
        Seconds since ``started_at``, or ``float("inf")`` when it is missing or
        unparseable.
    """
    started_at_str = session.get("started_at", "")
    try:
        return (now - datetime.fromisoformat(started_at_str)).total_seconds()
    except (ValueError, TypeError):
        return float("inf")


def gather_signals(
    session: VSCodeClaudeSession, snapshot: DetectionSnapshot
) -> DetectionSignals:
    """Compute the seven raw signals for one session from the frozen snapshot.

    This is the IO/Windows boundary: it reads only the snapshot, the session
    dict, ``Path`` existence, and the stored PID. ``folder_exists`` and
    ``pid_alive`` are gathered INDEPENDENTLY (R6) — there is no folder-gone
    short-circuit, so a live process for a deleted folder stays reachable as a
    zombie precursor. ``directory_empty`` and ``within_grace`` are computed
    here as plain bools so the downstream ``types``/``decide`` stay pure.

    Returns:
        A frozen :class:`DetectionSignals` with the seven raw signals plus
        ``directory_empty`` and ``within_grace``.
    """
    folder = session["folder"]
    folder_path = Path(folder)
    folder_exists = folder_path.exists()
    directory_empty = folder_exists and not any(folder_path.iterdir())

    title_match = _title_binds(snapshot, session["issue_number"], session.get("repo"))
    cmdline_match, found_pid = _cmdline_scan(snapshot, folder)
    pid_alive = check_vscode_running(
        session.get("vscode_pid"), session["vscode_pid_create_time"]
    )

    age_seconds = _session_age_seconds(session, snapshot.captured_at)
    within_grace = age_seconds < LAUNCH_GRACE_SECONDS

    return DetectionSignals(
        folder_exists=folder_exists,
        title_match=title_match,
        cmdline_match=cmdline_match,
        pid_alive=pid_alive,
        found_pid=found_pid,
        age_seconds=age_seconds,
        within_grace=within_grace,
        directory_empty=directory_empty,
    )
