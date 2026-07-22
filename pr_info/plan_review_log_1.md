# Plan Review Log — Issue #1071 (Workflow-step library refactor)

Run: 1
Started: 2026-07-22
Supervisor: technical lead (automated)

Plan under review: `pr_info/steps/step_1.md` … `step_6.md` + `summary.md`
Base branch: main (branch up to date — no rebase needed)
Implementation status: not started (TASK_TRACKER empty)

---

## Round 1 — 2026-07-22

**Findings** (from `/plan_review` engineer subagent):
- B1 (blocker): Plan missed a production consumer — `cli/commands/check_branch_status.py:32` imports `check_and_fix_ci` from `implement.ci_operations`. Step 4's "shim or removed" would break this CLI import → RED.
- B2 (blocker): Step 3 moved `tests/workflows/implement/test_rebase.py` wholesale, dragging `TestRebaseIntegration` (an `implement/core` orchestration test) into `tests/workflow_steps/` — violates "tests mirror source structure."
- I1: Step 2 framed the `task_processing.py` self-import of the moved commit/push/run_formatters funcs as reactive, but it's a mandatory production edit for `process_single_task`.
- I2: Step 4 constant list omits `PR_INFO_DIR` (already relocated in Step 2) — could read as missing.
- I3: Shared `check_git_clean` narrows create_pr's all-exceptions catch to `ValueError`.
- Validated as correct: dual-enforcer edits (import-linter + tach), dependency-constrained ordering (commit/push → rebase → CI), 9+3 constant relocation, `finalisation.py:73` doubled-path quirk preserved, CI signature parameterization byte-identical, `is_branch_not_base` custom-base semantics.

**Decisions**: Accepted all five (B1, B2, I1, I2, I3). None affect scope/architecture — all align with the issue's explicit decisions (production call sites import moved symbols directly; reactive-shim-only for patch targets; tests mirror source). No user escalation needed.

**User decisions**: None required this round.

**Changes**: Engineer applied via `/plan_update`:
- step_2.md — I1 (mandatory self-import stated as production edit)
- step_3.md — B2 (test_rebase split; orchestration test stays in implement; patch → `implement.core._attempt_rebase_and_push`; rebase.py removed if no patch target remains)
- step_4.md — B1 (CLI consumer repointed to `workflow_steps.ci`; shim reactive-only) + I2 (PR_INFO_DIR note)
- step_5.md — I3 (exception-scope-delta note)
- summary.md — propagated B1/B2/I1
- Decisions.md — created; logged the five triaged decisions

**Status**: plan changed — pending commit; loop continues (fresh review round required).

## Round 2 — 2026-07-22

**Findings** (fresh `/plan_review` engineer, verified against actual source/tests):
- B2-followup (blocker): The round-1 B2 fix was materially wrong. `tests/workflows/implement/test_rebase.py::TestRebaseIntegration` actually has **5** methods, all patching `implement.rebase.*` internals (`push_changes`, `rebase_onto_branch`, `_get_rebase_target_branch`) and asserting on the real `_attempt_rebase_and_push` body (e.g. `force_with_lease=True`, never-block-on-failure). Round 1's instruction to keep them under `implement/` and repoint to `core._attempt_rebase_and_push` would (a) leave dangling patch targets once `implement/rebase.py` is removed, and (b) replace the function under test with a mock, destroying the assertions.
- B1/I1/I2/I3: re-verified as correctly and consistently applied. No new issues introduced by round 1. CI test move (Step 4) confirmed clean (no entangled orchestration tests). No other unaccounted production consumers of moved symbols.

**Decisions**: Accept the B2 correction (source-verified, no scope/architecture impact — no user escalation). Move all 5 `TestRebaseIntegration` tests to `tests/workflow_steps/test_rebase.py`, repoint to `workflow_steps.rebase.*`, do NOT patch `_attempt_rebase_and_push` wholesale; core-level orchestration coverage already exists separately in `test_core_workflow.py`/`test_failure_reporting.py` (unchanged). `implement/rebase.py` removal now follows as a consequence.

**User decisions**: None required this round.

**Changes**: Engineer updated `step_3.md`, `Decisions.md` (§2), and `summary.md` consistently (WHERE block, TDD, LLM prompt, decision text, moved-tests bullet); fixed the 5-methods test-count wording throughout.

**Status**: plan changed — pending commit; loop continues (fresh review round required).
