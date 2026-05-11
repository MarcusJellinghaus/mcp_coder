# Step 2 — Verify VSCode identity via `create_time` (Item #2)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`) in
> full. Implement only what this step describes. Follow TDD: write failing
> tests first, then implementation, then run the three MCP quality checks.
> One commit at the end.

## Goal

Close the PID-reuse hole that lets unrelated live VSCode processes pin dead
sessions in `sessions.json`. The stored PID's `create_time` must match the
process actually running under that PID — otherwise it's a different process.

## Design choice (KISS deviation from issue)

The issue prescribes capturing `create_time` at launch *and* in
`update_session_pid`. Since the issue itself notes that launch-time capture
on Windows almost always returns `None` (launcher `.cmd` exits immediately),
this step uses **`update_session_pid` as the only populator**.
`build_session` always stores `None`; the field self-populates on the first
cmdline-match refresh after launch. Single populator → atomic invariant is
self-enforcing.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/types.py`
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_types.py` (if existing migration coverage)

## WHAT — function signatures

```python
# types.py
class VSCodeClaudeSession(TypedDict):
    folder: str
    repo: str
    issue_number: int
    status: str
    vscode_pid: int | None
    vscode_pid_create_time: float | None  # NEW
    started_at: str
    is_intervention: bool

# sessions.py
def check_vscode_running(
    pid: int | None,
    expected_create_time: float | None,
) -> bool: ...

def update_session_pid(folder: str, pid: int) -> None:
    """Atomically writes both vscode_pid and vscode_pid_create_time."""
```

`build_session` signature unchanged — internally sets
`vscode_pid_create_time=None`.

## HOW — integration points

- All reads use `session.get("vscode_pid_create_time")` — never subscript.
- `is_session_active` call site at `sessions.py:556` passes
  `session.get("vscode_pid_create_time")` to `check_vscode_running`.
- `update_session_pid` callers unchanged (`is_session_active`,
  `build_active_session_set`, `session_restart.py:409`). Atomicity is enforced
  inside the function — no caller can write one field without the other.
- `helpers.py:build_session` adds `"vscode_pid_create_time": None` to the
  returned dict.

## ALGORITHM

```
# update_session_pid(folder, pid):
try:
    create_time = psutil.Process(pid).create_time()
except (psutil.NoSuchProcess, psutil.AccessDenied):
    create_time = None
for session in store["sessions"]:
    if session["folder"] == folder:
        session["vscode_pid"] = pid
        session["vscode_pid_create_time"] = create_time
        break
save_sessions(store)

# check_vscode_running(pid, expected_create_time):
if pid is None or not psutil.pid_exists(pid):
    return False
proc = psutil.Process(pid)
if proc.name().lower() not in VSCODE_PROCESS_NAMES:
    return False
if expected_create_time is not None and abs(proc.create_time() - expected_create_time) > 1.0:
    return False
return True
```

## DATA

- `VSCodeClaudeSession.vscode_pid_create_time: float | None`
  (Unix epoch seconds from `psutil.Process.create_time()`).
- Tolerance `1.0` seconds for float comparison.
- Return values unchanged (`bool`, `None`).

## Tests (write first)

1. **Migration**: load a `sessions.json` payload missing
   `vscode_pid_create_time` → no error; session usable;
   `check_vscode_running(pid, None)` falls back to loose name-only check.
2. **Identity mismatch**: stored `create_time = 1000.0`, mock
   `psutil.Process(pid).create_time()` to return `2000.0` →
   `check_vscode_running(pid, 1000.0)` returns `False`.
3. **Identity match within tolerance**: stored `1000.0`, actual `1000.5` →
   `True`.
4. **`update_session_pid` atomic write**: pre-existing session with
   `vscode_pid=100, vscode_pid_create_time=500.0`. Mock
   `psutil.Process(200).create_time()` to return `999.0`. Call
   `update_session_pid(folder, 200)`. Reload store. Assert
   `vscode_pid == 200 and vscode_pid_create_time == 999.0`.
5. **`update_session_pid` handles dead PID**: mock `psutil.Process` to raise
   `NoSuchProcess`. Call → `vscode_pid` updates; `vscode_pid_create_time` is
   `None`.
6. **`build_session` defaults**: returned dict has
   `"vscode_pid_create_time": None`.

## Done when

- All new and existing tests pass.
- mypy clean (TypedDict change picked up across callers).
- pylint clean.
- One commit: tests + implementation.
