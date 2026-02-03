#!/usr/bin/env python3
"""
Safe folder deletion utility with comprehensive diagnostics.

This script attempts to delete folders safely while providing detailed
information about why deletion might fail.

Usage:
    python tools/safe_delete_folder.py <folder_path> [--force] [--diagnose-only]

Features:
    - Diagnoses why folders can't be deleted
    - Checks for open file handles (Windows)
    - Identifies locking processes
    - Provides remediation suggestions
    - Optionally forces deletion with retries

================================================================================
DEPENDENCIES & SETUP NOTES
================================================================================

Sysinternals Handle Tool (RECOMMENDED for accurate lock detection):
    - AUTO-DOWNLOADED: The script will automatically download handle64.exe if not found
    - Download location: %LOCALAPPDATA%\\Sysinternals\\ (standard Windows location)
    - Manual download: https://learn.microsoft.com/en-us/sysinternals/downloads/handle
    - First run requires accepting EULA: handle64.exe -accepteula
    - Usage: handle64.exe <path> - shows which process has handles to the path

================================================================================
LEARNINGS & KNOWN ISSUES (Updated from real-world usage)
================================================================================

CLAUDE CODE WARNING:
    If running this script from within Claude Code (claude.exe), be aware that
    Claude Code itself may hold file handles to folders it's diagnosing!
    handle64.exe output shows: claude.exe and cmd.exe holding handles.
    Solution: Run the script from a separate terminal, not from within Claude.

HANDLE64.EXE PERFORMANCE:
    handle64.exe can be VERY SLOW (2-3 minutes!) especially on first run.
    The script uses a 180-second timeout. If it still times out:
    1. Run manually once: handle64.exe -accepteula
    2. Wait for it to complete (can take several minutes)
    3. Subsequent runs should be faster

Common blocking files in Python .venv folders:
    - cryptography/hazmat/bindings/_rust.pyd  (cryptography package)
    - nacl/_sodium.pyd                         (PyNaCl package)
    - psutil/_psutil_windows.pyd              (psutil package)
    - pydantic_core/_pydantic_core.*.pyd      (pydantic v2 package)
    - pywin32_system32/pywintypes*.dll        (pywin32 package)
    - rpds/rpds.*.pyd                         (rpds-py package)
    - win32/win32api.pyd, win32job.pyd        (pywin32 package)

    These .pyd/.dll files are compiled Python extensions that Windows keeps
    locked even after the Python process exits. Common causes:
    - VS Code Python extension background processes
    - Windows SearchIndexer scanning the folder
    - Anti-virus real-time scanning
    - DLL caching by Windows kernel
    - Claude Code (claude.exe) when running diagnostics from within it

Strategies that work (in order of reliability):
    1. Run from OUTSIDE Claude Code (avoids self-locking)
    2. Kill Python processes running from the folder (--kill-python flag)
    3. Kill VS Code processes for this folder (--kill-vscode flag)
    4. Move locked .pyd/.dll files to C:\\temp, then delete (Jenkins approach)
    5. Kill specific process holding the file (use handle64.exe to identify)
    6. Restart Windows Explorer (--restart-explorer flag)
    7. Robocopy /MIR to empty folder (can delete most files, fails on locked)
    8. Move folder to temp, then delete (sometimes bypasses locks)
    9. Stop SearchIndexer service temporarily
    10. Schedule for deletion on reboot (--schedule-reboot, requires admin)
    11. Boot into Safe Mode (nuclear option)

Jenkins CI approach (from AutoRunner):
    The most reliable automated approach combines:
    1. Kill Python processes with WMI (finds processes by path in CommandLine)
    2. Move locked .pyd/.dll files to C:\\temp with unique names
    3. Then delete the now-empty directory structure
    See: https://github.com/MarcusJellinghaus/AutoRunner

Strategies that DON'T work reliably:
    - Simple shutil.rmtree (fails on any locked file)
    - PowerShell Remove-Item -Force (still respects file locks)
    - cmd rmdir /s /q (same issue)
    - Taking ownership (doesn't help with locks, only permissions)
    - Running from within Claude Code (it locks the folder during diagnosis!)

================================================================================
"""

from __future__ import annotations

import argparse
import os
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

# Windows-specific imports
if sys.platform == "win32":
    pass  # Windows-specific imports handled inline


@dataclass
class DiagnosticResult:
    """Results from folder diagnostics."""

    path: Path
    exists: bool = False
    is_directory: bool = False
    is_empty: bool = True
    contents: list[str] = field(default_factory=list)
    permissions_ok: bool = False
    owner: str = ""
    attributes: str = ""
    locking_processes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def get_folder_attributes_windows(path: Path) -> str:
    """Get Windows file attributes as a readable string."""
    if sys.platform != "win32":
        return "N/A (not Windows)"

    try:
        attrs = path.stat().st_file_attributes
        attr_names = []
        attr_map = {
            stat.FILE_ATTRIBUTE_READONLY: "READONLY",
            stat.FILE_ATTRIBUTE_HIDDEN: "HIDDEN",
            stat.FILE_ATTRIBUTE_SYSTEM: "SYSTEM",
            stat.FILE_ATTRIBUTE_DIRECTORY: "DIRECTORY",
            stat.FILE_ATTRIBUTE_ARCHIVE: "ARCHIVE",
            stat.FILE_ATTRIBUTE_TEMPORARY: "TEMPORARY",
            stat.FILE_ATTRIBUTE_REPARSE_POINT: "REPARSE_POINT",
            stat.FILE_ATTRIBUTE_COMPRESSED: "COMPRESSED",
            stat.FILE_ATTRIBUTE_ENCRYPTED: "ENCRYPTED",
        }
        for attr_val, attr_name in attr_map.items():
            if attrs & attr_val:
                attr_names.append(attr_name)
        return ", ".join(attr_names) if attr_names else "NORMAL"
    except (OSError, AttributeError) as e:
        return f"Error: {e}"


def _get_sysinternals_dir() -> Path:
    """Get the standard directory for Sysinternals tools.

    Returns:
        Path to %LOCALAPPDATA%\\Sysinternals\\ (standard Windows location for user tools).
    """
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        return Path(local_app_data) / "Sysinternals"
    # Fallback to user home
    return Path.home() / ".sysinternals"


def _download_handle_executable() -> str | None:
    """Download Sysinternals Handle tool if not present.

    Downloads from Microsoft's official Sysinternals site and extracts
    the appropriate executable (handle64.exe for 64-bit, handle.exe for 32-bit).

    The tool is saved to %LOCALAPPDATA%\\Sysinternals\\ which is the standard
    Windows location for user-installed Sysinternals tools.

    Returns:
        Path to the downloaded executable, or None if download failed.
    """
    import io
    import urllib.request
    import zipfile

    target_dir = _get_sysinternals_dir()
    url = "https://download.sysinternals.com/files/Handle.zip"
    exe_name = "handle64.exe" if sys.maxsize > 2**32 else "handle.exe"
    target_path = target_dir / exe_name

    # Don't re-download if already exists
    if target_path.exists():
        return str(target_path)

    print(f"  Downloading Sysinternals Handle tool from {url}...")

    try:
        # Download the zip file
        with urllib.request.urlopen(url, timeout=30) as response:
            zip_data = response.read()

        # Extract the executable
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # Find the executable in the zip
            for name in zf.namelist():
                if name.lower() == exe_name.lower():
                    # Extract to target directory
                    target_dir.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(target_path, "wb") as dst:
                        dst.write(src.read())
                    print(f"  Downloaded {exe_name} to {target_path}")
                    return str(target_path)

        print(f"  Warning: {exe_name} not found in downloaded zip")
        return None

    except urllib.error.URLError as e:
        print(f"  Warning: Failed to download Handle tool: {e}")
        return None
    except zipfile.BadZipFile:
        print("  Warning: Downloaded file is not a valid zip")
        return None
    except OSError as e:
        print(f"  Warning: Failed to save Handle tool: {e}")
        return None


def _ensure_handle_eula_accepted(handle_exe: str) -> bool:
    """Ensure the Sysinternals EULA has been accepted for handle64.exe.

    The first run of handle64.exe requires EULA acceptance, which can be very slow
    (2-3 minutes). This function does a quick test run to check/accept the EULA.

    Args:
        handle_exe: Path to handle64.exe

    Returns:
        True if EULA is accepted and handle64.exe is ready to use.
    """
    if not handle_exe or not Path(handle_exe).exists():
        return False

    # Quick test: run handle64.exe on a path that definitely exists
    # If EULA is already accepted, this returns quickly
    # If not, we need to wait for acceptance
    try:
        # First, try a quick run with short timeout to see if EULA is already accepted
        result = subprocess.run(
            [handle_exe, "-accepteula", "-nobanner", "C:\\"],
            capture_output=True,
            text=True,
            timeout=10,  # Short timeout for quick check
            check=False,
        )
        # If it returns quickly, EULA is accepted
        if result.returncode == 0 or "No matching handles found" in result.stdout:
            return True
    except subprocess.TimeoutExpired:
        # Timed out - EULA probably not accepted yet, need longer run
        pass

    # EULA not accepted - do a full acceptance run with progress indicator
    print("  Accepting Sysinternals EULA (this may take 2-3 minutes on first run)...")
    try:
        result = subprocess.run(
            [handle_exe, "-accepteula", "-nobanner", "C:\\"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for EULA acceptance
            check=False,
        )
        if result.returncode == 0 or "No matching handles found" in result.stdout:
            print("  EULA accepted successfully.")
            return True
        else:
            print("  Warning: handle64.exe returned unexpected output")
            return False
    except subprocess.TimeoutExpired:
        print("  Warning: handle64.exe timed out during EULA acceptance")
        return False
    except OSError as e:
        print(f"  Warning: Failed to run handle64.exe: {e}")
        return False


def _find_handle_executable(auto_download: bool = True) -> str | None:
    """Find the Sysinternals handle executable.

    Searches for handle64.exe (preferred on 64-bit) or handle.exe in:
    1. System PATH
    2. %LOCALAPPDATA%\\Sysinternals\\ (standard location)
    3. Current script directory (legacy)
    4. Common installation locations
    5. Auto-downloads to %LOCALAPPDATA%\\Sysinternals\\ if not found

    Args:
        auto_download: If True, automatically download if not found.

    Returns:
        Path to executable or None if not found.
    """
    # Prefer 64-bit on 64-bit Windows
    candidates = ["handle64.exe", "handle.exe"] if sys.maxsize > 2**32 else ["handle.exe", "handle64.exe"]

    # Check PATH first
    for exe in candidates:
        try:
            result = subprocess.run(
                ["where", exe],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Check standard Sysinternals directory first
    sysinternals_dir = _get_sysinternals_dir()
    for exe in candidates:
        exe_path = sysinternals_dir / exe
        if exe_path.exists():
            return str(exe_path)

    # Check script directory (legacy location)
    script_dir = Path(__file__).parent
    for exe in candidates:
        exe_path = script_dir / exe
        if exe_path.exists():
            return str(exe_path)

    # Check other common locations
    common_locations = [
        Path(os.environ.get("SYSTEMROOT", "C:\\Windows")) / "System32",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps",
        Path("C:\\Tools"),
        Path("C:\\Sysinternals"),
    ]
    for loc in common_locations:
        for exe in candidates:
            exe_path = loc / exe
            if exe_path.exists():
                return str(exe_path)

    # Auto-download if not found
    if auto_download:
        return _download_handle_executable()

    return None


def find_locking_processes_windows(path: Path) -> list[str]:
    """Find processes that have handles open to the given path (Windows only).

    Uses Sysinternals Handle tool if available for accurate detection,
    falls back to heuristics if not.
    """
    if sys.platform != "win32":
        return []

    locking = []

    # Try using handle.exe/handle64.exe from Sysinternals if available
    handle_exe = _find_handle_executable()
    if handle_exe:
        # Ensure EULA is accepted before running (handles first-run slowness)
        if not _ensure_handle_eula_accepted(handle_exe):
            locking.append("[INFO] handle64.exe EULA could not be accepted")
        else:
            try:
                # EULA is accepted, now run the actual query (should be fast)
                result = subprocess.run(
                    [handle_exe, "-nobanner", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute should be enough after EULA is accepted
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if line.strip() and "No matching handles found" not in line:
                            locking.append(f"[{Path(handle_exe).name}] {line.strip()}")
                # returncode 0 with no output or "No matching handles" = no locks (good!)
            except subprocess.TimeoutExpired:
                locking.append(f"[{Path(handle_exe).name}] Timed out querying handles")
    else:
        locking.append("[INFO] handle64.exe not available (download failed or offline)")

    # Try using PowerShell to find processes with files open
    # This is a heuristic - checks common processes that might lock folders
    try:
        ps_script = f"""
        $path = '{path}'
        Get-Process | Where-Object {{
            try {{
                $_.Modules | Where-Object {{ $_.FileName -like "$path*" }}
            }} catch {{ }}
        }} | Select-Object -Property Id, ProcessName -Unique | ForEach-Object {{
            "$($_.Id): $($_.ProcessName)"
        }}
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if line.strip() and ":" in line:
                    locking.append(f"[PowerShell] {line.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Note: We used to check for common processes (explorer, SearchIndexer, etc.)
    # but this was misleading - it only showed they were RUNNING, not that they
    # were actually locking THIS folder. Removed to avoid confusion.
    # The handle64.exe output above is the only reliable way to identify lockers.

    return locking


def diagnose_folder(path: Path, quick: bool = False) -> DiagnosticResult:
    """Run comprehensive diagnostics on a folder."""
    result = DiagnosticResult(path=path)

    # Check existence
    result.exists = path.exists()
    if not result.exists:
        result.errors.append("Folder does not exist")
        return result

    # Check if it's a directory
    result.is_directory = path.is_dir()
    if not result.is_directory:
        result.errors.append("Path exists but is not a directory")
        return result

    # Get contents
    try:
        result.contents = [item.name for item in path.iterdir()]
        result.is_empty = len(result.contents) == 0
    except PermissionError as e:
        result.errors.append(f"Cannot list contents: {e}")
        result.permissions_ok = False

    # Check permissions
    try:
        # Try to check write access
        result.permissions_ok = os.access(path, os.W_OK)
        if not result.permissions_ok:
            result.errors.append("No write permission on folder")
            result.suggestions.append("Run as administrator or change permissions")
    except OSError as e:
        result.errors.append(f"Permission check failed: {e}")

    # Get owner (Windows)
    if sys.platform == "win32":
        try:
            ps_cmd = f"(Get-Acl '{path}').Owner"
            proc = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0:
                result.owner = proc.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            result.owner = "Unknown"

    # Get attributes
    result.attributes = get_folder_attributes_windows(path)
    if "READONLY" in result.attributes:
        result.errors.append("Folder has READONLY attribute")
        result.suggestions.append("Remove readonly attribute with: attrib -r <folder>")
    if "REPARSE_POINT" in result.attributes:
        result.errors.append("Folder is a reparse point (junction/symlink)")
        result.suggestions.append("Use 'rmdir' instead of recursive delete")

    # Find locking processes (skip in quick mode - can be slow)
    if not quick:
        result.locking_processes = find_locking_processes_windows(path)
    # No generic suggestions - only actual diagnostic results matter
    # Suggestions are only added for specific diagnosed issues (permissions, readonly, etc.)

    return result


def print_diagnostic_report(diag: DiagnosticResult) -> None:
    """Print a formatted diagnostic report."""
    print("\n" + "=" * 60)
    print("FOLDER DIAGNOSTIC REPORT")
    print("=" * 60)
    print(f"\nPath: {diag.path}")
    print(f"Exists: {diag.exists}")

    if not diag.exists:
        print("\n[!] Folder does not exist - nothing to delete")
        return

    print(f"Is Directory: {diag.is_directory}")
    print(f"Is Empty: {diag.is_empty}")
    print(f"Permissions OK: {diag.permissions_ok}")
    print(f"Owner: {diag.owner}")
    print(f"Attributes: {diag.attributes}")

    if diag.contents:
        print(f"\nContents ({len(diag.contents)} items):")
        for item in diag.contents[:10]:
            print(f"  - {item}")
        if len(diag.contents) > 10:
            print(f"  ... and {len(diag.contents) - 10} more items")

    if diag.errors:
        print("\n[ERRORS]")
        for error in diag.errors:
            print(f"  [X] {error}")

    if diag.locking_processes:
        print("\n[HANDLE DETECTION]")
        for proc in diag.locking_processes:
            # Distinguish between actual locks found and info/warning messages
            if proc.startswith("[INFO]"):
                print(f"  {proc}")
            elif "Timed out" in proc or "EULA" in proc:
                print(f"  [WARN] {proc}")
            else:
                # Actual lock found - this is the important diagnostic info
                print(f"  [LOCKED BY] {proc}")

    # Only show suggestions if there are specific actionable ones (not generic advice)
    if diag.suggestions:
        print("\n[ACTIONABLE ISSUES]")
        for suggestion in diag.suggestions:
            print(f"  - {suggestion}")

    print("\n" + "=" * 60)


def remove_readonly_onerror(func: Callable[..., None], path: str, _excinfo: object) -> None:
    """Error handler for shutil.rmtree to handle readonly files (legacy)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_readonly_onexc(func: Callable[..., None], path: str, _exc: BaseException) -> None:
    """Exception handler for shutil.rmtree to handle readonly files (Python 3.12+)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _rmtree_with_handler(path: Path) -> None:
    """Remove directory tree with appropriate error/exception handler."""
    # Python 3.12+ uses onexc, earlier versions use onerror
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=remove_readonly_onexc)
    else:
        shutil.rmtree(path, onerror=remove_readonly_onerror)  # pylint: disable=deprecated-argument


def _run_cmd_rmdir(path: Path) -> None:
    """Run cmd rmdir command."""
    subprocess.run(
        ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
        check=True,
        capture_output=True,
        timeout=10,
    )


def _run_powershell_remove(path: Path) -> None:
    """Run PowerShell Remove-Item command."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Remove-Item -Path '{path}' -Recurse -Force -ErrorAction Stop"],
        capture_output=True,
        timeout=60,  # Increased timeout for large folders
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        raise OSError(f"PowerShell error: {error_msg}")


def _kill_workspace_python_processes(path: Path) -> list[str]:
    """Kill Python processes that are running from the given path (Windows only).

    Uses WMI to find Python processes whose executable or command line
    references the target path, then terminates them.

    This is based on the Jenkins cleanup approach from:
    https://github.com/MarcusJellinghaus/AutoRunner/blob/main/jenkins-jobs/vars/mcpCoderExecutorWindows.groovy

    Returns:
        List of killed process descriptions.
    """
    if sys.platform != "win32":
        return []

    killed = []
    path_str = str(path).replace("\\", "\\\\")

    ps_script = f'''
    $killed = @()
    Get-WmiObject Win32_Process | Where-Object {{
        ($_.Name -match "python") -and
        (($_.CommandLine -like "*{path_str}*") -or ($_.ExecutablePath -like "*{path_str}*"))
    }} | ForEach-Object {{
        $info = "PID $($_.ProcessId): $($_.Name)"
        try {{
            Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
            $killed += $info
        }} catch {{
            # Process may have already exited
        }}
    }}
    $killed -join "`n"
    '''

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    killed.append(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return killed


def _kill_vscode_processes(path: Path) -> list[str]:
    """Kill VS Code processes that have the given path open (Windows only).

    VS Code (Code.exe) often keeps file handles open to folders in the workspace,
    which can prevent deletion. This function ONLY kills VS Code processes that
    have the target path in their command line arguments or window title.

    It will NOT kill unrelated VS Code windows.

    WARNING: This will close VS Code windows for this folder! Use with caution.

    Returns:
        List of killed process descriptions.
    """
    if sys.platform != "win32":
        return []

    killed = []
    path_str = str(path).replace("\\", "\\\\")
    folder_name = path.name  # Just the folder name for window title matching

    # Kill Code.exe processes that have this path in their command line
    # This is very specific - only kills VS Code instances working on this folder
    ps_script = f'''
    $killed = @()
    $pathToCheck = "{path_str}"
    $folderName = "{folder_name}"

    # Method 1: Check command line for the exact path
    # This catches VS Code instances that were opened with this folder
    Get-WmiObject Win32_Process | Where-Object {{
        ($_.Name -match "^Code") -and
        ($_.CommandLine -like "*$pathToCheck*")
    }} | ForEach-Object {{
        $info = "PID $($_.ProcessId): $($_.Name) (path in cmdline)"
        try {{
            Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
            $killed += $info
        }} catch {{
            # Process may have already exited
        }}
    }}

    # Method 2: Check window titles for the folder name
    # Only if Method 1 didn't find anything
    if ($killed.Count -eq 0) {{
        Get-Process -Name "Code" -ErrorAction SilentlyContinue | Where-Object {{
            $_.MainWindowTitle -like "*$folderName*"
        }} | ForEach-Object {{
            $info = "PID $($_.Id): $($_.Name) - $($_.MainWindowTitle)"
            try {{
                Stop-Process -Id $_.Id -Force -ErrorAction Stop
                $killed += $info
            }} catch {{
                # Process may have already exited
            }}
        }}
    }}

    $killed -join "`n"
    '''

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    killed.append(line.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return killed


def _move_locked_pyd_files_then_delete(path: Path) -> None:
    """Move locked .pyd/.dll files to temp, then delete the directory.

    This is a clever trick from Jenkins CI pipelines: Windows often allows
    MOVING files that are locked, even when it won't allow DELETING them.
    By moving the locked files elsewhere, the original directory becomes
    deletable.

    Based on the approach from:
    https://github.com/MarcusJellinghaus/AutoRunner/blob/main/jenkins-jobs/vars/mcpCoderExecutorWindows.groovy

    The moved files accumulate in C:\\temp but can be cleaned up later or on reboot.
    """
    import uuid

    if sys.platform != "win32":
        raise OSError("This strategy is Windows-only")

    # Use C:\temp as destination (create if needed)
    temp_dir = Path("C:/temp")
    temp_dir.mkdir(exist_ok=True)

    moved_files = []

    # Find and move all .pyd and .dll files (common lock culprits)
    for pattern in ["*.pyd", "*.dll"]:
        try:
            for pyd_file in path.rglob(pattern):
                try:
                    # Generate unique destination name
                    dest_name = f"{pyd_file.name}.{uuid.uuid4().hex[:8]}.old"
                    dest_path = temp_dir / dest_name

                    # Try to move the file
                    shutil.move(str(pyd_file), str(dest_path))
                    moved_files.append(pyd_file.name)
                except (PermissionError, OSError):
                    pass  # File might not be movable either
        except (PermissionError, OSError):
            pass  # Can't enumerate, skip this pattern

    # Now try to delete the directory
    if moved_files:
        # Give Windows a moment to release handles
        time.sleep(1)

    # Try cmd rmdir first (often works after moving locked files)
    try:
        subprocess.run(
            ["cmd", "/c", "rd", "/s", "/q", str(path)],
            check=True,
            capture_output=True,
            timeout=30,
        )
        if not path.exists():
            return  # Success!
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    # Fallback to shutil
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)

    if path.exists():
        raise OSError(f"Moved {len(moved_files)} .pyd/.dll files but directory still exists")


def _delete_empty_folder_aggressive(path: Path) -> None:
    """Aggressively try to delete an empty folder using multiple methods.

    This handles the case where folder contents are deleted but the
    empty folder itself is still locked (common Windows issue).
    """
    if not path.exists():
        return

    # Check if folder is actually empty
    try:
        contents = list(path.iterdir())
        if contents:
            raise OSError(f"Folder not empty: {len(contents)} items remain")
    except PermissionError:
        pass  # Can't check, try anyway

    # Method 1: Simple rmdir
    try:
        os.rmdir(path)
        if not path.exists():
            return
    except OSError:
        pass

    # Method 2: cmd rmdir
    try:
        subprocess.run(
            ["cmd", "/c", "rmdir", str(path)],
            check=True,
            capture_output=True,
            timeout=10,
        )
        if not path.exists():
            return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass

    # Method 3: PowerShell with retries
    ps_script = f'''
    $path = '{path}'
    $maxRetries = 5
    for ($i = 0; $i -lt $maxRetries; $i++) {{
        try {{
            Remove-Item -Path $path -Force -ErrorAction Stop
            exit 0
        }} catch {{
            Start-Sleep -Milliseconds 500
        }}
    }}
    exit 1
    '''
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if not path.exists():
            return
    except subprocess.TimeoutExpired:
        pass

    # Method 4: Rename then delete (sometimes works on locked empty folders)
    import uuid
    temp_name = path.parent / f"_del_{uuid.uuid4().hex[:8]}"
    try:
        path.rename(temp_name)
        os.rmdir(temp_name)
        if not path.exists() and not temp_name.exists():
            return
    except OSError:
        # Try to clean up the renamed folder if it exists
        if temp_name.exists() and not path.exists():
            try:
                os.rmdir(temp_name)
            except OSError:
                pass
            if not temp_name.exists():
                return  # Original is gone, renamed was deleted

    if path.exists():
        raise OSError("Empty folder still locked after all deletion attempts")


def _run_robocopy_mirror_delete(path: Path) -> None:
    """Use robocopy /MIR to delete folder contents by mirroring an empty folder.

    This is a clever trick: robocopy /MIR (mirror) will delete files in the
    destination that don't exist in the source. By pointing it at an empty
    source folder, it effectively deletes all contents.

    This sometimes succeeds where other methods fail because robocopy uses
    different Windows APIs and has better retry logic built in.
    """
    import tempfile
    import uuid

    # Create temporary empty folder
    temp_dir = Path(tempfile.gettempdir())
    empty_folder = temp_dir / f"_empty_for_robocopy_{uuid.uuid4().hex[:8]}"

    try:
        empty_folder.mkdir(exist_ok=True)

        # Run robocopy to mirror empty folder to target (deletes all contents)
        result = subprocess.run(
            [
                "robocopy",
                str(empty_folder),
                str(path),
                "/MIR",  # Mirror - delete dest files not in source
                "/R:2",  # 2 retries
                "/W:1",  # 1 second wait between retries
                "/NFL",  # No file list
                "/NDL",  # No directory list
                "/NJH",  # No job header
                "/NJS",  # No job summary
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for large folders
            check=False,
        )

        # Robocopy exit codes: 0-7 are success, 8+ are errors
        # But even with errors, it may have deleted most files
        if result.returncode >= 8:
            # Check if any "Access is denied" errors
            if "ERROR 5" in result.stdout or "Access is denied" in result.stdout:
                raise OSError("Robocopy access denied - some files locked")
            raise OSError(f"Robocopy failed with code {result.returncode}")

        # After robocopy, the folder should be empty - try to remove it
        if path.exists():
            os.rmdir(path)

    finally:
        # Clean up our temp empty folder
        if empty_folder.exists():
            try:
                empty_folder.rmdir()
            except OSError:
                pass  # Best effort cleanup


def _move_to_temp_then_delete(path: Path) -> None:
    """Move folder to temp directory, then delete from there."""
    import tempfile
    import uuid

    # Create a unique name in temp
    temp_dir = Path(tempfile.gettempdir())
    temp_name = f"_delete_me_{uuid.uuid4().hex[:8]}_{path.name}"
    temp_path = temp_dir / temp_name

    # Try to move
    shutil.move(str(path), str(temp_path))

    # If move succeeded, try to delete from temp
    if temp_path.exists() and not path.exists():
        try:
            shutil.rmtree(temp_path, ignore_errors=True)
        except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            # Schedule for deletion on reboot (Windows)
            if sys.platform == "win32":
                _schedule_delete_on_reboot(temp_path)


def _rename_with_delete_prefix(path: Path) -> None:
    """Rename folder with a delete prefix (sometimes works when delete doesn't)."""
    import uuid

    new_name = f"_TO_DELETE_{uuid.uuid4().hex[:8]}_{path.name}"
    new_path = path.parent / new_name

    # Rename
    path.rename(new_path)

    # Try to delete the renamed folder
    if new_path.exists():
        shutil.rmtree(new_path, ignore_errors=True)

    # If original path is gone, we succeeded
    if not path.exists() and not new_path.exists():
        return
    if not path.exists():
        # Renamed but couldn't delete - that's still progress
        raise OSError(f"Renamed to {new_path} but couldn't delete. You can delete it manually or after reboot.")
    raise OSError("Rename failed")


def _schedule_delete_on_reboot(path: Path) -> None:
    """Schedule a file/folder for deletion on next Windows reboot."""
    if sys.platform != "win32":
        return

    import ctypes
    from ctypes import wintypes

    MOVEFILE_DELAY_UNTIL_REBOOT = 0x4

    # Properly declare the function with error handling
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    MoveFileExW = kernel32.MoveFileExW
    MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
    MoveFileExW.restype = wintypes.BOOL

    # For directories, we need to use a different approach via registry
    # MoveFileEx with DELAY_UNTIL_REBOOT doesn't work well on directories
    # Use PendingFileRenameOperations registry key instead
    if path.is_dir():
        _schedule_dir_delete_via_registry(path)
        return

    result = MoveFileExW(str(path), None, MOVEFILE_DELAY_UNTIL_REBOOT)
    if not result:
        error_code = ctypes.get_last_error()
        raise OSError(f"MoveFileExW failed with error code {error_code}")


def _schedule_dir_delete_via_registry(path: Path) -> None:
    """Schedule directory deletion via PendingFileRenameOperations registry key."""
    import winreg

    key_path = r"SYSTEM\CurrentControlSet\Control\Session Manager"
    value_name = "PendingFileRenameOperations"

    # Format: \??\C:\path\to\delete\0\0 (null-terminated pairs, second is empty for delete)
    # The path must be in NT format
    nt_path = f"\\??\\{path}"
    entry = f"{nt_path}\0\0"  # Source path, empty destination (delete)

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE
        ) as key:
            try:
                existing, _ = winreg.QueryValueEx(key, value_name)
                if isinstance(existing, str):
                    # Append to existing entries
                    new_value = existing.rstrip("\0") + "\0" + entry
                else:
                    new_value = entry
            except FileNotFoundError:
                new_value = entry

            winreg.SetValueEx(key, value_name, 0, winreg.REG_MULTI_SZ, new_value.split("\0"))
    except PermissionError:
        raise OSError("Need Administrator privileges to schedule reboot deletion") from None
    except OSError as e:
        raise OSError(f"Registry operation failed: {e}") from None


def try_delete_folder(
    path: Path,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    kill_python: bool = False,
    kill_vscode: bool = False,
) -> tuple[bool, str]:
    """
    Attempt to delete a folder with multiple strategies.

    Args:
        path: The folder path to delete.
        max_retries: Number of retry attempts.
        retry_delay: Seconds to wait between retries.
        kill_python: If True, kill Python processes running from this path first.
        kill_vscode: If True, kill VS Code processes that have this folder open.

    Returns:
        Tuple of (success, message)
    """
    if not path.exists():
        return True, "Folder does not exist (already deleted)"

    # Optionally kill VS Code processes first (only those with this folder open)
    if kill_vscode and sys.platform == "win32":
        killed = _kill_vscode_processes(path)
        if killed:
            print(f"  Killed {len(killed)} VS Code process(es): {', '.join(killed)}")
            time.sleep(2)  # Give Windows time to release handles

    # Optionally kill Python processes (Jenkins approach)
    if kill_python and sys.platform == "win32":
        killed = _kill_workspace_python_processes(path)
        if killed:
            print(f"  Killed {len(killed)} Python process(es): {', '.join(killed)}")
            time.sleep(2)  # Give Windows time to release handles

    last_error = "No deletion strategies available"
    strategies: list[tuple[str, Callable[[], None]]] = [
        ("shutil.rmtree with readonly handler", lambda: _rmtree_with_handler(path)),
        ("os.rmdir (for empty folders)", lambda: os.rmdir(path)),
        ("Aggressive empty folder delete", lambda: _delete_empty_folder_aggressive(path)),
    ]

    # Add move/rename strategies (often work when delete doesn't)
    strategies.extend([
        ("Move to temp then delete", lambda: _move_to_temp_then_delete(path)),
        ("Rename then delete", lambda: _rename_with_delete_prefix(path)),
    ])

    # Add Windows-specific strategies
    if sys.platform == "win32":
        strategies.extend([
            ("cmd /c rmdir /s /q", lambda: _run_cmd_rmdir(path)),
            ("PowerShell Remove-Item -Force", lambda: _run_powershell_remove(path)),
            # Jenkins approach: move locked .pyd/.dll files to temp, then delete
            ("Move .pyd/.dll to temp then delete (Jenkins approach)", lambda: _move_locked_pyd_files_then_delete(path)),
            ("Robocopy /MIR empty folder", lambda: _run_robocopy_mirror_delete(path)),
            # Last resort: stop SearchIndexer service (may require admin)
            ("Stop SearchIndexer and delete", lambda: _stop_searchindexer_and_delete(path)),
        ])

    for attempt in range(max_retries):
        for strategy_name, strategy_func in strategies:
            try:
                strategy_func()
                if not path.exists():
                    return True, f"Successfully deleted using: {strategy_name}"
            except Exception as e:  # noqa: BLE001  # pylint: disable=broad-exception-caught
                last_error = f"{strategy_name}: {e}"
                continue

        # If folder still exists, wait before retry
        if path.exists() and attempt < max_retries - 1:
            print(f"  Retry {attempt + 1}/{max_retries} in {retry_delay}s...")
            time.sleep(retry_delay)

    return False, f"All deletion strategies failed. Last error: {last_error}"


def restart_explorer() -> bool:
    """Restart Windows Explorer (may help release folder locks)."""
    if sys.platform != "win32":
        return False

    try:
        # Kill explorer
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], check=True, capture_output=True)
        time.sleep(1)
        # Start explorer
        subprocess.Popen(["explorer.exe"])  # noqa: S603
        time.sleep(2)
        return True
    except subprocess.CalledProcessError:
        return False


def _is_running_in_claude_code() -> bool:
    """Detect if we're running inside Claude Code.

    Claude Code (claude.exe) holds file handles to folders it's working with,
    which can prevent deletion. This function detects if Claude Code is running.

    Returns:
        True if Claude Code is running (may be holding handles), False otherwise.
    """
    if sys.platform != "win32":
        return False

    try:
        # Simple check: is claude.exe running?
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq claude.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=True,  # Needed for tasklist on some systems
        )
        return "claude.exe" in result.stdout.lower()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _stop_searchindexer_and_delete(path: Path) -> None:
    """Stop Windows Search Indexer, delete folder, then restart indexer.

    SearchIndexer often holds locks on folders it's indexing.
    Temporarily stopping it can allow deletion.

    Note: Requires admin privileges to stop/start services.
    """
    if sys.platform != "win32":
        raise OSError("Windows only")

    indexer_was_running = False

    # Check if SearchIndexer is running and stop it
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Service WSearch -ErrorAction SilentlyContinue).Status"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if "Running" in result.stdout:
            indexer_was_running = True
            print("  Stopping Windows Search Indexer...")
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Stop-Service WSearch -Force -ErrorAction SilentlyContinue"],
                capture_output=True,
                timeout=30,
                check=False,
            )
            time.sleep(2)  # Give it time to release handles
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        # Try to delete
        if path.exists():
            if not any(path.iterdir()):  # Empty folder
                os.rmdir(path)
            else:
                shutil.rmtree(path, ignore_errors=False)

        if not path.exists():
            return  # Success!
        raise OSError("Folder still exists after stopping SearchIndexer")

    finally:
        # Restart SearchIndexer if it was running
        if indexer_was_running:
            print("  Restarting Windows Search Indexer...")
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Start-Service WSearch -ErrorAction SilentlyContinue"],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Safely delete folders with comprehensive diagnostics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Diagnose why a folder can't be deleted
    python tools/safe_delete_folder.py "C:\\path\\to\\folder" --diagnose-only

    # Try to delete with force
    python tools/safe_delete_folder.py "C:\\path\\to\\folder" --force

    # Delete multiple folders
    python tools/safe_delete_folder.py folder1 folder2 folder3 --force

    # Restart Explorer before deletion (helps with locks)
    python tools/safe_delete_folder.py "C:\\path\\to\\folder" --force --restart-explorer
        """,
    )
    parser.add_argument("paths", nargs="+", help="Folder path(s) to diagnose/delete")
    parser.add_argument("--diagnose-only", "-d", action="store_true", help="Only run diagnostics, don't delete")
    parser.add_argument("--force", "-f", action="store_true", help="Attempt to force delete")
    parser.add_argument("--restart-explorer", "-r", action="store_true", help="Restart Windows Explorer before deletion")
    parser.add_argument("--retries", type=int, default=3, help="Number of retry attempts (default: 3)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--quick", action="store_true", help="Skip slow diagnostics (process detection)")
    parser.add_argument("--schedule-reboot", action="store_true", help="Schedule deletion on next reboot (Windows only)")
    parser.add_argument(
        "--kill-python", "-k",
        action="store_true",
        help="Kill Python processes running from this folder before deletion (Windows only)"
    )
    parser.add_argument(
        "--kill-vscode",
        action="store_true",
        help="Kill VS Code processes that have this folder open (Windows only). Only kills VS Code windows for this specific folder."
    )

    args = parser.parse_args()

    # Warn if running inside Claude Code
    if sys.platform == "win32" and _is_running_in_claude_code():
        print("\n" + "!" * 60)
        print("WARNING: Running inside Claude Code!")
        print("Claude Code holds file handles to folders it's working with.")
        print("This may prevent deletion. For best results, run this script")
        print("from a separate terminal (cmd.exe, PowerShell, or Git Bash).")
        print("!" * 60 + "\n")

    if args.restart_explorer and sys.platform == "win32":
        print("Restarting Windows Explorer...")
        if restart_explorer():
            print("Explorer restarted successfully")
        else:
            print("Failed to restart Explorer")

    exit_code = 0

    for path_str in args.paths:
        path = Path(path_str).resolve()

        if not args.quiet:
            print(f"\n{'=' * 60}")
            print(f"Processing: {path}")
            print("=" * 60)

        # Run diagnostics
        diag = diagnose_folder(path, quick=args.quick)

        if not args.quiet:
            print_diagnostic_report(diag)

        # Attempt deletion if requested
        if args.force and not args.diagnose_only:
            if not diag.exists:
                print(f"\n[OK] {path} - Already deleted or doesn't exist")
                continue

            print(f"\n[...] Attempting to delete {path}...")
            success, message = try_delete_folder(
                path,
                max_retries=args.retries,
                kill_python=args.kill_python,
                kill_vscode=args.kill_vscode,
            )

            if success:
                print(f"[OK] {message}")
            else:
                print(f"[FAIL] {message}")
                exit_code = 1

                # Provide additional help
                # Try scheduling for reboot if requested
                if args.schedule_reboot and sys.platform == "win32":
                    print("\n[...] Scheduling for deletion on reboot...")
                    try:
                        _schedule_delete_on_reboot(path)
                        print(f"[OK] Scheduled {path} for deletion on next reboot")
                        exit_code = 0  # Consider this a success
                    except OSError as e:
                        print(f"[FAIL] Could not schedule for reboot: {e}")
                else:
                    # Only show actionable next steps, not generic advice
                    print("\nNext steps: Run with --schedule-reboot or from outside Claude Code")

        elif args.diagnose_only:
            if diag.errors or diag.locking_processes:
                exit_code = 1
        elif not args.force and diag.exists:
            print("\n[!] Use --force to attempt deletion")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
