#!/usr/bin/env python3
"""
Safe folder deletion utility for Windows.

Detects processes locking a folder using Sysinternals handle64.exe,
kills them, then deletes the folder.

Usage:
    python tools/safe_delete_folder.py <folder_path> --force --kill-lockers

Features:
    - Auto-downloads handle64.exe from Microsoft
    - Detects which processes are locking the folder
    - Kills locking processes (--kill-lockers)
    - Falls back to schedule-on-reboot if needed
"""

from __future__ import annotations

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
    """Kill all processes detected by handle64.exe."""
    if sys.platform != "win32":
        return []

    killed = []

    for proc_info in locking_processes:
        if proc_info.startswith("[ERROR]") or proc_info.startswith("[INFO]"):
            continue

        # Parse: "cmd.exe  pid: 35140  type: File  ..."
        match = re.search(r"^(\S+)\s+pid:\s*(\d+)", proc_info)
        if not match:
            continue

        proc_name = match.group(1)
        pid = int(match.group(2))

        try:
            result = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                killed.append(f"KILLED: {proc_name} (PID {pid})")
            elif "not found" in result.stderr.lower():
                killed.append(f"ALREADY GONE: {proc_name} (PID {pid})")
            else:
                killed.append(f"FAILED: {proc_name} (PID {pid})")
        except Exception as e:  # noqa: BLE001
            killed.append(f"ERROR: {proc_name} (PID {pid}): {e}")

    return killed


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


def _schedule_delete_on_reboot(path: Path) -> None:
    """Schedule folder for deletion on next Windows reboot via registry."""
    if sys.platform != "win32":
        raise OSError("Windows only")

    import winreg

    key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager"
    value_name = "PendingFileRenameOperations"
    nt_path = f"\\??\\{path}"
    entry = f"{nt_path}\0\0"

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE
        ) as key:
            try:
                existing, _ = winreg.QueryValueEx(key, value_name)
                if isinstance(existing, str):
                    new_value = existing.rstrip("\0") + "\0" + entry
                else:
                    new_value = entry
            except FileNotFoundError:
                new_value = entry

            winreg.SetValueEx(key, value_name, 0, winreg.REG_MULTI_SZ, new_value.split("\0"))
    except PermissionError:
        raise OSError("Need Administrator privileges") from None


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
    # Diagnose locks
    python tools/safe_delete_folder.py "C:\\path\\folder" --diagnose-only

    # Delete (kill lockers first)
    python tools/safe_delete_folder.py "C:\\path\\folder" --force --kill-lockers

    # Schedule for reboot if all else fails
    python tools/safe_delete_folder.py "C:\\path\\folder" --force --kill-lockers --schedule-reboot
        """,
    )
    parser.add_argument("paths", nargs="+", help="Folder path(s) to delete")
    parser.add_argument("--diagnose-only", "-d", action="store_true", help="Only diagnose, don't delete")
    parser.add_argument("--force", "-f", action="store_true", help="Attempt deletion")
    parser.add_argument("--kill-lockers", "-k", action="store_true", help="Kill processes locking the folder")
    parser.add_argument("--schedule-reboot", action="store_true", help="Schedule deletion on reboot if deletion fails")
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

        if args.diagnose_only:
            continue

        if not args.force:
            print("\n[!] Use --force to attempt deletion")
            continue

        if not diag.exists:
            print("\n[OK] Already deleted")
            continue

        # Kill lockers if requested
        if args.kill_lockers and diag.locking_processes:
            print("\n[...] Killing locking processes...")
            killed = _kill_detected_lockers(diag.locking_processes)
            for k in killed:
                print(f"  {k}")
            if any("KILLED" in k for k in killed):
                print("  Waiting for handles to release...")
                time.sleep(2)

        # Delete
        print(f"\n[...] Deleting {path}...")
        success, message = _delete_folder(path)

        if success:
            print(f"[OK] {message}")
        else:
            print(f"[FAIL] {message}")
            exit_code = 1

            if args.schedule_reboot and sys.platform == "win32":
                print("\n[...] Scheduling for deletion on reboot...")
                try:
                    _schedule_delete_on_reboot(path)
                    print("[OK] Scheduled for reboot")
                    exit_code = 0
                except OSError as e:
                    print(f"[FAIL] {e}")
            else:
                print("\nTip: Try --kill-lockers or --schedule-reboot")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
