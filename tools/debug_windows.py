#!/usr/bin/env python
"""Debug script to enumerate all visible windows on Windows."""
import psutil

try:
    import win32gui
    import win32process
except ImportError:
    print("ERROR: pywin32 not installed. Run: pip install pywin32")
    exit(1)



def get_process_info(hwnd):
    """Get process name and executable for a window handle."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid:
            proc = psutil.Process(pid)
            return pid, proc.name(), proc.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        pass
    return None, "Unknown", "Unknown"


def enum_windows():
    """Enumerate all visible windows and print their titles."""
    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only windows with titles
                pid, proc_name, exe_path = get_process_info(hwnd)
                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "pid": pid,
                    "process": proc_name,
                    "exe": exe_path,
                })
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def main():
    print("Enumerating all visible windows with titles...\n")
    windows = enum_windows()

    # Sort by process name then title
    windows.sort(key=lambda x: (x["process"].lower(), x["title"].lower()))

    print(f"Found {len(windows)} windows:\n")
    print("=" * 120)
    
    current_process = None
    vscode_windows = []
    
    for w in windows:
        # Group by process
        if w["process"] != current_process:
            current_process = w["process"]
            print(f"\n[{w['process']}] - {w['exe']}")
            print("-" * 120)
        
        print(f"  PID: {w['pid'] or 'N/A':>8}  HWND: {w['hwnd']:>10}  Title: {w['title'][:80]}")
        
        if "Visual Studio Code" in w["title"] or w["process"].lower() == "code.exe":
            vscode_windows.append(w)

    print("\n" + "=" * 120)
    print(f"\nVSCode-related windows ({len(vscode_windows)}):")
    print("-" * 120)
    for w in vscode_windows:
        print(f"  Process: {w['process']:<15} PID: {w['pid'] or 'N/A':>8}  Title: {w['title']}")


if __name__ == "__main__":
    main()
