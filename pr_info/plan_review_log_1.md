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


## Round 2 — 2026-05-01

**Findings**:
- Resolved-from-Round-1: All 9 Round 1 findings verified properly addressed (C1, C2, I1-I5, Q1-Q2).
- Improvement I6 — Wrong test name: plan referenced `test_get_active_session_count` (~line 277) but actual test is `test_get_active_session_count_with_mocked_pid_check` at line 224.
- Improvement I7 — Step 1 size: large but cohesive; splitting would re-introduce the C1 transient regression. Accept as-is.
- Improvement I8 — `__init__.py` modifications span steps 1 and 4; summary table acceptable in aggregate.
- Improvement I9 — Step 2 ordering verified safe (depends only on step 1).
- Improvement I10 — Invariant test in step 3 patches `mcp_coder.workflows.vscodeclaude.sessions.is_session_active` but consumers may use `from .sessions import is_session_active`, binding name into their own namespace. Test correctness relies on no module other than `sessions.py` referencing the symbol after step 3.
- Improvement I11 — Invariant + PID-refresh tests in step 3 may write to user's real `~/.mcp_coder/` because `update_session_pid` is not mocked.

**Decisions**:
- I6 → ACCEPT: fix test name everywhere it appears; update line reference to 224 or drop.
- I7 → SKIP: cohesion wins over size; no change.
- I8 → SKIP: minor; aggregate table is correct.
- I9 → SKIP: confirmed correct, no change.
- I10 → ACCEPT: add patching note to step 3 invariant test explaining the post-step-3 invariant and giving a debug recipe.
- I11 → ACCEPT: add explicit instruction to patch `get_sessions_file_path` or `update_session_pid` in tests to sandbox file writes.

**User decisions**: None — all autonomous-class (factual corrections + test-safety notes).

**Changes**:
- step_4.md: replaced `test_get_active_session_count` → `test_get_active_session_count_with_mocked_pid_check` (5 sites); line `~277` → `224`.
- summary.md: same test-name fix in Files-modified table.
- step_3.md: added "Patching note" explaining `from x import y` pitfall and post-step-3 invariant.
- step_3.md: added "File-write isolation" block instructing tests to patch `get_sessions_file_path` or `update_session_pid` to avoid writes to real home directory; covers both invariant test and PID-refresh test.

**Status**: Plan files updated; pending commit.


## Round 3 — 2026-05-01

**Findings**:
- Improvement R3-1 — Step 2 lists only `test_session_launch_process_issues.py` (claimed 7 sites). Actual scope: 9 sites across 4 files. In particular `test_session_restart.py::test_process_eligible_issues_respects_max_sessions` patches `get_active_session_count` to return 2 — once the function is no longer called the patch is a silent no-op and the test exercises a different code path.
- Skip — Redundancy of PID-refresh tests (helper-level + status integration). Both serve different purposes; per "test behavior, not implementation", keep both.
- Skip — `__init__.py` `__all__` removal correctly handled in step 4.
- Skip — Trivial line-number drift in step 1 (262-267 vs 264-267). Per planning_principles.md, ignore.

**Decisions**:
- R3-1 → ACCEPT: expand step 2 scope to all 4 test files; explain `monkeypatch.setattr → current_count=N` rewrite; call out max-sessions test explicitly.
- Other findings → SKIP per principles.

**User decisions**: None — autonomous-class factual scope correction.

**Changes**:
- step_2.md: WHERE block lists 4 test files; TDD block describes the rewrite pattern with explicit `monkeypatch.setattr` example and the canonical max-sessions case; Acceptance asserts no leftover patches; LLM Prompt updated.
- summary.md: Tests-modified table now lists all 4 files for step 2; max-sessions test called out explicitly.

**Status**: Plan files updated; pending commit.


## Round 4 — 2026-05-01

**Findings**: None.
**Decisions**: N/A.
**User decisions**: None.
**Changes**: None — plan is internally consistent, prior rounds' findings reflected, no actionable issues impeding implementing engineer.
**Status**: Loop exit signal received: "No changes recommended — plan is ready for approval."

## Final Status

- **Rounds run:** 4 (Rounds 1-3 produced plan changes; Round 4 produced none).
- **Plan structure:** 4 steps (down from initial 5 after Round 1 merger of old steps 1+2).
- **Commits produced (plan + log only — no source changes):**
  - Round 1: `0f4a561` — merge steps 1+2; `.get(folder, False)` lookups; drop redundant counter; move invariant test; INFO log; doc status side effect & intervention path
  - Round 2: `5f2f505` — fix wrong test name; add patching pitfall note; add file-write isolation note
  - Round 3: `e22b285` — expand step 2 scope to all 4 test files / 9 patch sites; document monkeypatch → current_count rewrite pattern
- **Compliance:** plan satisfies `planning_principles.md` (one step = one commit, no preparation steps, all checks green per step, no rollback) and `refactoring_principles.md` (clean deletion in step 4, no legacy artifacts, scoped steps).
- **Plan is ready for approval.**
