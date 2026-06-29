# Implementation Review Log — Issue #985

Rebuild vscodeclaude session-state around an explicit assessment model.

Supervised review of the implementation diff against issue requirements, the
design decisions in `pr_info/steps/`, and the project knowledge base.

---

## Round 1 — 2026-06-29

**Findings** (from `/implementation_review`):
1. **Critical** — `apply_assessments` built the audit run-block from the reloaded post-cleanup `sessions.json`, so the destructive `delete`/`remove_missing` records (already persisted out of the store by `remove_session` during cleanup/restart) never reached the 50-run audit trail — defeating the PR's headline "make destructive decisions inspectable" goal. A mocked orchestration test masked it.
2. `decide()` carries an unused `transition` parameter (used only for logging elsewhere).
3. `status.display_status_table` recomputes git status with a second subprocess per session — `build_assessments` already computed it for `decide` but didn't store it (TOCTOU gap vs. the "same snapshot" determinism guarantee).
4. Possibly-vestigial exported helpers (`build_active_session_set`, `get_next_action`, `check_folder_dirty`).

**Decisions**:
- #1 **Accept** — headline observability defect; bounded fix.
- #2 **Skip** — `decide` signature is explicitly locked in `Decisions.md`/`summary.md`; the param documents the decision inputs; removal churns every layer test for zero behavioral gain.
- #3 **Accept** — more than cosmetic: reopens a TOCTOU gap on a decision input against a stated invariant.
- #4 **Skip** — `build_active_session_set` is mandated to stay (Decisions.md Correction 3); the others are test-coupled. Defer genuine dead-code adjudication to the `run_vulture_check` step.

**Changes**:
- #1 — `apply_assessments` now sources the audit run-block from the build-time `assessments` map (threading the original sessions list for repo/issue/status), while PID-refresh / `last_active` still iterate the live surviving store. Rewrote the masking test to exercise the real cleanup-then-apply order and assert the deleted session's record survives into the trail.
- #3 — added `git_status` field to frozen `SessionAssessment`, populated in `assess_session` from the value already passed to `decide`; `display_status_table` reads it instead of recomputing.
- Files: `types.py`, `assessment.py`, `status.py`, `commands.py`, `test_assessment_orchestration.py`.
- Checks: pylint / mypy(strict) / ruff clean; pytest 721 passed, 2 skipped.

**Status**: changes made — committing.

## Round 2 — 2026-06-29

**Findings** (follow-up review of commit `8f232ca`):
- Both Round-1 fixes verified correct: the audit run-block now genuinely includes destructive `delete`/`remove_missing` records for cleanup-removed sessions (test no longer masked; PID/`last_active` mutation still survivor-only); the new `apply_assessments` signature is consistently passed at the real call site with no missing-folder edge case; the new `git_status` field is frozen-correct, populated only via `assess_session`, read by status; `status` remains write-free.
- Minor observation: `git_status` (a `decide()` input) was omitted from the `_flatten` serializer, so it didn't surface in the audit trail / `--explain` for DELETE/KEEP_ACTIVE/RESTART records — a small gap against the branch's "fully reconstruct the destructive decision" goal.

**Decisions**:
- **Accept** the serializer observation — trivial, free now that the field exists, and directly serves the headline inspectability goal.

**Changes**:
- Added `git_status` to `SessionAssessment._flatten` (flows into `to_audit_record`) and to `to_explain`. `types.py` only; existing serializer tests use membership assertions so none needed updating.
- Checks: pylint / mypy clean; pytest 721 passed, 2 skipped.

**Status**: changes made — committing.

## Round 3 — 2026-06-29

**Findings**: Confirmation sweep of commits `8f232ca` + `b2ffcaf`. No remaining correctness issues, broken invariants, type errors, or dead code. The `git_status` serializer addition reaches `to_audit_record`/`--explain` and breaks no tests; the audit-source/PID-mutation split and the new `apply_assessments` signature are consistently wired at the single real call site.

**Decisions**: nothing to act on.

**Changes**: none.

**Status**: no changes needed — review loop complete.

---

## Final Status

**Rounds run:** 3 (Round 3 produced zero code changes → loop complete).

**Accepted findings implemented:**
1. Critical — audit run-block now sourced from the build-time `assessments` map so cleanup-deleted destructive `delete`/`remove_missing` records survive into the persisted 50-run audit trail (masking test rewritten). Commit `8f232ca`.
2. `git_status` carried on the frozen `SessionAssessment` and read by `status` (closes the TOCTOU gap vs. the same-snapshot determinism guarantee). Commit `8f232ca`.
3. `git_status` surfaced in the shared `_flatten` serializer → reaches the audit trail (`to_audit_record`) and `--explain` (`to_explain`) for every action. Commit `b2ffcaf`.

**Skipped findings:** unused `transition` param in `decide()` (signature locked by `Decisions.md`); vestigial-helper note (`build_active_session_set` mandated to stay; others deferred to vulture).

**Architectural checks (run by supervisor):**
- `lint-imports`: PASSED — 19 contracts kept, 0 broken.
- `vulture` (min-confidence 60): clean after whitelisting genuine false positives (new `VSCodeClaudeSession` TypedDict fields + `@patch`/lambda signature params). Commit `56b740f`.

**Quality:** pylint / mypy(strict) / ruff clean; pytest 721 passed, 2 skipped (vscodeclaude + coordinator unit suites) across all rounds.

**Commits produced this review:** `8f232ca`, `b2ffcaf`, `56b740f` (+ this log).
