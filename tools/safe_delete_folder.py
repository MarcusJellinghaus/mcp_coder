#!/usr/bin/env python3
"""
Safe folder deletion utility for Windows.

Detects processes locking a folder using Sysinternals handle64.exe,
kills them, then deletes the folder.

Usage:
    python tools/safe_delete_folder.py <folder_path> --delete --kill-lockers
"""

from __future__ import annotations

# =============================================================================
# Protected Processes - NEVER kill these, just report as blocking
# =============================================================================
PROTECTED_PROCESSES: set[str] = {
    "explorer.exe",      # Windows Explorer - killing causes desktop issues
    "dwm.exe",           # Desktop Window Manager
    "csrss.exe",         # Client Server Runtime
    "winlogon.exe",      # Windows Logon
    "services.exe",      # Service Control Manager
    "lsass.exe",         # Local Security Authority
    "smss.exe",          # Session Manager
    "svchost.exe",       # Service Host (many services depend on it)
    "System",            # System process
    "wininit.exe",       # Windows Initialization
}

# =============================================================================
# Problematic Files - Move to temp instead of direct delete
# These files often remain locked even after process termination
# =============================================================================
PROBLEMATIC_FILE_PATTERNS: set[str] = {
    "_rust.pyd",         # Cryptography Rust bindings
    "_cffi_backend.pyd", # CFFI backend
    "_sqlite3.pyd",      # SQLite bindings
    "_ssl.pyd",          # SSL bindings
    "_hashlib.pyd",      # Hash library bindings
    ".pyd",              # Any Python DLL (fallback pattern)
    ".dll",              # Any DLL file
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
# Problematic File Handling
# =============================================================================


def _is_problematic_file(filepath: Path) -> bool:
    """Check if a file matches known problematic patterns."""
    name = filepath.name.lower()
    for pattern in PROBLEMATIC_FILE_PATTERNS:
        if name.endswith(pattern.lower()):
            return True
    return False


def _move_problematic_files_to_temp(folder: Path) -> list[str]:
    """Move known problematic files to temp folder before deletion.

    This handles files like .pyd and .dll that often remain locked
    even after processes are terminated.

    Returns:
        List of status messages about moved files.
    """
    import tempfile
    import uuid

    results = []
    temp_base = Path(tempfile.gettempdir()) / "safe_delete_staging"

    try:
        for filepath in folder.rglob("*"):
            if filepath.is_file() and _is_problematic_file(filepath):
                try:
                    # Create unique temp location
                    unique_name = f"{filepath.stem}_{uuid.uuid4().hex[:8]}{filepath.suffix}"
                    temp_dest = temp_base / unique_name
                    temp_base.mkdir(parents=True, exist_ok=True)

                    # Try to move the file
                    shutil.move(str(filepath), str(temp_dest))
                    results.append(f"MOVED: {filepath.name} -> {temp_dest}")
                except PermissionError:
                    results.append(f"LOCKED (cannot move): {filepath}")
                except OSError as e:
                    results.append(f"ERROR moving {filepath.name}: {e}")
    except PermissionError:
        results.append("ERROR: Cannot scan folder (permission denied)")

    return results


# =============================================================================
# Folder Deletion
# =============================================================================


def _rmtree_remove_readonly(func: Callable[..., None], path: str, _exc: object) -> None:
    """Error handler for shutil.rmtree to handle readonly files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _delete_folder(path: Path) -> tuple[bool, str]:
    """Delete folder using shutil.rmtree with readonly handling."""
    if not path.exists():
        return True, "Already deleted"

    try:
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_rmtree_remove_readonly)
        else:
            shutil.rmtree(path, onerror=_rmtree_remove_readonly)  # pylint: disable=deprecated-argument

        if not path.exists():
            return True, "Deleted successfully"
        return False, "Folder still exists after rmtree"

    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except OSError as e:
        return False, f"OS error: {e}"


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
    parser.add_argument("--kill-lockers", "-k", action="store_true", help="Kill processes locking the folder")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()
    exit_code = 0

    for path_str in args.paths:
        path = Path(path_str).resolve()

        if not args.quiet:
            print(f"\n{'=' * 50}")
            print(f"Processing: {path}")
            print("=" * 50)

        # Diagnose
        diag = diagnose_folder(path)

        if not args.quiet:
            print_diagnostic_report(diag)

        if not args.delete:
            if diag.exists:
                print("\n[!] Use --delete to delete the folder")
            continue

        if not diag.exists:
            print("\n[OK] Already deleted")
            continue

        # Kill lockers if requested
        if args.kill_lockers and diag.locking_processes:
            print("\n[...] Killing locking processes...")
            kill_results = _kill_detected_lockers(diag.locking_processes)
            for msg in kill_results:
                print(f"  {msg}")
            if any("KILLED" in msg for msg in kill_results):
                print("  Waiting for handles to release...")
                time.sleep(2)
            # Warn if protected processes are blocking
            if any("PROTECTED" in msg for msg in kill_results):
                print("\n[!] Protected processes are blocking - deletion may fail")

        # Move problematic files to temp before deletion
        print("\n[...] Moving problematic files to temp...")
        move_results = _move_problematic_files_to_temp(path)
        if move_results:
            for msg in move_results:
                print(f"  {msg}")
        else:
            print("  No problematic files found")

        # Delete
        print(f"\n[...] Deleting {path}...")
        success, message = _delete_folder(path)

        if success:
            print(f"[OK] {message}")
        else:
            print(f"[FAIL] {message}")
            print("\nTip: Try --kill-lockers")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
