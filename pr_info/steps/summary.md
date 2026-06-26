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

### Explicit layered assessment model
This module's failure mode (#38) was implicit, re-derived, destructive state, so
we maximise **explicitness and inspectability**: the assessment is built as a chain
of small **pure functions**, each producing an **immutable typed value**, aggregated
into a frozen `SessionAssessment` that **embeds** its typed sub-results (it is not a
flattened bag of fields). Every assessment dataclass is **frozen**, so `apply()`
cannot mutate an assessment after it is computed.

| Concern | Type / function |
|---------|-----------------|
| Inputs (frozen) | `DetectionSignals` (IO/Windows boundary, captured once) + `IssueFacts` (injected issue data) |
| Liveness layer | `assess_liveness(signals) -> LivenessVerdict` (`active: bool`, `rule: LivenessRule`) |
| Issue-state layer | `assess_issue_state(issue_facts) -> IssueState` (open/stale/blocked/unassigned/eligible) |
| Transition layer | `assess_transition(prior_last_active, verdict) -> Transition` (active→inactive flip flag) |
| Decision layer | `decide(verdict, issue_state, transition, git_status, directory_empty) -> Decision` (`action: SessionAction`, `reason: str`, `destructive: bool`) |
| Composition | `assess_session(...)` composes the layers, returns frozen `SessionAssessment` embedding `LivenessVerdict`/`IssueState`/`Transition`/`Decision` |
| Serializer | **one** `SessionAssessment.to_audit_record()` / `to_explain()` — the single source feeding all three transparency surfaces |
| Audit | one `audit.py` module reusing the `sessions.json` write discipline |

Each layer function is individually unit-testable with injected inputs (no Windows).
Verdicts use **enums** (`LivenessRule`, `SessionAction`) and an explicit `destructive`
bool — no stringly-typed verdicts. The single serializer guarantees the persisted
audit trail, `--explain`, and the enriched VSCode column **cannot drift**. A typed
invariant test enforces: no `Decision` with `destructive=True` unless
`git_status == "Clean"` or `directory_empty` is True.

### The pipeline

```
capture_detection_snapshot()   # detection.py — ALL 3 caches captured at one instant (fixes R4 age-skew)
        │
        ▼
gather_signals(session, snapshot) -> DetectionSignals     # detection.py — the ONLY Windows/IO boundary
        │  (also gathers directory_empty + within_grace as plain bools)
        ▼
assess_session(signals, issue_facts, git_status, directory_empty, prior_last_active) -> SessionAssessment
        │      # assessment.py — PURE; composes the layered chain:
        │      #   assess_liveness -> LivenessVerdict
        │      #   assess_issue_state -> IssueState
        │      #   assess_transition -> Transition
        │      #   decide(verdict, issue_state, transition, git_status, directory_empty) -> Decision
        │      # → frozen SessionAssessment embedding all four typed sub-results
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
- **R1** — closed/stale/blocked/unassigned/ineligible (`assess_issue_state`) and the
  next action (`decide`) are computed **once** inside `assess_session`; cleanup and
  status read the same `SessionAssessment`, so they cannot disagree on the same snapshot.
- **Git-status safety matrix (pure `decide`)** — `git_status` (string) and
  `directory_empty` (bool) are injected inputs so `decide(...)` stays PURE and owns the
  **full** safety matrix, mirroring today's `cleanup_stale_sessions`:
  `Clean → DELETE`, `Missing → REMOVE_MISSING`, `Dirty → SKIP`,
  `No Git`/`Error` → DELETE **only if** `directory_empty` else `SKIP` (with reason),
  plus the zombie / keep-active / restart actions. This closes the bug where a stale
  **non-empty** `No Git`/`Error` folder fell through to a destructive DELETE on weak
  evidence (asymmetry violation). The rule "DELETE requires `git_status == "Clean"`
  OR `directory_empty`" is enforced in this one place and covered by the invariant test.
  `directory_empty` is gathered in the IO boundary (Step 4 `gather_signals`), **not**
  computed inside the pure function.
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
All three surfaces are fed by the **one** `SessionAssessment` serializer
(`to_audit_record()` / `to_explain()`) so they cannot drift:
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
| `src/mcp_coder/workflows/vscodeclaude/assessment.py` | Pure layer fns `assess_liveness`, `assess_issue_state`, `assess_transition`, `decide`; composer `assess_session`; `IssueFacts`; orchestration `build_assessments`, `apply_assessments` |
| `src/mcp_coder/workflows/vscodeclaude/detection.py` | `DetectionSnapshot`, `capture_detection_snapshot`, `gather_signals` (Windows/IO boundary) |
| `src/mcp_coder/workflows/vscodeclaude/audit.py` | Audit-trail read/append/trim (global file, 50-run ring buffer) |
| `tests/workflows/vscodeclaude/test_assessment.py` | Rule-matrix + decision unit tests (no Windows) |
| `tests/workflows/vscodeclaude/test_detection.py` | Snapshot + `gather_signals` tests (mocked psutil/win32) |
| `tests/workflows/vscodeclaude/test_audit.py` | Audit ring-buffer / atomic-write tests |
| `pr_info/steps/summary.md` + `step_1.md` … `step_10.md` | This plan |

### Modified
| Path | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/types.py` | Enums `LivenessRule`, `SessionAction`; frozen dataclasses `DetectionSignals`, `LivenessVerdict`, `IssueState`, `Transition`, `Decision`, `SessionAssessment` (embeds the four typed sub-results + `to_audit_record`/`to_explain` serializer); `VSCodeClaudeSession` gains `last_active`, `last_active_rule` |
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | `load_sessions` backfill; `build_active_session_set` becomes a thin wrapper over `build_assessments` |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | Consume assessments; ordering fix; lock veto; `.to_be_deleted` loop consumes assessment |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Consume assessments (RESTART / REMOVE_MISSING / INVESTIGATE_ZOMBIE) |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | Consume assessments; enriched `VSCode` column; write-free |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Export new symbols |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Build assessments once; call `apply_assessments` on launch; `--explain` rendering |
| vscodeclaude CLI argument parser | Add `--explain` flag |

## Step list
1. Types & persistence backfill (enums + frozen `LivenessVerdict`/`IssueState`/`Transition`/`Decision`/`SessionAssessment` + serializer)
2. Liveness layer (`assess_liveness -> LivenessVerdict`) — pure
3. Issue-state + transition + decision + composition (`assess_issue_state`, `assess_transition`, `decide`, `assess_session`, `IssueFacts`, serializer, invariant test) — pure
4. Detection snapshot + `gather_signals` (Windows/IO boundary; gathers `directory_empty` + `within_grace`)
5. `build_assessments` + `apply_assessments`; wire entrypoints (observe/apply split)
6. Cleanup migration (ordering fix, lock veto, retry-loop consumes assessment)
7. Restart migration (zombie / remove-missing)
8. Status migration (enriched column, write-free)
9. Audit trail + transition/decision logging
10. `--explain` flag

Each step = exactly one commit (tests + implementation + pylint/pytest/mypy green).
**Green-state ordering (Steps 5–8):** Step 5 keeps feeding the old-shape `active_set`
(`{f: a.verdict.active for f, a in assessments.items()}`) to not-yet-migrated
consumers so the build stays green; Steps 6/7/8 each flip exactly **one** consumer's
signature **and** its `commands.py` call site together (one consumer per commit).

## Post-fix verification checkpoint (not a step)
After the PR lands, **re-evaluate #629** against the rebuilt model to confirm it is
resolved or to scope any remaining work.
