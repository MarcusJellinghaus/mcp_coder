# Decisions — issue #985 plan

Decisions taken with the tech lead and applied to the plan in `pr_info/steps/`.

## Decision 1 — Explicit layered assessment model (reverses the earlier KISS collapse)
The earlier plan collapsed the issue's model into `DetectionSignals` + `IssueFacts`
(inputs) + one flat `SessionAssessment` (output) + a single staged `assess_session()`.
The tech lead **reversed** that: because this module's failure mode (#38) was implicit,
re-derived, destructive state, maximum explicitness/inspectability is worth the extra
types. Go with the explicit layered model:
- Frozen inputs `DetectionSignals` (IO/Windows boundary, captured once) + `IssueFacts`.
- Pure, individually unit-testable layer functions, each returning an immutable typed value:
  `assess_liveness -> LivenessVerdict`, `assess_issue_state -> IssueState`,
  `assess_transition -> Transition`, `decide -> Decision`.
- `assess_session(...)` composes them and returns a frozen `SessionAssessment` that
  **embeds** the four typed sub-results (not a flattened bag of fields).
- All assessment dataclasses are **frozen** so `apply()` cannot mutate an assessment.
- Enums for `rule` (`LivenessRule`) and `action` (`SessionAction`); `destructive` is an
  explicit bool — no stringly-typed verdicts.
- A **single** serializer on `SessionAssessment` (`to_audit_record()` / `to_explain()`)
  feeds all three transparency surfaces (audit trail, `--explain`, VSCode column) so they
  cannot drift.
- Typed-invariant unit test: no `Decision` with `destructive=True` unless
  `git_status == "Clean"` OR `directory_empty is True`.
- Work distribution: Step 1 (types/enums + serializer signature), Step 2 (`assess_liveness`),
  Step 3 (`assess_issue_state` + `assess_transition` + `decide` + `assess_session`
  composition + serializer + invariant test).

## Decision 2 — git-status → action decision lives in the pure `decide` layer
The earlier plan only special-cased `git_status == "Dirty"` before falling through to
DELETE, which would destroy a stale **non-empty** `No Git`/`Error` folder on weak evidence
(asymmetry violation). Fix:
- Promote `git_status` (string) and `directory_empty` (bool) into the injected inputs so
  `decide(...)` stays PURE and owns the full safety matrix, mirroring today's
  `cleanup_stale_sessions`: `Clean → DELETE`, `Missing → REMOVE_MISSING`, `Dirty → SKIP`,
  `No Git`/`Error` → DELETE only if `directory_empty` else `SKIP` (with reason), plus the
  zombie / keep-active / restart actions.
- "DELETE requires `git_status == "Clean"` OR `directory_empty`" is enforced in this one
  place and covered by the invariant test.
- `directory_empty` is gathered in the IO boundary (Step 4 `gather_signals`), NOT computed
  inside the pure function.

## Straightforward improvements (tech lead pre-approved)
1. **Step 5b green-state ordering:** after building `assessments`, keep feeding the old-shape
   `active_set = {f: a.verdict.active for f, a in assessments.items()}` to not-yet-migrated
   consumers so the build stays green. Steps 6/7/8 each flip ONE consumer's signature AND its
   `commands.py` call site together (one consumer per commit).
2. **Step 6 retry-loop no-assessment fallback:** `.to_be_deleted` is keyed by folder *name*,
   assessments by folder *path*. Map name→path under `workspace_base`. Fallback: no tracked
   session but folder still exists (locked) → retry delete (today's behaviour); folder gone →
   drop the entry. A live folder reconciled via assessment is spared.
3. **Step 5b `prior_last_active` wiring:** `build_assessments` reads `session["last_active"]`
   and passes it into `assess_session`/`assess_transition`.
4. **#629 re-eval:** added as a post-fix PR verification checkpoint note (not a step).
5. **`within_grace`:** computed as a plain bool in `gather_signals` (Step 4); `types.py` stays
   dependency-free (no import from `sessions`). `directory_empty` likewise a plain bool there.

## Plan corrections (tech-lead approved) — applied to the step files

These are mechanical plan-text fixes; no new design decisions.

### Correction 1 — Step 3 `decide` zombie/remove-missing tested in-signature
The locked signature is `decide(verdict, issue_state, transition, git_status,
directory_empty)` — it receives neither `signals` nor `folder_exists`, and an active
session's rule is TITLE/PID/CMDLINE (never `NO_ARTIFACTS`). So distinguishing
`INVESTIGATE_ZOMBIE` via `signals.folder_exists` / `verdict.rule == NO_ARTIFACTS`
cannot work. Fix: test folder-gone in-signature as `git_status == "Missing"` (the
pipeline sets `git_status` to `"Missing"` exactly when the folder is absent,
`status.py:332`). `INVESTIGATE_ZOMBIE = verdict.active and git_status == "Missing"`;
`REMOVE_MISSING = not verdict.active and git_status == "Missing"`. Removed the
`folder_exists`/`NO_ARTIFACTS` references (would break the agreed signature and the
destructive-invariant test) and made the zombie/remove-missing unit tests use
`git_status == "Missing"` consistently.

### Correction 2 — Step 5 split into Step 5 + Step 5b; `_issue_facts` short-circuit note
Step 5 was the heaviest step. Split into two one-commit sub-steps (steps 6-10 NOT
renumbered): Step 5 = `IssueFacts` production via a `_issue_facts` helper replicating
the ~80-line eligibility logic of `get_stale_sessions` (`cleanup.py:99-180`, incl. the
individual-issue API fallback and assignment check) + `assess_issue_state` wiring;
Step 5b = `build_assessments`/`apply_assessments` orchestration + the read-only
`build_active_session_set` wrapper + the two `commands.py` call sites + the green-state
`active_set` shim + `prior_last_active` wiring. `_issue_facts` MUST preserve the current
short-circuit: compute `is_session_stale` only when the session is not
closed/blocked/unassigned/ineligible (mirrors `cleanup.py:174-180`), to avoid the
spurious staleness warning the current code guards against.

### Correction 3 — Step 8 keeps the `build_active_session_set` wrapper
Step 8 previously implied retiring `build_active_session_set`, but it is used by
`test_sessions.py::test_build_active_session_set`, `test_active_set_invariant.py`,
`test_cleanup.py:2568`, `test_status_display.py:1880`, plus two `commands.py` call
sites. Resolution: KEEP the thin read-only wrapper (defined in the Step 5b migration).
Only the green-state `active_set` shim is retired at Step 8; status consumes
assessments via the embedded sub-results while the wrapper remains available for
backward compat. This avoids churning four test files.
