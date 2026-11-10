# Step 5 — Window title authoritative on Windows after grace

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`), then implement Step 5 only:
> - window-enumeration success flag
> - `window_count` and `title_authoritative` signals
> - the new `assess_liveness` order (producing `LivenessRule.NO_WINDOW`, added in Step 4)
> - the DEBUG title dump on an authoritative miss
>
> Write the tests first, then the implementation. Run the checks from the summary, then make one commit.

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/detection.py`**

`_get_vscode_window_titles(refresh: bool = False) -> tuple[list[tuple[int, str]], bool]` returns `(titles, ok)`:

| Case | Return |
|---|---|
| no win32gui | `([], False)` |
| cache hit | `(cache, True)` |
| `EnumWindows` raises | `([], False)` (not cached, as today) |
| success | `(entries, True)` |

Docstring: drop "so callers can bind a title match to the specific VSCode instance …". Keep that the PID is the owning process.

`DetectionSnapshot` gains `window_enum_ok: bool`. `capture_detection_snapshot` unpacks `window_titles, window_enum_ok = _get_vscode_window_titles(refresh=True)`.

`gather_signals` additions:
```python
window_count = len(snapshot.window_titles)
title_authoritative = bool(
    HAS_WIN32GUI
    and snapshot.window_enum_ok
    and session.get("repo")
    and not (snapshot.pids and window_count == 0)
)
if title_authoritative and not title_match:
    logger.debug("Title miss for #%s; VSCode windows: %s",
                 session["issue_number"], list(snapshot.window_titles))
```
Both values are passed to `DetectionSignals`.

Wording:
- `LAUNCH_GRACE_SECONDS` comment: beyond grace, the title check is authoritative on Windows when win32gui is available, window enumeration succeeded, the session has a repo, and at least one VSCode window was seen while `Code.exe` runs.
- Module docstring and `gather_signals` docstring: replace "seven raw signals" with "the raw signals". List `window_count` / `title_authoritative` next to `directory_empty` / `within_grace` as values computed here.

**`src/mcp_coder/workflows/vscodeclaude/types.py`**
- `DetectionSignals`: add `window_count: int` and `title_authoritative: bool`, with no defaults.
- `_flatten()["signals"]`: add both keys.

**`src/mcp_coder/workflows/vscodeclaude/assessment.py`**
- `assess_liveness`: new order (see ALGORITHM). Rewrite the docstring: title-positive always wins; past grace with an authoritative title a miss is decisive (`NO_WINDOW` when only VSCode's shared main process still references the folder); otherwise pid → cmdline → folder fallback; no folder-gone short-circuit before the title/pid checks.
- `_log_assessment`: add `window_count=%s title_authoritative=%s` to the DEBUG signals line.

**`docs/coordinator-vscodeclaude.md`** (Session States)
- On Windows a session whose window is closed but whose folder VSCode's main process still references shows `Closed (no_window)`. It is never deleted, only restarted if eligible. Remedy: close all VSCode windows.

## ALGORITHM (`assess_liveness`)

```
if s.title_match:                                  return active(TITLE)
if s.title_authoritative and not s.within_grace:
    if not s.folder_exists:                        return inactive(NO_ARTIFACTS)
    if s.pid_alive or s.cmdline_match:             return inactive(NO_WINDOW)
    return inactive(NO_MATCH)
if s.pid_alive:                                    return active(PID)
if s.cmdline_match:                                return active(CMDLINE)
return inactive(NO_ARTIFACTS if not s.folder_exists else NO_MATCH)
```

The delete/restart guards from Step 4 already apply, so `NO_WINDOW` never deletes and a fresh authoritative miss is only acted on after the confirmation run.

## DATA

```python
@dataclass(frozen=True)
class DetectionSnapshot:
    processes: tuple[dict[str, Any], ...]
    window_titles: tuple[tuple[int, str], ...]
    pids: frozenset[int]
    window_enum_ok: bool
    captured_at: datetime
```

## Tests (write first)

**`conftest.py`**
- `make_signals` gains `window_count: int = 0` and `title_authoritative: bool = False`.
- `_build_assessment`'s `DetectionSignals(...)` gets `window_count=0, title_authoritative=False`.

**Constructors** — add the new fields to every direct `DetectionSignals(...)` / `DetectionSnapshot(...)` call:
- `test_audit.py`, `test_cleanup.py`, `test_closed_issues_integration.py`, `test_status_display_scenario.py`, `test_detection.py` (snapshot helper ~line 66), `test_workspace_untrusted.py`
- plus any other hit from `search_files`.

**Fakes** — make every fake of `_get_vscode_window_titles` return `(titles, True)`:
- `test_detection.py` ~line 315, `test_detection_probes.py`.

**`test_assessment_layers.py`** — one parametrized `assess_liveness` matrix:

| `title_authoritative` | `within_grace` | other signals | expected |
|---|---|---|---|
| True | False | pid alive, folder exists | inactive `NO_WINDOW` |
| True | False | cmdline match, folder exists | inactive `NO_WINDOW` |
| True | False | pid alive, folder missing | inactive `NO_ARTIFACTS` |
| True | False | nothing | inactive `NO_MATCH` |
| True | True | pid alive | active `PID` |
| True | True | cmdline match | active `CMDLINE` |
| False | False | pid alive / cmdline match | active `PID` / `CMDLINE` (unchanged) |
| True | False | title match | active `TITLE` |

- Stale wording: replace the "tie-breaker" wording in `test_assessment_layers.py` (docstrings/comments describing PID as a tie-breaker) so it matches the new `assess_liveness` contract.

**`test_detection.py`** — `gather_signals`, monkeypatching `HAS_WIN32GUI` in `detection`:
- `title_authoritative` is False for each of:
  - `window_enum_ok=False`
  - `HAS_WIN32GUI=False`
  - session without `repo`
  - `pids={1}` with no window titles
- True with win32gui, enum ok, repo and at least one title.
- `window_count == len(window_titles)`.
- DEBUG title dump: `caplog` at DEBUG on the `detection` logger. An authoritative miss logs the issue number and a title from the snapshot; a title match does not.
- `capture_detection_snapshot` / `_get_vscode_window_titles`: patch `HAS_WIN32GUI=True` and a fake `win32gui` whose `EnumWindows` raises → `([], False)` and `snapshot.window_enum_ok is False`. Without win32gui → `ok` False.

**`test_audit.py` / `test_explain.py`**
- `window_count` and `title_authoritative` appear in the audit record `signals` block and in `to_explain()` output.

## Commit

`feat(vscodeclaude): make window title authoritative on Windows after grace`
