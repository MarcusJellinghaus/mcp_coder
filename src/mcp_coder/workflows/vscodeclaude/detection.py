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

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .sessions import (
    HAS_WIN32GUI,
    LAUNCH_GRACE_SECONDS,
    _get_vscode_pids,
    _get_vscode_processes,
    _get_vscode_window_titles,
    check_vscode_running,
)
from .types import DetectionSignals, VSCodeClaudeSession


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
        captured_at=datetime.now(timezone.utc),
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
    """Age of the session in seconds, or ``inf`` if ``started_at`` is unusable."""
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
