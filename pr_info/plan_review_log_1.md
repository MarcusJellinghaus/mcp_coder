# Plan Review Log — Issue #872

**Issue:** vscodeclaude: redundant is_session_active calls in launch and status
**Branch:** 872-vscodeclaude-redundant-is-session-active-calls-in-launch-and-status
**Started:** 2026-05-01


## Round 1 — 2026-05-01

**Findings**:
- Critical C1 — Step 1 leaves a transient regression: `restart_closed_sessions` clears caches and re-calls `is_session_active` after the snapshot is built (double-scan until step 2 lands).
- Critical C2 — `active_set[session["folder"]]` raises KeyError if cleanup removed a session before downstream code iterates the store.
- Improvement I1 — Redundant `current_count += 1` inside `process_eligible_issues` inner loop (dead after `available_slots` slice caps `issues_to_start`).
- Improvement I2 — `build_active_session_set` calls `is_vscode_open_for_folder` after `is_session_active` may have already done so on the cmdline path (double scan).
- Improvement I3 — Cross-flow invariant test gated behind step 5 (deletion); regressions in steps 2-3 not caught until then.
- Improvement I4 — Framing log "Checking N session(s)…" planned at OUTPUT level mismatches per-session INFO logs.
- Improvement I5 — `vscodeclaude status` now mutates sessions.json on window-title detection — intentional but undocumented.
- Question Q1 — Should `restart_closed_sessions` accept the snapshot session list to avoid drift from internal `load_sessions()`?
- Question Q2 — `_handle_intervention_mode` bypasses snapshot; should be documented.

**Decisions**:
- C1 → ACCEPT option B: merge old steps 1 and 2 into a single step (snapshot + cleanup + restart all threaded together). Eliminates transient regression; mock churn happens once per file. Step count drops 5 → 4.
- C2 → ACCEPT option A: use `active_set.get(folder, False)` everywhere for snapshot lookups. Simplest, semantically correct (removed sessions = inactive).
- I1 → ACCEPT: drop dead `current_count += 1` in the same step as the threading change. Boy Scout cleanup.
- I2 → ACCEPT option B: keep PID-refresh centralized in `build_active_session_set` per issue's stated requirement; second `is_vscode_open_for_folder` call hits the populated process cache (cheap). No code change needed.
- I3 → ACCEPT: move invariant test into the status-display step (now step 3) so it asserts `call_count == N_sessions` for both launch and status after both are converted. Step 4 becomes deletion-only.
- I4 → ACCEPT: use INFO level for the framing log line — matches existing per-session INFO logs.
- I5 → ACCEPT: document status side effect in summary.md and step 3; add explicit test asserting `update_session_pid` is called when stored PID is stale.
- Q1 → RESOLVED by C2-A: `.get(folder, False)` makes session-list drift safe; no need to thread session list separately.
- Q2 → ACCEPT: add one-line note in summary.md that intervention path bypasses snapshot.

**User decisions**: None — all findings handled autonomously per skill (step splitting/merging, missing test relocation, formatting/log-level/doc notes are explicitly autonomous-class; design notes align with issue's stated requirements).

**Changes**:
- Merged old `step_1.md` + `step_2.md` into new `step_1.md` (snapshot helper + cleanup threading + restart_closed_sessions threading in one commit).
- Renamed old `step_3.md` → `step_2.md`, old `step_4.md` → `step_3.md`, old `step_5.md` → `step_4.md`.
- step 1: framing log set to INFO (not OUTPUT); `.get(folder, False)` lookup pattern.
- step 2: dropped redundant `current_count += 1`; `.get(folder, False)` lookup.
- step 3: cross-flow invariant test moved here; status side effect documented; new test asserting `update_session_pid` called on stale PID.
- step 4: deletion-only — drops `get_active_session_count` and removes the old `test_get_active_session_count` test.
- summary.md: 4-step structure; `.get(folder, False)` rationale; status side-effect note; intervention-path note.

**Status**: Plan files updated; pending commit.
