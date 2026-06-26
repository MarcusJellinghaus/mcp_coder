# Summary — Rebuild vscodeclaude session-state around an explicit assessment model (#985)

## Goal

`mcp-coder vscodeclaude launch --cleanup` once declared a **live** VSCode session
inactive and started destroying its files (issue #38). That false-negative is one
symptom of a systemic problem: liveness, staleness, and the resulting
destructive/non-destructive action are recomputed **independently** in four code
paths (detection, cleanup, status, restart) plus the `.to_be_deleted` retry loop,
and the "why" survives only in log strings.

We rebuild the session-state surface as a **detect → assess → decide → render/apply**
pipeline, aggregated into one `SessionAssessment` built **once per session per run**
and **consumed** (never recomputed) by all five paths.

## Architectural / design changes

### KISS deviation from the issue's literal model
The issue proposes **five types** (`DetectionSignals`, `LivenessVerdict`,
`IssueState`, `Transition`, `Decision`) and **four chained public transformer
functions**. We preserve every *behavioural* requirement but collapse the type
surface to **two data boundaries** plus a single staged pure function:

| Issue's literal design | This implementation |
|------------------------|---------------------|
| 5 nested types         | `DetectionSignals` (injected input) + flat `SessionAssessment` (output) |
| 4 public transformer fns | 1 staged pure `assess_session()` (liveness → issue-state → transition → decision as ordered sections) |
| `LivenessVerdict`/`IssueState`/`Transition`/`Decision` as types | flat fields + 2 small enums on `SessionAssessment` |
| New audit abstraction  | one `audit.py` module reusing the `sessions.json` write discipline |

The "four pure layers" survive as four ordered, readable sections **inside one
function** — still pure, still independently unit-testable — without the extra
type/glue. This preserves inspectability (`--explain` = dump the flat object), the
observe/apply split, testability, and "consumers never recompute".

### The pipeline

```
capture_detection_snapshot()   # detection.py — ALL 3 caches captured at one instant (fixes R4 age-skew)
        │
        ▼
gather_signals(session, snapshot) -> DetectionSignals     # detection.py — the ONLY Windows/IO boundary
        │
        ▼
assess_session(signals, issue_facts, git_status, prior_last_active) -> SessionAssessment   # assessment.py — PURE
        │
   ┌────┴───────────────────────────────────────────────┐
   ▼ (read-only)                                          ▼ (apply() runs only)
build_assessments() -> dict[folder, SessionAssessment]   apply_assessments()  # PID refresh + last_active + audit
   │
   ├── status      (read-only consumer — never apply())
   ├── cleanup      ─┐
   ├── restart       ├─ apply() consumers: advance last_active, append audit record
   └── .to_be_deleted retry loop ─┘
```

### Key behavioural fixes (irreducible — do not simplify away)
- **R3 / #38** — title-miss **falls through** to PID/cmdline; it is no longer an
  authoritative `False`. Title-positive stays authoritative; PID is a tie-breaker only.
- **R1** — closed/stale/blocked/unassigned/ineligible and the next action are
  computed **once** inside `assess_session`; cleanup and status read the same
  `SessionAssessment`, so they cannot disagree on the same snapshot.
- **R2** — `assess_session` is pure; all writes (PID refresh, `sessions.json`,
  `last_active`, audit) move to `apply_assessments`. `status` is **write-free**.
- **R4** — one immutable `DetectionSnapshot` populates `_vscode_process_cache`,
  `_vscode_window_cache`, **and** `_vscode_pids_cache` at the same instant.
- **R6 / zombie** — `folder_exists` and `pid_alive` are gathered **independently**
  (no folder-gone short-circuit). Liveness checks title/pid/cmdline **before**
  folder existence, so a live process for a deleted folder is reachable and is
  classified `INVESTIGATE_ZOMBIE`; it self-resolves to `REMOVE_MISSING` once the
  process exits.
- **Cleanup ordering** — the `.code-workspace` launcher is deleted **only after**
  folder deletion succeeds (was: deleted first, unconditionally).
- **Lock-failure veto** — a failed delete (locked folder) **never** calls
  `remove_session`; the entry stays in `.to_be_deleted` and is retried each run.
- **`.to_be_deleted` retry loop** consumes the `SessionAssessment` instead of
  re-calling cmdline-only `is_vscode_open_for_folder` (the second #38 door).

### Liveness rule order (reconciles the issue's R6 with its rule list)
A live process must be detectable regardless of folder state, so the order is:
```
title_match   -> ACTIVE(TITLE)
pid_alive     -> ACTIVE(PID)        # tie-breaker only
cmdline_match -> ACTIVE(CMDLINE)
not folder    -> INACTIVE(NO_ARTIFACTS)
else          -> INACTIVE(NO_MATCH)
```
`INVESTIGATE_ZOMBIE` = `active and not folder_exists`; `REMOVE_MISSING` =
`not active and not folder_exists`. `LAUNCH_GRACE_SECONDS` is **kept** as a thin
cold-start margin (the grace branch uses the same fallthrough chain).

### Transparency
1. **Always-on** — enrich the existing `VSCode` column with the winning rule:
   `Running (title)`, `Closed (no match)`. Zero new columns.
2. **On-demand** — `--explain` dumps the full `DetectionSignals` + transition per session.
3. **Persisted audit trail** — one **global** file, one **run-block** per command
   invocation (spanning all repos), **last 50 runs** (ring buffer), written **only**
   by `apply()` runs, using the atomic-rewrite discipline of `sessions.json`.

### Persistence
`VSCodeClaudeSession` gains `last_active: bool | None` and `last_active_rule:
str | None`, **backfilled to `None`** on read ("never observed under the new
system") — reuses the no-baseline branch new sessions already need; one-run blind
spot is harmless under the asymmetry principle.

## Out of scope (captured as follow-ups)
Finding #10 (`is_vscode_open_for_folder` return-type contract), #12 (launch-time
partial setup), the N-failed-runs escalation, and the "name the locking process"
feature — per the issue's Decisions table. Branch skip-reasons
(`!! No branch` / `!! Multi-branch`) stay local to restart (launch-time git I/O,
not session-state).

## Files created / modified

### Created
| Path | Purpose |
|------|---------|
| `src/mcp_coder/workflows/vscodeclaude/assessment.py` | Pure `assess_liveness`, `assess_session`, `IssueFacts`; orchestration `build_assessments`, `apply_assessments` |
| `src/mcp_coder/workflows/vscodeclaude/detection.py` | `DetectionSnapshot`, `capture_detection_snapshot`, `gather_signals` (Windows/IO boundary) |
| `src/mcp_coder/workflows/vscodeclaude/audit.py` | Audit-trail read/append/trim (global file, 50-run ring buffer) |
| `tests/workflows/vscodeclaude/test_assessment.py` | Rule-matrix + decision unit tests (no Windows) |
| `tests/workflows/vscodeclaude/test_detection.py` | Snapshot + `gather_signals` tests (mocked psutil/win32) |
| `tests/workflows/vscodeclaude/test_audit.py` | Audit ring-buffer / atomic-write tests |
| `pr_info/steps/summary.md` + `step_1.md` … `step_10.md` | This plan |

### Modified
| Path | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/types.py` | Enums `LivenessRule`, `SessionAction`; dataclasses `DetectionSignals`, `SessionAssessment`; `VSCodeClaudeSession` gains `last_active`, `last_active_rule` |
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | `load_sessions` backfill; `build_active_session_set` becomes a thin wrapper over `build_assessments` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Consume assessments; ordering fix; lock veto; `.to_be_deleted` loop consumes assessment |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Consume assessments (RESTART / REMOVE_MISSING / INVESTIGATE_ZOMBIE) |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Consume assessments; enriched `VSCode` column; write-free |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Export new symbols |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Build assessments once; call `apply_assessments` on launch; `--explain` rendering |
| vscodeclaude CLI argument parser | Add `--explain` flag |

## Step list
1. Types & persistence backfill
2. Liveness layer (`assess_liveness`) — pure
3. Issue-state + transition + decision (`assess_session`, `IssueFacts`) — pure
4. Detection snapshot + `gather_signals` (Windows/IO boundary)
5. `build_assessments` + `apply_assessments`; wire entrypoints (observe/apply split)
6. Cleanup migration (ordering fix, lock veto, retry-loop consumes assessment)
7. Restart migration (zombie / remove-missing)
8. Status migration (enriched column, write-free)
9. Audit trail + transition/decision logging
10. `--explain` flag

Each step = exactly one commit (tests + implementation + pylint/pytest/mypy green).
