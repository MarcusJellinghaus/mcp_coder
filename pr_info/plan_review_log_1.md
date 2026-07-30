# Plan Review Log — Issue #1068

Branch: `1068-branch-status-read-pr-review-feedback-via-dedup-onto-mcp-workspace-implementation`
Base: `main`
Plan: `pr_info/steps/` (Step 1–3 + summary.md)

Supervised automated plan review. Each round below records the engineer's review
findings, the supervisor's triage decisions, any user decisions, and the changes applied.

---

## Round 1 — 2026-07-30

**Findings** (from `/plan_review` engineer subagent):
- Prerequisite (mcp-workspace #244) independently verified at runtime — all required symbols resolve. No blocker.
- Step scoping correct — no step-split/merge needed. No critical issues.
- (1) [docs] Step 2 adds `--fail-on-reviews` and changes exit-code 2's meaning but doesn't update `docs/cli-reference.md` or the `execute_check_branch_status` docstring.
- (2) [other] `create_empty_report` re-exported but has zero consumers after the refactor — tension with "re-export only consumed names."
- (3) [missing-test] Step 3's `_run_reviewer` `pr_note` tests have no named home; `tests/workflows/review/test_reviewer.py` doesn't exist yet.
- (4) [correctness] Step 2 output-string safety + dropping `replace()` enrichment — verified safe against installed upstream. No change.
- (5) [design] Step 3 threads PR feedback via the **shared** review core → fires for both `review-plan` (pre-PR, no-op) and `review-implementation`. Gate to implementation lane?
- (6) [design] Per-round `collect_branch_status` not individually guarded → silent-drop on degraded fetch.

**Decisions**:
- (1) **Accept** — add docs + docstring update to Step 2.
- (2) **Accept (keep + clarify)** — issue's Decisions table explicitly lists `create_empty_report` in the re-export surface; the specific instruction wins. Keep it; add a one-line note in Step 1 explaining it's retained per the specified surface.
- (3) **Accept** — name `tests/workflows/review/test_reviewer.py` in Step 3; `ci_note` backfill optional (avoid scope creep).
- (4) **Skip** — verified safe, no change.
- (6) **Skip** — silent fail-open matches issue's "feedback fetch failure must never fail the report" decision + KISS.

**User decisions**:
- (5) User chose **B** — gate PR-feedback threading to the **implementation lane only** via a `ReviewConfig` flag (aligned with the existing `run_after_steps` / `inject_base_branch` split). Plan-review lane skips the `collect_branch_status` call entirely.

**Changes**: applying via `/plan_update` (findings 1, 2, 3, 5B). See engineer report below.

**Changes applied** (via `/plan_update` engineer):
- `step_1.md` — retention note for `create_empty_report` (finding 2).
- `step_2.md` — docs tasks: `docs/cli-reference.md` (`--fail-on-reviews` option + exit-code-2 "reviews undeterminable" meaning) + `execute_check_branch_status` docstring (finding 1).
- `step_3.md` — rewritten: new `ReviewConfig.thread_pr_feedback` bool (`True` for `REVIEW_IMPLEMENTATION`, `False` for `REVIEW_PLAN`); per-round `collect_branch_status` + both feed targets gated behind it; named test files `test_reviewer.py` / `test_config.py` / `test_core.py` / `test_core_after_steps.py`; `ci_note` backfill optional (findings 5B, 3).
- `summary.md` — design point 5 + modified-file lists + Steps list updated for consistency.
- `Decisions.md` — new; logs the four review decisions.

**Status**: committed (see commit below). Plan files changed → loop continues with a fresh review round.
