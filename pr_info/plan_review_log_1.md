# Plan Review Log — Issue #1025

Split large file `implement/core.py` + `test_core.py`.

Supervisor: technical lead delegating to engineer subagents (`/plan_review`, `/plan_update`) and a commit agent.

Base branch: `main` (branch up to date, no rebase needed). Run #1.

---

## Round 1 — 2026-07-06

**Findings** (from `/plan_review` engineer, all claims verified against real code):
- [STRAIGHTFORWARD] Un-listed consumer: `tests/integration/test_execution_dir_integration.py` (~L333) patches `core.<moved-name>` targets incl. `prepare_task_tracker`; marked `claude_cli_integration`/`execution_dir`, so skipped by the fast-unit gate. Summary wrongly called the CLI "the only external consumer."
- [verify-early] Strategy hinges on `move_symbol` adding a DIRECT import to `core.py` (`from .task_tracker_prep import prepare_task_tracker`) so `core.prepare_task_tracker` stays patchable. Qualified refs would break every `patch("...core.<name>")`. Checkable via the Step 3 dry-run.
- [NITPICK] Off-by-one: `core.py` drops under 750 after Step 3 (~654), not Step 4.
- [OK] `test_core_workflow.py` is the tightest new file (~717 vs 750) — watch after black/isort.
- [OK] Deliberate `_make_llm_response` duplication; one-PR/6-commit shape; empty TASK_TRACKER (pre-impl). No action.

**Decisions**:
- Accept findings 1, 2, 3 — all mechanical (plan hardening + factual corrections), none affect scope/architecture → no user escalation.
- Findings 4–7: informational, no change.

**User decisions**: none required this round (no design/requirements questions).

**Changes** (applied by engineer via MCP edits; `/plan_update` is `disable-model-invocation`):
- `summary.md`: "only external consumer" → "main external consumer" + note on the integration test's patch targets; step list corrected so `core.py` < 750 after Step 3, → ~500 after Step 4.
- `step_3.md`: added dry-run import-form confirmation (STOP if qualified refs) + integration patch-target check (`run_pytest_check(markers=["execution_dir"])`).
- `step_4.md`: corrected header/DoD wording (core.py already <750 after Step 3; this step → ~500).
- `step_6.md`: added integration-marker run to final verification gate.

**Status**: plan files changed → committed via commit agent; loop continues with a fresh review round.

## Round 2 — 2026-07-06

**Findings** (fresh review; round-1 fixes re-verified as correct & consistent):
- [STRAIGHTFORWARD] Steps 1, 2, 4 carry the same `move_symbol` direct-import dependency as Step 3 (retained orchestrator UNIT tests patch `core._handle_workflow_failure`/`_format_failure_comment`, `core._attempt_rebase_and_push`/`_get_rebase_target_branch`, `core.run_finalisation`) but lacked the dry-run guard. Steps 1-2 run before Step 3's guard → consistency/robustness gap.
- [STRAIGHTFORWARD] Step 5's rationale "keep `_make_llm_response` (still used by `TestRunImplementWorkflow`)" is factually wrong — that class (test_core.py L1130-1784) has zero references; helper becomes dead code (ruff won't strip a module-level fn; no vulture in gate).
- [NITPICK] Integration patch-target check (`execution_dir`/`claude_cli_integration`) can skip when Claude CLI is absent → green-because-skipped false assurance; real guard is the fast-gate unit tests patching the same `core.<name>` attrs.
- [OK] All round-1 fixes verified correct; line arithmetic, `__init__`/`__all__`, import-linter, naming/collisions (incl. `tests/workflows/test_utils.py` vs `tests/cli/test_utils.py` — package-qualified, no clash) all sound.

**Decisions**: accept all three (guard propagation, dead-helper removal, supplementary-check clarification) — mechanical, no scope/architecture impact → no user escalation.

**User decisions**: none required.

**Changes** (engineer, direct MCP edits; grounded by re-verifying `TestRunImplementWorkflow` has no helper ref):
- `step_1.md`/`step_2.md`/`step_4.md`: added the dry-run direct-import guard (STOP if qualified refs), adapted per step's moved symbols.
- `step_5.md`: now REMOVES dead `_make_llm_response` (+ its `Dict[str, Any]` import) from `test_core.py`; corrected rationale.
- `summary.md`: dropped `test_core.py` from the helper-copy list (kept for task_tracker_prep / finalisation / core_workflow).
- `step_3.md`/`step_6.md`: noted the integration check is supplementary/may-skip; unit tests are the primary guard.

**Status**: plan files changed → committed via commit agent; loop continues.

## Round 3 — 2026-07-06

**Findings** (convergence check; all round-2 edits re-verified against real source):
- [OK] `_make_llm_response` removal is clean — all 20 refs mapped; `TestRunImplementWorkflow` (the only class left in `test_core.py`) has zero refs, no dangling call site. `from typing import Any, Dict` line becomes fully unused after the moves → ruff strips it cleanly.
- [OK] Dry-run guards in Steps 1/2/4 coherent and load-bearing (100+ `core.<name>` patch sites across retained orchestrator tests).
- [OK] Class assignment complete & exclusive (17 classes, 1:1); step ordering sound; `__init__.py`/`__all__` repoint valid.
- [OK/NITPICK] Steps 1 & 2 guard wording names a companion function (`core._format_failure_comment`, `core._get_rebase_target_branch`) as "staying patchable on core" — imprecise (core only imports the fn it calls) but harmless: no test patches the former on `core`; the latter is patched only by `TestRebaseIntegration`, already retargeted to `rebase.` in Step 2. No action.
- [STRAIGHTFORWARD/self-correcting] Step 5's explicit import list for `test_core_workflow.py` omits `resolve_project_dir` (needed by moved `TestIntegration.test_resolve_project_dir_real_filesystem`) — covered by the governing "add needed imports" instruction and enforced by the pytest collection gate. No plan edit required.

**Decisions**: no plan changes this round. The two observations are minor and fully self-correcting via the per-step test/ruff gate; making further edits would be gold-plating. Accept reviewer verdict.

**User decisions**: none required.

**Changes**: none.

**Status**: zero plan changes → loop terminates.

---

## Final Status

- **Rounds run**: 3 (round 1 and round 2 each produced mechanical plan improvements; round 3 produced zero changes → converged).
- **Commits produced** (local branch `1025-split-large-file-implement-core-py-test-core-py`):
  - `fa7b558` — round 1: external-consumer note, move_symbol import check, core.py line-count timing.
  - `f72623b` — round 2: dry-run guards on Steps 1/2/4, dropped dead `_make_llm_response`, marked integration check supplementary.
  - (+ this review log commit)
- **User escalations**: none — all findings were mechanical (plan hardening + factual corrections); none affected scope or architecture.
- **Verdict**: **Plan is READY FOR APPROVAL / implementation.** The split is verified correct against the real source (symbol/class groupings, line arithmetic, naming-collision avoidance, `__init__`/`__all__` handling, import-linter no-change, allowlist removal). The "pure move" property holds. Remaining nitpicks are self-correcting via the mandatory per-step gate.
