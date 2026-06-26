# Plan Review Log — Issue #985

Rebuild vscodeclaude session-state around an explicit `SessionAssessment` model.

Supervisor: technical lead (delegating review + plan edits to engineer subagents).
Started: 2026-06-26

---

## Round 1 — 2026-06-26

**Findings** (engineer review, cross-checked against source):
- Plan accurately diagnoses current code (zombie unreachable, double PID write, workspace-file unlinked first at `cleanup.py:229-236`, retry loop cmdline-only at `cleanup.py:317`).
- All issue requirements covered (observe/apply split, 5 consumers migrate, title-miss fallthrough, 3-cache snapshot, zombie reachability, cleanup ordering + lock veto, write-free status, 50-run audit ring, `last_active` backfill).
- **Gap (safety):** pure `assess_session` only special-cased `Dirty` before DELETE → would emit destructive DELETE on a stale non-empty `No Git`/`Error` folder, violating asymmetry principle.
- **Ordering bug:** Step 5 swapped `active_set`→`assessments` in `commands.py` while consumers still expected `active_set` → broke "each step green".
- Minor: retry-loop no-assessment fallback undefined; `prior_last_active` wiring unspecified; `#629` re-eval uncaptured; `within_grace` could stay a plain bool to keep `types.py` dependency-free.

**Decisions**:
- *accept (straightforward):* Step 5 green-state shim; retry-loop fallback (locked→retry, gone→drop); `prior_last_active` wiring; `#629` re-eval note; `within_grace` plain bool.
- *escalated to user:* (1) type model — KISS collapse vs explicit layered; (2) where the git-status→action decision lives.

**User decisions**:
- After discussing pros/cons, user chose the **explicit layered model** (frozen typed sub-results `LivenessVerdict`/`IssueState`/`Transition`/`Decision` from per-layer pure functions, embedded in a frozen `SessionAssessment`, enums for rule/action, single `to_audit_record`/`to_explain` serializer) — reversing the KISS collapse. Rationale: the module's failure mode is implicit/re-derived/destructive state, so explicitness + inspectability are worth the extra types.
- git-status → action decision lives in the **pure `decide` layer**, with `git_status` + `directory_empty` promoted into injected inputs; "DELETE requires Clean-or-empty" enforced in one place with a typed-invariant test.

**Changes**: summary.md rewritten (explicit layered model, updated pipeline + file tables); step_1 (frozen typed sub-results + enums + serializer, `within_grace`/`directory_empty` bools, dependency-free types); step_2 (`assess_liveness`→frozen verdict); step_3 (layered `assess_issue_state`/`assess_transition`/`decide` with full safety matrix + invariant test + composer); step_4 (`directory_empty`/`within_grace` at IO boundary); step_5 (green-state shim, `prior_last_active`, one-consumer-per-commit); step_6 (retry-loop mapping + fallback); step_7/8 (consumer field access, status retires `active_set`); step_9 (single serializer for audit); step_10 (`--explain` via `to_explain()`); new Decisions.md.

**Status**: plan changed — pending commit; loop continues (fresh review next round).
