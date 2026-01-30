#!/usr/bin/env python
"""Debug script to diagnose VSCode session detection."""

import json
import sys
from pathlib import Path

try:
    import win32gui
    import win32process
except ImportError:
    print("ERROR: pywin32 not installed. Run: pip install pywin32")
    sys.exit(1)

import psutil


def get_vscode_pids() -> set[int]:
    """Get PIDs of all Code.exe processes."""
    pids = set()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info.get("name", "").lower() == "code.exe":
                pids.add(proc.info.get("pid"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


def get_vscode_windows() -> list[dict]:
    """Get all windows owned by VSCode."""
    vscode_pids = get_vscode_pids()
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid in vscode_pids:
                    windows.append({"hwnd": hwnd, "title": title, "pid": pid})
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def load_sessions() -> list[dict]:
    """Load sessions from the session store."""
    sessions_file = Path.home() / ".mcp_coder" / "coordinator_cache" / "vscodeclaude_sessions.json"
    if not sessions_file.exists():
        return []
    try:
        data = json.loads(sessions_file.read_text(encoding="utf-8"))
        return data.get("sessions", [])
    except (json.JSONDecodeError, OSError):
        return []


def match_session_to_window_OLD(session: dict, windows: list[dict]) -> dict | None:
    """OLD: Match by folder name in window title (doesn't work)."""
    folder_name = Path(session.get("folder", "")).name.lower()
    
    for window in windows:
        title_lower = window["title"].lower()
        if folder_name in title_lower:
            return window
    return None


def match_session_to_window(session: dict, windows: list[dict]) -> dict | None:
    """NEW: Match by issue number (#N) AND repo name in window title.
    
    VSCode window titles look like:
    - '[#323 review] Add coordinator... - mcp_coder'
    - '[#42 new] pytest - adjust... - mcp-code-checker'
    
    We match on:
    1. Issue number pattern '#N' must be in title
    2. Repo name (last part of 'owner/repo') must be in title
    """
    issue_number = session.get("issue_number")
    repo_full = session.get("repo", "")  # e.g., 'MarcusJellinghaus/mcp_coder'
    repo_name = repo_full.split("/")[-1].lower() if "/" in repo_full else repo_full.lower()
    
    issue_pattern = f"#{issue_number}"
    
    for window in windows:
        title_lower = window["title"].lower()
        # Both issue number AND repo name must be present
        if issue_pattern in window["title"] and repo_name in title_lower:
            return window
    return None


def main():
    print("=" * 80)
    print("VSCode Session Detection Diagnostic")
    print("=" * 80)
    
    # 1. What windows can we find?
    print("\n[1] VSCode Windows Found:")
    print("-" * 80)
    windows = get_vscode_windows()
    if not windows:
        print("  (none)")
    for w in windows:
        print(f"  PID: {w['pid']:>8}  Title: {w['title']}")
    
    # 2. What are we looking for?
    print("\n[2] Sessions (what we're looking for):")
    print("-" * 80)
    sessions = load_sessions()
    if not sessions:
        print("  (no sessions in store)")
    for s in sessions:
        folder = s.get("folder", "")
        folder_name = Path(folder).name
        issue = s.get("issue_number", "?")
        repo = s.get("repo", "?")
        print(f"  Issue #{issue} ({repo})")
        print(f"    Folder: {folder}")
        print(f"    Looking for: '{folder_name}' in window title")
    
    # 3. Matching results
    print("\n[3] Matching Results:")
    print("-" * 80)
    matched = []
    unmatched = []
    
    for s in sessions:
        folder_name = Path(s.get("folder", "")).name
        issue = s.get("issue_number", "?")
        match = match_session_to_window(s, windows)
        
        if match:
            matched.append((s, match))
            print(f"  [MATCH] Issue #{issue}: '{folder_name}' -> '{match['title']}'")
        else:
            unmatched.append(s)
            print(f"  [NO MATCH] Issue #{issue}: '{folder_name}' not found in any window")
    
    # 4. What do we need to start?
    print("\n[4] Sessions that would be restarted:")
    print("-" * 80)
    if not unmatched:
        print("  (none - all sessions matched)")
    for s in unmatched:
        issue = s.get("issue_number", "?")
        repo = s.get("repo", "?")
        folder_name = Path(s.get("folder", "")).name
        print(f"  Issue #{issue} ({repo}) - folder '{folder_name}'")
    
    # 5. Analysis
    print("\n[5] Analysis:")
    print("-" * 80)
    
    # Check if issue numbers appear in window titles
    for s in unmatched:
        issue = s.get("issue_number", "?")
        folder_name = Path(s.get("folder", "")).name
        
        # Check what's in the window titles
        for w in windows:
            title = w["title"]
            # Does the issue number appear?
            if f"#{issue}" in title:
                print(f"  Issue #{issue}: Found '#{issue}' in window '{title}'")
                print(f"    BUT folder '{folder_name}' doesn't match")
                
                # What DOES match from the folder?
                parts = folder_name.split("_")
                for part in parts:
                    if part.lower() in title.lower():
                        print(f"    Part '{part}' IS in the title")
                    else:
                        print(f"    Part '{part}' is NOT in the title")


if __name__ == "__main__":
    main()
