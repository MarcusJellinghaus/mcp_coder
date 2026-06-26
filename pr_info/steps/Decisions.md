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
1. **Step 5 green-state ordering:** after building `assessments`, keep feeding the old-shape
   `active_set = {f: a.verdict.active for f, a in assessments.items()}` to not-yet-migrated
   consumers so the build stays green. Steps 6/7/8 each flip ONE consumer's signature AND its
   `commands.py` call site together (one consumer per commit).
2. **Step 6 retry-loop no-assessment fallback:** `.to_be_deleted` is keyed by folder *name*,
   assessments by folder *path*. Map name→path under `workspace_base`. Fallback: no tracked
   session but folder still exists (locked) → retry delete (today's behaviour); folder gone →
   drop the entry. A live folder reconciled via assessment is spared.
3. **Step 5 `prior_last_active` wiring:** `build_assessments` reads `session["last_active"]`
   and passes it into `assess_session`/`assess_transition`.
4. **#629 re-eval:** added as a post-fix PR verification checkpoint note (not a step).
5. **`within_grace`:** computed as a plain bool in `gather_signals` (Step 4); `types.py` stays
   dependency-free (no import from `sessions`). `directory_empty` likewise a plain bool there.
