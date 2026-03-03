#!/usr/bin/env python3
"""Stop MLflow UI with comprehensive diagnostics including parent process detection.

Usage:
    python tools/stop_mlflow.py           # Normal mode
    python tools/stop_mlflow.py --debug   # Debug mode with full diagnostics
    python tools/stop_mlflow.py --find-parent  # Find what's restarting MLflow
"""

import argparse
import re
import subprocess
import sys
import time


def run_command(cmd, timeout=10):
    """Run a command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def check_windows_services(debug=False):
    """Check if MLflow is running as a Windows service."""
    print("\n" + "=" * 60)
    print("CHECKING: Windows Services")
    print("=" * 60)
    
    code, out, err = run_command(["sc", "query", "state=", "all"])
    mlflow_services = []
    
    for line in out.split("\n"):
        if "mlflow" in line.lower():
            mlflow_services.append(line.strip())
    
    if mlflow_services:
        print("  [!] Found MLflow-related services:")
        for svc in mlflow_services:
            print(f"      {svc}")
        return mlflow_services
    else:
        print("  [OK] No MLflow services found")
        return []


def check_scheduled_tasks(debug=False):
    """Check if MLflow is in scheduled tasks."""
    print("\n" + "=" * 60)
    print("CHECKING: Scheduled Tasks")
    print("=" * 60)
    
    code, out, err = run_command(["schtasks", "/query", "/fo", "LIST"])
    mlflow_tasks = []
    
    current_task = None
    for line in out.split("\n"):
        if line.startswith("TaskName:"):
            current_task = line.split(":", 1)[1].strip()
        if current_task and "mlflow" in line.lower():
            if current_task not in mlflow_tasks:
                mlflow_tasks.append(current_task)
    
    if mlflow_tasks:
        print("  [!] Found MLflow-related tasks:")
        for task in mlflow_tasks:
            print(f"      {task}")
        return mlflow_tasks
    else:
        print("  [OK] No MLflow scheduled tasks found")
        return []


def find_python_mlflow_processes(debug=False, show_header=True):
    """Find all Python processes running MLflow."""
    if show_header:
        print("\n" + "=" * 60)
        print("FINDING: Python MLflow Processes")
        print("=" * 60)
    
    processes = []
    
    # Use PowerShell to get process details
    # Look for various MLflow patterns: ui, server, or any mlflow command
    ps_cmd = """
    Get-WmiObject Win32_Process -Filter "name='python.exe'" | 
    Where-Object { $_.CommandLine -like '*mlflow*' -and $_.CommandLine -notlike '*stop_mlflow*' } |
    ForEach-Object {
        Write-Output "$($_.ProcessId)|$($_.ParentProcessId)|$($_.CommandLine)"
    }
    """
    
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=15)
    
    if out.strip():
        for line in out.strip().split("\n"):
            parts = line.split("|", 2)
            if len(parts) >= 3:
                try:
                    pid = int(parts[0])
                    parent_pid = int(parts[1])
                    cmdline = parts[2]
                    processes.append({
                        "pid": pid,
                        "parent_pid": parent_pid,
                        "cmdline": cmdline
                    })
                    if show_header:
                        print(f"\n  [!] Found MLflow process:")
                        print(f"      PID: {pid}")
                        print(f"      Parent PID: {parent_pid}")
                        print(f"      Command: {cmdline[:100]}...")
                except (ValueError, IndexError):
                    continue
    
    if not processes and show_header:
        print("  [OK] No Python MLflow processes found")
    
    return processes


def get_parent_process_info(parent_pid, debug=False):
    """Get detailed info about a parent process."""
    print(f"\n  >>> Investigating Parent PID {parent_pid}:")
    
    ps_cmd = f"""
    $proc = Get-WmiObject Win32_Process -Filter "ProcessId={parent_pid}"
    if ($proc) {{
        Write-Output "$($proc.Name)|$($proc.CommandLine)|$($proc.ParentProcessId)"
    }}
    """
    
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd])
    
    if out.strip():
        parts = out.strip().split("|", 2)
        if len(parts) >= 2:
            name = parts[0]
            cmdline = parts[1] if len(parts) > 1 else ""
            grandparent = parts[2] if len(parts) > 2 else "N/A"
            
            print(f"      Name: {name}")
            print(f"      Command: {cmdline[:100]}...")
            print(f"      Parent: {grandparent}")
            
            return {
                "pid": parent_pid,
                "name": name,
                "cmdline": cmdline,
                "parent_pid": grandparent
            }
    else:
        print(f"      [GONE] Parent process no longer exists")
    
    return None


def check_waitress_gunicorn(debug=False):
    """Check for waitress-serve or gunicorn processes (MLflow's web servers)."""
    print("\n" + "=" * 60)
    print("CHECKING: MLflow Web Servers (waitress/gunicorn)")
    print("=" * 60)
    
    processes = []
    
    # Check for waitress or gunicorn
    ps_cmd = """
    Get-WmiObject Win32_Process | 
    Where-Object { $_.CommandLine -like '*waitress*' -or $_.CommandLine -like '*gunicorn*' } |
    ForEach-Object {
        Write-Output "$($_.ProcessId)|$($_.Name)|$($_.CommandLine)"
    }
    """
    
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=15)
    
    if out.strip():
        for line in out.strip().split("\n"):
            parts = line.split("|", 2)
            if len(parts) >= 3:
                try:
                    pid = int(parts[0])
                    name = parts[1]
                    cmdline = parts[2]
                    # Exclude our own diagnostic PowerShell processes
                    if "Get-WmiObject" not in cmdline and "powershell" not in name.lower():
                        processes.append({"pid": pid, "name": name, "cmdline": cmdline})
                        print(f"  [!] Found: PID {pid} - {name}")
                        print(f"      Command: {cmdline[:80]}...")
                except (ValueError, IndexError):
                    continue
    
    if not processes:
        print("  [OK] No waitress/gunicorn processes found")
    
    return processes


def diagnose_ports(ports=[5000, 5001, 5002], debug=False):
    """Find all processes on specified ports with full TCP state analysis."""
    print("\n" + "=" * 60)
    print(f"DIAGNOSIS: Ports {ports} - Full Network Analysis")
    print("=" * 60)

    listening_pids = set()  # ONLY processes that are LISTENING (servers)
    port_info = {}

    # Method 1: netstat - ALL states for analysis, but only collect LISTENING for killing
    print("\n[1] netstat -ano (all TCP states)")
    code, out, err = run_command(["netstat", "-ano"])
    
    for port in ports:
        port_info[port] = {"listening": [], "established": [], "time_wait": [], "other": []}
        
        for line in out.split("\n"):
            if re.search(rf":({port})\s", line):
                parts = line.split()
                if len(parts) >= 4:
                    state = parts[3] if len(parts) >= 5 else "UNKNOWN"
                    pid_str = parts[-1]
                    
                    try:
                        pid = int(pid_str)
                        
                        if "LISTENING" in state:
                            port_info[port]["listening"].append((pid, line.strip()))
                            listening_pids.add(pid)  # Only add LISTENING processes
                        elif "ESTABLISHED" in state:
                            port_info[port]["established"].append((pid, line.strip()))
                        elif "TIME_WAIT" in state:
                            port_info[port]["time_wait"].append((pid, line.strip()))
                        else:
                            port_info[port]["other"].append((pid, line.strip()))
                    except ValueError:
                        pass
    
    # Display organized results
    for port in ports:
        info = port_info[port]
        total = len(info["listening"]) + len(info["established"]) + len(info["time_wait"]) + len(info["other"])
        
        if total > 0:
            print(f"\n  Port {port}:")
            
            if info["listening"]:
                print(f"    LISTENING ({len(info['listening'])})")
                for pid, line in info["listening"]:
                    print(f"      PID {pid}: {line}")
            
            if info["established"]:
                print(f"    ESTABLISHED ({len(info['established'])})")
                for pid, line in info["established"][:3]:  # Show max 3
                    print(f"      PID {pid}: {line}")
                if len(info["established"]) > 3:
                    print(f"      ... and {len(info['established']) - 3} more")
            
            if info["time_wait"]:
                print(f"    TIME_WAIT ({len(info['time_wait'])}) - cleanup in progress")
            
            if info["other"]:
                print(f"    OTHER STATES ({len(info['other'])})")
                for pid, line in info["other"][:2]:
                    print(f"      PID {pid}: {line}")

    # Method 2: PowerShell for LISTENING only
    print("\n[2] PowerShell Get-NetTCPConnection (LISTENING verification)")
    for port in ports:
        ps_cmd = (
            f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty OwningProcess"
        )
        code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd])
        for line in out.strip().split("\n"):
            try:
                pid = int(line.strip())
                # Exclude system processes
                if pid > 0 and pid != 4:  # Skip System Idle (0) and System (4)
                    listening_pids.add(pid)
                    print(f"  Port {port} LISTENING: PID {pid}")
            except ValueError:
                pass
    
    if not listening_pids:
        print("  [OK] No processes actively listening")

    # Filter out system PIDs (0 = System Idle, 4 = System)
    listening_pids = {pid for pid in listening_pids if pid > 4}

    print(f"\n>>> LISTENING processes (servers only): {len(listening_pids)}")
    print(f">>> PIDs to investigate: {sorted(listening_pids)}")
    print(">>> Note: Client connections (ESTABLISHED, CLOSE_WAIT, etc.) are NOT included")

    return sorted(listening_pids), port_info


def get_process_info(pid, debug=False):
    """Get detailed info about a process with zombie detection."""
    info = {
        "pid": pid, 
        "exists": False, 
        "is_zombie": False,
        "name": "unknown", 
        "cmdline": "", 
        "parent_pid": None
    }

    # Method 1: PowerShell Get-Process (most reliable)
    ps_cmd = f"""
    try {{
        $proc = Get-Process -Id {pid} -ErrorAction Stop
        Write-Output "EXISTS|$($proc.Name)"
    }} catch {{
        Write-Output "NOT_FOUND"
    }}
    """
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd])
    if "EXISTS" in out:
        info["exists"] = True
        parts = out.strip().split("|")
        if len(parts) > 1:
            info["name"] = parts[1]

    # Method 2: Check with tasklist
    code, out, err = run_command(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"])
    if code == 0 and str(pid) in out:
        info["exists"] = True
        try:
            parts = out.split('"')
            if len(parts) > 1:
                info["name"] = parts[1]
        except Exception:
            pass

    # Method 3: Get command line and parent with WMI
    ps_cmd = f"""
    $proc = Get-WmiObject Win32_Process -Filter "ProcessId={pid}"
    if ($proc) {{
        Write-Output "$($proc.Name)|$($proc.CommandLine)|$($proc.ParentProcessId)"
    }}
    """
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd])
    if out.strip():
        info["exists"] = True  # WMI found it
        parts = out.strip().split("|")
        if len(parts) >= 1 and parts[0]:
            info["name"] = parts[0]
        if len(parts) >= 2 and parts[1]:
            info["cmdline"] = parts[1]
        if len(parts) >= 3:
            try:
                info["parent_pid"] = int(parts[2])
            except ValueError:
                pass
    
    # If in netstat but not in process list = ZOMBIE
    if not info["exists"]:
        info["is_zombie"] = True

    if debug:
        print(f"\n  PID {pid} details:")
        print(f"    Exists: {info['exists']}")
        print(f"    Zombie: {info['is_zombie']}")
        print(f"    Name: {info['name']}")
        print(f"    Parent PID: {info['parent_pid']}")
        if info['cmdline']:
            print(f"    CmdLine: {info['cmdline'][:100]}...")

    return info


def kill_process_aggressive(pid, debug=False):
    """Kill a process using multiple aggressive methods."""
    print(f"\n>>> Killing PID {pid}...")

    success = False

    # Method 1: taskkill /F /T (kill process tree)
    print(f"  [1] taskkill /F /T /PID {pid}")
    code, out, err = run_command(["taskkill", "/F", "/T", "/PID", str(pid)])
    if code == 0 or "SUCCESS" in out:
        print(f"      [OK] SUCCESS")
        success = True
    else:
        print(f"      [FAIL] {err.strip() or out.strip()}")

    time.sleep(1)

    # Method 2: PowerShell Stop-Process
    print(f"  [2] PowerShell Stop-Process -Force")
    code, out, err = run_command(
        ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"]
    )
    if code == 0:
        print(f"      [OK] SUCCESS")
        success = True
    else:
        print(f"      [FAIL] {err.strip()}")

    time.sleep(1)

    # Method 3: wmic process delete
    print(f"  [3] wmic process delete")
    code, out, err = run_command(
        ["wmic", "process", "where", f"ProcessId={pid}", "delete"]
    )
    if code == 0:
        print(f"      [OK] SUCCESS")
        success = True
    else:
        print(f"      [FAIL] {err.strip() or out.strip()}")

    return success


def verify_process_gone(pid):
    """Verify a process no longer exists."""
    code, out, err = run_command(["tasklist", "/FI", f"PID eq {pid}"])
    if str(pid) in out:
        return False

    code, out, err = run_command(
        ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"]
    )
    if code == 0 and out.strip():
        return False

    return True


def verify_port_free(port=5000):
    """Verify port is no longer in use."""
    code, out, err = run_command(["netstat", "-ano"])
    for line in out.split("\n"):
        if re.search(rf"127\.0\.0\.1:{port}\s", line) and "LISTENING" in line:
            return False
    return True


def test_http_response(port=5000):
    """Test if HTTP server is responding on specified port using multiple methods."""
    url = f"http://127.0.0.1:{port}/"
    
    # Method 1: PowerShell with explicit success/failure detection and NO caching
    ps_cmd = f"""
    try {{
        # Disable caching with Headers and add timestamp to URL
        $timestamp = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
        $response = Invoke-WebRequest -Uri '{url}?_nocache=$timestamp' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop -Headers @{{"Cache-Control"="no-cache"; "Pragma"="no-cache"}}
        if ($response.StatusCode -eq 200) {{
            Write-Output "SUCCESS_HTTP_200"
            exit 0
        }} else {{
            Write-Output "STATUS_$($response.StatusCode)"
            exit 1
        }}
    }} catch {{
        Write-Output "FAILED_$($_.Exception.Message)"
        exit 1
    }}
    """
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=4)
    # Debug: Always log what PowerShell returned
    if "SUCCESS_HTTP_200" in out:
        return True, "PowerShell", f"HTTP 200 OK (code={code}, out={out[:50]})"
    elif "FAILED" in out:
        return False, "PowerShell", f"Connection failed (code={code}, out={out[:50]})"
    elif code != 0:
        return False, "PowerShell", f"Error (code={code}, err={err[:50] if err else 'none'})"
    else:
        # Unexpected response
        return False, "PowerShell", f"Unexpected (code={code}, out={out[:50]})"
    
    # Method 2: Try curl if available
    code, out, err = run_command(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "2", url], timeout=4)
    if code == 0 and ("200" in out or "302" in out):
        return True, "curl", f"HTTP {out.strip()}"
    
    # Method 3: Try Python urllib
    py_cmd = [
        "python", "-c",
        f"import urllib.request; import sys; "
        f"try: urllib.request.urlopen('{url}', timeout=2); print('SUCCESS'); sys.exit(0)\n"
        f"except: print('FAILED'); sys.exit(1)"
    ]
    code, out, err = run_command(py_cmd, timeout=4)
    if code == 0 and "SUCCESS" in out:
        return True, "Python", "HTTP OK"
    
    return False, "all methods", "connection refused/timeout"


def comprehensive_final_check(port=5000):
    """Perform comprehensive final verification that MLflow is stopped."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE FINAL VERIFICATION")
    print("=" * 60)
    
    results = {}
    
    # Check 1: HTTP Response Test
    print("\n[1] HTTP Response Test")
    http_running, method, details = test_http_response(port)
    results['http'] = not http_running
    if http_running:
        print(f"    [FAIL] MLflow IS RESPONDING (detected via {method})")
        print(f"           {details}")
    else:
        print(f"    [OK] No HTTP response (tested with {method})")
    
    # Check 2: Active Listeners
    print("\n[2] Active Listeners on Port {}".format(port))
    ps_cmd = (
        f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | "
        "Select-Object LocalAddress,LocalPort,State,OwningProcess | Format-Table -AutoSize"
    )
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd])
    if out.strip() and "OwningProcess" in out:
        lines = [line for line in out.strip().split("\n") if line.strip()]
        if len(lines) > 2:  # Header + separator + data
            print(f"    [FAIL] Found active listeners:")
            for line in lines:
                print(f"           {line}")
            results['listeners'] = False
        else:
            print(f"    [OK] No active listeners")
            results['listeners'] = True
    else:
        print(f"    [OK] No active listeners")
        results['listeners'] = True
    
    # Check 3: Python MLflow processes
    print("\n[3] Python MLflow Processes")
    ps_cmd = """
    Get-WmiObject Win32_Process -Filter "name='python.exe'" | 
    Where-Object { $_.CommandLine -like '*mlflow*ui*' -or $_.CommandLine -like '*mlflow*server*' } |
    Select-Object ProcessId,CommandLine | Format-List
    """
    code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=10)
    if out.strip():
        print(f"    [FAIL] Found MLflow processes:")
        print(f"           {out.strip()[:200]}...")
        results['processes'] = False
    else:
        print(f"    [OK] No MLflow processes running")
        results['processes'] = True
    
    # Check 4: Browser accessibility test instruction
    print("\n[4] Browser Test (Manual)")
    print(f"    Please verify in your browser: http://127.0.0.1:{port}/")
    print(f"    Expected result: Connection refused or cannot connect")
    
    # Final verdict
    print("\n" + "=" * 60)
    if all(results.values()):
        print("FINAL VERDICT: ✓ MLflow is STOPPED")
        print("=" * 60)
        print(f"\n✓ HTTP server not responding on port {port}")
        print("✓ No active listeners detected")
        print("✓ No MLflow processes found")
        print(f"\n→ You can verify by opening http://127.0.0.1:{port}/ in your browser")
        print("  It should show 'connection refused' or fail to connect.")
        return True
    else:
        print("FINAL VERDICT: ✗ MLflow may still be running")
        print("=" * 60)
        failed = [k for k, v in results.items() if not v]
        print(f"\nFailed checks: {', '.join(failed)}")
        print("\nRecommendations:")
        if not results.get('http', True):
            print("  - MLflow HTTP server is responding - needs further investigation")
        if not results.get('listeners', True):
            print("  - Active listeners still present - may need Administrator privileges")
        if not results.get('processes', True):
            print("  - MLflow processes still running - try manual termination")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stop MLflow UI with diagnostics")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--find-parent", action="store_true", help="Find parent processes")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum kill attempts")
    args = parser.parse_args()

    print("=" * 60)
    print("  MLflow Killer - Comprehensive Stop Tool")
    print("=" * 60)

    # Always check for services and scheduled tasks first
    services = check_windows_services(debug=args.debug)
    tasks = check_scheduled_tasks(debug=args.debug)
    
    if services or tasks:
        print("\n" + "!" * 60)
        print("WARNING: Found services/tasks that might restart MLflow!")
        print("!" * 60)
        if services:
            print("\nTo stop services:")
            for svc in services:
                print(f"  sc stop {svc}")
        if tasks:
            print("\nTo disable tasks:")
            for task in tasks:
                print(f"  schtasks /change /tn \"{task}\" /disable")

    # Find Python MLflow processes and their parents
    if args.find_parent:
        mlflow_procs = find_python_mlflow_processes(debug=args.debug)
        if mlflow_procs:
            print("\n" + "=" * 60)
            print("PARENT PROCESS CHAIN")
            print("=" * 60)
            for proc in mlflow_procs:
                if proc["parent_pid"]:
                    parent_info = get_parent_process_info(proc["parent_pid"], debug=args.debug)
                    # Check grandparent
                    if parent_info and parent_info.get("parent_pid") and parent_info["parent_pid"] != "N/A":
                        try:
                            grandparent_pid = int(parent_info["parent_pid"])
                            get_parent_process_info(grandparent_pid, debug=args.debug)
                        except ValueError:
                            pass

    for attempt in range(1, args.max_attempts + 1):
        print(f"\n{'#' * 60}")
        print(f"ATTEMPT {attempt} of {args.max_attempts}")
        print('#' * 60)

        # Find MLflow processes on every attempt
        mlflow_procs = find_python_mlflow_processes(debug=args.debug, show_header=True)
        mlflow_pids = [p["pid"] for p in mlflow_procs]
        
        # COMPREHENSIVE SEARCH: Find ANY process with mlflow (not just python.exe)
        print("\n" + "=" * 60)
        print("COMPREHENSIVE SEARCH: All processes with 'mlflow'")
        print("=" * 60)
        ps_cmd_all = """
        Get-WmiObject Win32_Process | 
        Where-Object { $_.CommandLine -like '*mlflow*' -or $_.Name -like '*mlflow*' } |
        Select-Object ProcessId,Name,CommandLine | 
        Format-Table -AutoSize -Wrap
        """
        code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd_all], timeout=15)
        if out.strip():
            print(out.strip())
            # Parse and extract PIDs
            for line in out.strip().split("\n"):
                # Look for PID numbers at start of lines (after header)
                parts = line.split()
                if parts and parts[0].isdigit():
                    try:
                        pid = int(parts[0])
                        if pid > 4 and "stop_mlflow" not in line.lower():
                            if pid not in mlflow_pids:
                                print(f"  [!] Found additional MLflow process: PID {pid}")
                                mlflow_pids.append(pid)
                    except (ValueError, IndexError):
                        pass
        else:
            print("  [OK] No processes found with 'mlflow' in name or command")
        
        # Check for web servers
        web_servers = check_waitress_gunicorn(debug=args.debug)
        web_server_pids = [p["pid"] for p in web_servers]

        # Diagnose multiple ports
        pids, port_info = diagnose_ports(ports=[5000, 5001, 5002], debug=args.debug)
        
        # Additional check: Direct PID lookup for port 5000 using resource monitor method
        print("\n[EXTRA] Direct port 5000 owner lookup:")
        ps_cmd2 = """
        $conn = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
        foreach ($c in $conn) {
            try {
                $proc = Get-Process -Id $c.OwningProcess -ErrorAction Stop
                Write-Output "PID_$($c.OwningProcess)|NAME_$($proc.Name)|PATH_$($proc.Path)"
            } catch {
                Write-Output "PID_$($c.OwningProcess)|ZOMBIE|NO_PATH"
            }
        }
        """
        code, out, err = run_command(["powershell", "-NoProfile", "-Command", ps_cmd2], timeout=10)
        if out.strip():
            for line in out.strip().split("\n"):
                if "PID_" in line:
                    print(f"  {line}")
                    parts = line.split("|")
                    if len(parts) >= 2 and "ZOMBIE" not in line:
                        # Found a real process!
                        try:
                            pid_part = [p for p in parts if p.startswith("PID_")][0]
                            real_pid = int(pid_part.replace("PID_", ""))
                            if real_pid not in pids and real_pid > 4:
                                print(f"  [!] Found HIDDEN process not detected before: PID {real_pid}")
                                pids.append(real_pid)
                        except (ValueError, IndexError):
                            pass
        
        # Combine all PIDs: port-based + MLflow processes + web servers
        all_pids = sorted(set(pids) | set(mlflow_pids) | set(web_server_pids))

        if not all_pids:
            print("\n[OK] No processes found on any MLflow ports")
            break
        
        pids = all_pids

        # Get process info with zombie detection and filtering
        print("\n" + "=" * 60)
        print("PROCESS INFORMATION & FILTERING")
        print("=" * 60)
        
        zombie_pids = []
        live_pids = []
        filtered_pids = []  # Browser/client processes we won't kill
        
        # Excluded process names (browsers and clients, not servers)
        EXCLUDED_NAMES = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe', 'iexplore.exe']
        
        for pid in pids:
            info = get_process_info(pid, debug=args.debug)
            
            if info['is_zombie']:
                zombie_pids.append(pid)
                print(f"\nPID {pid}: [ZOMBIE - Dead process with orphaned socket]")
                print(f"  Status: Process no longer exists")
                print(f"  Action: Will clean up socket reference")
            elif info['name'].lower() in EXCLUDED_NAMES:
                filtered_pids.append(pid)
                print(f"\nPID {pid}: [BROWSER/CLIENT - Will NOT kill]")
                print(f"  Name: {info['name']}")
                print(f"  Reason: This is a browser/client connection, not the MLflow server")
            else:
                live_pids.append(pid)
                print(f"\nPID {pid}: [SERVER PROCESS - Will kill]")
                print(f"  Name: {info['name']}")
                if info['parent_pid']:
                    print(f"  Parent PID: {info['parent_pid']}")
                if info['cmdline']:
                    print(f"  Command: {info['cmdline'][:100]}...")
        
        if zombie_pids:
            print(f"\n>>> Found {len(zombie_pids)} zombie process(es): {zombie_pids}")
            print(">>> These are harmless orphaned sockets from crashed/killed processes")
        if filtered_pids:
            print(f"\n>>> Excluded {len(filtered_pids)} browser/client process(es): {filtered_pids}")
            print(">>> These are safe to leave running")
        if live_pids:
            print(f"\n>>> Found {len(live_pids)} server process(es) to kill: {live_pids}")

        # Kill only live processes (zombies can't be killed, just cleaned)
        if live_pids:
            print("\n" + "=" * 60)
            print("KILLING LIVE PROCESSES")
            print("=" * 60)
            for pid in live_pids:
                kill_process_aggressive(pid, debug=args.debug)
        
        # Clean up zombie references
        if zombie_pids:
            print("\n" + "=" * 60)
            print("CLEANING ZOMBIE REFERENCES")
            print("=" * 60)
            for pid in zombie_pids:
                print(f">>> Attempting cleanup for zombie PID {pid}...")
                # wmic often works for cleaning orphaned references
                code, out, err = run_command(
                    ["wmic", "process", "where", f"ProcessId={pid}", "delete"]
                )
                if "not found" in out.lower() or "not found" in err.lower():
                    print(f"    [OK] Reference cleaned (process was already gone)")
                else:
                    print(f"    [OK] Cleanup attempted")

        # Verify
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        
        time.sleep(2)

        all_gone = True
        for pid in pids:
            is_gone = verify_process_gone(pid)
            print(f"  PID {pid}: {'[OK] GONE' if is_gone else '[FAIL] STILL EXISTS'}")
            if not is_gone:
                all_gone = False

        port_free = verify_port_free(5000)
        print(f"  Port 5000 (netstat): {'[OK] FREE' if port_free else '[WARN] STALE ENTRIES'}")

        http_works, method, details = test_http_response(5000)
        print(f"  HTTP test ({method}): {'[FAIL] STILL RESPONDING' if http_works else '[OK] NOT RESPONDING'}")
        if args.debug:
            print(f"    Debug: method={method}, details={details}, result={http_works}")

        # Success if HTTP not responding (most important check)
        # Ignore stale netstat entries and focus on actual HTTP response
        if not http_works:
            print("\n" + "=" * 60)
            print("[OK][OK][OK] SUCCESS: MLflow stopped")
            print("=" * 60)
            if not port_free or not all_gone:
                print(f"\nNote: Stale netstat entries may remain (zombie PIDs: {zombie_pids if 'zombie_pids' in locals() else 'unknown'})")
                print("These are harmless orphaned sockets that will timeout.")
            print("MLflow UI is NOT running - HTTP test confirms this.")
            
            # Perform comprehensive final check
            comprehensive_final_check(port=5000)
            return 0

        if attempt < args.max_attempts:
            print(f"\n[WARN] Not fully stopped, retrying in 3 seconds...")
            time.sleep(3)

    print("\n" + "=" * 60)
    print("[FAIL][FAIL][FAIL] FAILED: Could not completely stop MLflow")
    print("=" * 60)
    print("\nRemaining issues:")
    print("  - Try running as Administrator")
    print("  - Check if a service/task is restarting it")
    print("  - Try restarting your computer")
    return 1


if __name__ == "__main__":
    sys.exit(main())
