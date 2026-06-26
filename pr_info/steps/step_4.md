# Step 4 — Detection snapshot + `gather_signals` (Windows / IO boundary)

**Read first:** [summary.md](./summary.md) (sections "The pipeline", R4 age-skew,
R6 independent signals, grace window). This is the **only** place that touches
psutil/win32. It produces `DetectionSignals`; everything downstream is pure.

## WHERE
- Create: `src/mcp_coder/workflows/vscodeclaude/detection.py`
- Tests: `tests/workflows/vscodeclaude/test_detection.py`
- Modify: `__init__.py` (export)
- Reuse (import) from `sessions.py`: `_get_vscode_processes`, `_get_vscode_window_titles`,
  `_get_vscode_pids`, `check_vscode_running`, `LAUNCH_GRACE_SECONDS`, `HAS_WIN32GUI`.

## WHAT
```python
@dataclass(frozen=True)
class DetectionSnapshot:
    processes: tuple[dict[str, Any], ...]      # pid + cmdline_lower
    window_titles: tuple[tuple[int, str], ...]
    pids: frozenset[int]
    captured_at: datetime

def capture_detection_snapshot() -> DetectionSnapshot:
    """Populate ALL THREE caches at one instant, freeze the result."""

def gather_signals(session: VSCodeClaudeSession, snapshot: DetectionSnapshot) -> DetectionSignals:
    """Compute the 7 raw signals for one session from the frozen snapshot."""
```

## HOW
- `capture_detection_snapshot` refreshes the three module caches in immediate
  succession (`_get_vscode_processes(refresh=True)`, `_get_vscode_window_titles(refresh=True)`,
  then read `_get_vscode_pids()`), so **no signal ages relative to another** (R4).
- `gather_signals` reads only the snapshot + the session dict + `Path.exists` +
  `check_vscode_running` (stored pid). **No folder-gone short-circuit** — compute
  `folder_exists` and `pid_alive` independently (R6).
- **`directory_empty`** is computed here (IO boundary), **not** in the pure `decide`:
  `directory_empty = folder_exists and not any(Path(folder).iterdir())`. `decide`
  consumes it to gate destruction on `No Git`/`Error` folders (DECISION 2).
- **`within_grace`** is computed here as a **plain bool**:
  `within_grace = age_seconds < LAUNCH_GRACE_SECONDS` (keeps `types.py` dependency-free).
- Title match: port the bracket `[#N` + repo-name binding logic from
  `is_vscode_window_open_for_folder`, but read from `snapshot` (pure over snapshot).
- Cmdline match + `found_pid`: scan `snapshot.processes` for folder path/name.
- **Grace handling:** if `within_grace` and there is no title, do not treat the
  title-miss as evidence of death — `gather` just reports the raw signals and the
  pure rule order already falls through to pid/cmdline. (Keep `LAUNCH_GRACE_SECONDS`.)

## ALGORITHM (`gather_signals`)
```
folder = session["folder"]
folder_exists = Path(folder).exists()
directory_empty = folder_exists and not any(Path(folder).iterdir())
title_match   = _title_binds(snapshot, folder, session["issue_number"], session["repo"])
cmdline_match, found_pid = _cmdline_scan(snapshot, folder)
pid_alive = check_vscode_running(session.get("vscode_pid"), session["vscode_pid_create_time"])
age = (now - parse(session["started_at"])) or inf
within_grace = age < LAUNCH_GRACE_SECONDS
return DetectionSignals(folder_exists, title_match, cmdline_match, pid_alive,
                        found_pid, age, within_grace, directory_empty)
```

## DATA
`DetectionSnapshot` (frozen), `DetectionSignals` (Step 1).

## Tests (write first) — mock psutil/win32 helpers
- title bind: title contains `[#38 ...repo` AND owning pid has folder in cmdline → `title_match=True`.
- restore case: title hit, cmdline miss → `title_match=True, cmdline_match=False`.
- zombie: `folder_exists=False` but a process with the folder in cmdline / a live
  stored pid → `pid_alive`/`cmdline_match` still computed (no short-circuit).
- non-Windows (`HAS_WIN32GUI=False`): `title_match=False`, falls to cmdline/pid.
- `directory_empty`: empty existing folder → `True`; non-empty → `False`; missing → `False`.
- `within_grace`: `age < LAUNCH_GRACE_SECONDS` → `True`, else `False` (plain bool).
- `capture_detection_snapshot` returns frozen tuples; calling the three refreshers once.

## Done when
All three checks pass. One commit.
