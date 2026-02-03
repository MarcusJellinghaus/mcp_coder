#!/usr/bin/env python3
"""
Safe folder deletion utility for Windows.

Two modes of operation:

1. DIAGNOSE (default): Scans entire folder with handle64.exe upfront to show
   all locking processes. Useful for understanding what's blocking deletion.

2. DELETE (--delete): Tries to delete immediately, only runs handle64.exe on
   specific files that fail. Faster when most files aren't locked.

Escalation strategy for --delete:
    1. Try shutil.rmtree
    2. If file locked, move it to temp
    3. If move fails and --kill-lockers, find and kill locker, retry move
    4. Repeat until done or max retries

Usage:
    python tools/safe_delete_folder.py <folder_path>                    # diagnose
    python tools/safe_delete_folder.py <folder_path> --delete           # delete
    python tools/safe_delete_folder.py <folder_path> --delete -k        # delete + kill
"""

from __future__ import annotations

# =============================================================================
# Protected Processes - NEVER kill these, just report as blocking
# =============================================================================
PROTECTED_PROCESSES: set[str] = {
    "explorer.exe",      # Windows Explorer - killing causes desktop issues
}


import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class DiagnosticResult:
    """Results from folder diagnostics."""

    path: Path
    exists: bool = False
    is_directory: bool = False
    is_empty: bool = True
    contents: list[str] = field(default_factory=list)
    permissions_ok: bool = False
    locking_processes: list[str] = field(default_factory=list)


# =============================================================================
# Handle64.exe Management
# =============================================================================


def _get_sysinternals_dir() -> Path:
    """Get %LOCALAPPDATA%\\Sysinternals\\ directory."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        return Path(local_app_data) / "Sysinternals"
    return Path.home() / ".sysinternals"


def _download_handle_executable() -> str | None:
    """Download Sysinternals Handle tool if not present."""
    import io
    import urllib.request
    import zipfile

    target_dir = _get_sysinternals_dir()
    url = "https://download.sysinternals.com/files/Handle.zip"
    exe_name = "handle64.exe" if sys.maxsize > 2**32 else "handle.exe"
    target_path = target_dir / exe_name

    if target_path.exists():
        return str(target_path)

    print(f"  Downloading handle64.exe from {url}...")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            zip_data = response.read()

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            for name in zf.namelist():
                if name.lower() == exe_name.lower():
                    target_dir.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(target_path, "wb") as dst:
                        dst.write(src.read())
                    print(f"  Downloaded to {target_path}")
                    return str(target_path)
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  Warning: Download failed: {e}")
        return None


def _find_handle_executable() -> str | None:
    """Find handle64.exe in PATH or standard locations, auto-download if needed."""
    exe_name = "handle64.exe" if sys.maxsize > 2**32 else "handle.exe"

    # Check PATH
    try:
        result = subprocess.run(
            ["where", exe_name], capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Check standard location
    exe_path = _get_sysinternals_dir() / exe_name
    if exe_path.exists():
        return str(exe_path)

    # Auto-download
    return _download_handle_executable()


def _run_handle_exe(handle_exe: str, path: Path) -> list[str]:
    """Run handle64.exe and return list of locking processes."""
    print("  Running handle64.exe (may take 1-3 minutes on first run)...")

    try:
        result = subprocess.run(
            [handle_exe, "-accepteula", "-nobanner", str(path)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        print("  handle64.exe done.")

        locking = []
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if line.strip() and "No matching handles found" not in line:
                    locking.append(line.strip())
        return locking

    except subprocess.TimeoutExpired:
        return ["[ERROR] handle64.exe timed out"]
    except OSError as e:
        return [f"[ERROR] {e}"]


# =============================================================================
# Process Killing
# =============================================================================


def _kill_detected_lockers(locking_processes: list[str]) -> list[str]:
    """Kill processes detected by handle64.exe, skipping protected ones."""
    if sys.platform != "win32":
        return []

    results = []

    for proc_info in locking_processes:
        if proc_info.startswith("[ERROR]") or proc_info.startswith("[INFO]"):
            continue

        # Parse: "cmd.exe  pid: 35140  type: File  ..."
        match = re.search(r"^(\S+)\s+pid:\s*(\d+)", proc_info)
        if not match:
            continue

        proc_name = match.group(1)
        pid = int(match.group(2))

        # Skip protected processes
        if proc_name.lower() in {p.lower() for p in PROTECTED_PROCESSES}:
            results.append(f"PROTECTED (not killed): {proc_name} (PID {pid})")
            continue

        try:
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                results.append(f"KILLED: {proc_name} (PID {pid})")
            elif "not found" in result.stderr.lower():
                results.append(f"ALREADY GONE: {proc_name} (PID {pid})")
            else:
                results.append(f"FAILED: {proc_name} (PID {pid})")
        except Exception as e:  # noqa: BLE001
            results.append(f"ERROR: {proc_name} (PID {pid}): {e}")

    return results


# =============================================================================
# Folder Deletion
# =============================================================================

MAX_DELETE_RETRIES = 50  # Max locked files to move before giving up


def _rmtree_remove_readonly(func: Callable[..., None], path: str, _exc: object) -> None:
    """Error handler for shutil.rmtree to handle readonly files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _move_file_to_temp(filepath: Path) -> tuple[bool, str]:
    """Move a locked file to temp directory."""
    import tempfile
    import uuid

    temp_base = Path(tempfile.gettempdir()) / "safe_delete_staging"
    unique_name = f"{filepath.stem}_{uuid.uuid4().hex[:8]}{filepath.suffix}"
    temp_dest = temp_base / unique_name

    try:
        temp_base.mkdir(parents=True, exist_ok=True)
        shutil.move(str(filepath), str(temp_dest))
        return True, str(temp_dest)
    except (PermissionError, OSError) as e:
        return False, str(e)


def _extract_path_from_error(error: PermissionError | OSError) -> Path | None:
    """Extract file path from a PermissionError or OSError."""
    # Error format: [WinError 5] Access is denied: 'C:\\path\\to\\file'
    if error.filename:
        return Path(error.filename)
    # Try parsing from string representation
    match = re.search(r"['\"]([^'\"]+)['\"]$", str(error))
    if match:
        return Path(match.group(1))
    return None


def _delete_folder(
    path: Path, kill_lockers: bool = False, quiet: bool = False
) -> tuple[bool, str, list[str], list[str]]:
    """Delete folder with escalating strategies for locked files.

    Strategy (escalates as needed):
        1. Try delete
        2. If fails, try move locked file to temp
        3. If move fails AND kill_lockers=True, kill locker, retry move
        4. Retry delete

    Args:
        path: Folder to delete
        kill_lockers: If True, kill locking processes as last resort
        quiet: Suppress progress output

    Returns:
        Tuple of (success, message, moved_files, killed_processes)
    """
    if not path.exists():
        return True, "Already deleted", [], []

    moved_files: list[str] = []
    killed_procs: list[str] = []

    def log(msg: str) -> None:
        if not quiet:
            print(f"  {msg}")

    for _ in range(MAX_DELETE_RETRIES):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=_rmtree_remove_readonly)
            else:
                shutil.rmtree(path, onerror=_rmtree_remove_readonly)  # pylint: disable=deprecated-argument

            if not path.exists():
                return True, "Deleted successfully", moved_files, killed_procs
            return False, "Folder still exists after rmtree", moved_files, killed_procs

        except PermissionError as e:
            locked_path = _extract_path_from_error(e)
            if not locked_path or not locked_path.exists():
                return (
                    False,
                    f"Permission denied (cannot identify file): {e}",
                    moved_files,
                    killed_procs,
                )

            # Step 1: Try move
            moved, result = _move_file_to_temp(locked_path)
            if moved:
                log(f"MOVED: {locked_path.name}")
                moved_files.append(f"{locked_path.name} -> {result}")
                continue  # Retry delete

            # Step 2: Move failed - escalate to kill (if allowed)
            if not kill_lockers:
                return (
                    False,
                    f"Cannot move locked file: {locked_path} (use --kill-lockers)",
                    moved_files,
                    killed_procs,
                )

            log(f"LOCKED: {locked_path.name} - finding locker...")
            handle_exe = _find_handle_executable()
            if handle_exe:
                lockers = _run_handle_exe(handle_exe, locked_path)
                if lockers:
                    kill_results = _kill_detected_lockers(lockers)
                    for msg in kill_results:
                        log(msg)
                        killed_procs.append(msg)
                    if any("KILLED" in msg for msg in kill_results):
                        time.sleep(1)  # Wait for handles to release

            # Step 3: Try move again after kill
            moved, result = _move_file_to_temp(locked_path)
            if moved:
                log(f"MOVED: {locked_path.name}")
                moved_files.append(f"{locked_path.name} -> {result}")
                continue  # Retry delete

            # Can't handle this file
            return (
                False,
                f"Cannot delete or move: {locked_path}",
                moved_files,
                killed_procs,
            )

        except OSError as e:
            return False, f"OS error: {e}", moved_files, killed_procs

    return (
        False,
        f"Too many locked files (>{MAX_DELETE_RETRIES})",
        moved_files,
        killed_procs,
    )


# =============================================================================
# Diagnostics
# =============================================================================


def diagnose_folder(path: Path) -> DiagnosticResult:
    """Run diagnostics on a folder."""
    result = DiagnosticResult(path=path)

    result.exists = path.exists()
    if not result.exists:
        return result

    result.is_directory = path.is_dir()
    if not result.is_directory:
        return result

    try:
        result.contents = [item.name for item in path.iterdir()]
        result.is_empty = len(result.contents) == 0
    except PermissionError:
        pass

    result.permissions_ok = os.access(path, os.W_OK)

    # Find locking processes
    handle_exe = _find_handle_executable()
    if handle_exe:
        result.locking_processes = _run_handle_exe(handle_exe, path)
    else:
        result.locking_processes = ["[INFO] handle64.exe not available"]

    return result


def print_diagnostic_report(diag: DiagnosticResult) -> None:
    """Print diagnostic report."""
    print(f"\nPath: {diag.path}")
    print(f"Exists: {diag.exists}")

    if not diag.exists:
        print("[!] Folder does not exist")
        return

    print(f"Is Directory: {diag.is_directory}")
    print(f"Is Empty: {diag.is_empty}")
    print(f"Permissions OK: {diag.permissions_ok}")

    if diag.contents and not diag.is_empty:
        print(f"Contents: {len(diag.contents)} items")

    if diag.locking_processes:
        print("\nLocking processes:")
        for proc in diag.locking_processes:
            print(f"  {proc}")


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete folders by killing locking processes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Diagnose locks (default behavior)
    python tools/safe_delete_folder.py "C:\\path\\folder"

    # Delete after killing lockers
    python tools/safe_delete_folder.py "C:\\path\\folder" --delete --kill-lockers
        """,
    )
    parser.add_argument("paths", nargs="+", help="Folder path(s) to process")
    parser.add_argument("--delete", action="store_true", help="Delete the folder(s)")
    parser.add_argument(
        "--kill-lockers", "-k", action="store_true", help="Kill locking processes"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()
    exit_code = 0

    for path_str in args.paths:
        path = Path(path_str).resolve()

        if not args.quiet:
            print(f"\n{'=' * 50}")
            print(f"Processing: {path}")
            print("=" * 50)

        if not args.delete:
            # DIAGNOSE mode: scan entire folder with handle64 upfront
            diag = diagnose_folder(path)
            if not args.quiet:
                print_diagnostic_report(diag)
            if diag.exists:
                print("\n[!] Use --delete to delete the folder")
            continue

        # DELETE mode: skip upfront diagnose, handle locks as needed
        if not path.exists():
            print("\n[OK] Already deleted")
            continue

        # Delete with escalating strategy:
        # 1. Try delete
        # 2. If fails, move locked file
        # 3. If move fails, kill locker (if --kill-lockers), retry move
        print(f"\n[...] Deleting {path}...")
        success, message, moved_files, killed_procs = _delete_folder(
            path, kill_lockers=args.kill_lockers, quiet=args.quiet
        )

        if not args.quiet:
            if moved_files:
                print(f"\n  Summary: Moved {len(moved_files)} file(s) to temp")
            if killed_procs:
                print(f"  Summary: {len(killed_procs)} process action(s)")

        if success:
            print(f"\n[OK] {message}")
        else:
            print(f"\n[FAIL] {message}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
