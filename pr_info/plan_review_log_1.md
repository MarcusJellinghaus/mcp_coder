# Plan Review Log — Issue #1072 (Automated review workflows)

Supervisor-driven automated plan review. Base branch: `main` (branch up to date, no rebase needed).
Plan: 9 steps in `pr_info/steps/`, nothing implemented yet (TASK_TRACKER empty).

---

## Round 1 — 2026-07-22

**Findings** (from `/plan_review` engineer):
- Coverage is strong; all major scope items map to steps. Under-specification, not omissions:
  - Step 1: A-B-A prototype asserts token recall but not the issue-mandated "strictly sequential (never concurrent)" execution.
  - Step 1: `create_plan` context-loss finding home — engineer worried `pr_info/` deletion loses it.
  - Step 8: rebase-needed → the issue mandates needs-human/error "never success", but the plan only wired CI as a gate; unresolved rebase silently proceeds.
  - Step 4: confirm reviewer prompt enforces `file:line` + severity contract (sole reviewer→supervisor interface, not machine-parsed).
- Step design: all 9 steps conform (one commit each, TDD, checks-green boundaries, no prep/verify steps). Step 7/8 is a horizontal cut through one `core.py` function — defensible, each lands green.
- Anchors: all spot-checked anchors HOLD (`check_and_fix_ci`/`CIFixConfig` + `session_dir_name`, `commit_changes`/`_attempt_rebase_and_push`/`detect_base_branch`, `handle_workflow_failure` taking plain string category, `update_workflow_label` needing `IssueManager` + `update_issue_labels` gate, config schema `coordinator.repos.*`, `labels.json` shape + adjacency rule, `get_prompt`/`PROMPTS_FILE_PATH`, `create_plan/core.py:303` reuse-original-id, `.importlinter` layering). No broken anchors.
- KISS divergences both SOUND: (a) one shared review engine + `ReviewConfig` (eliminates the drift risk the issue warns about); (b) failure labels as a config dict (`handle_workflow_failure` already consumes category as a plain string). Both explicitly reversible.

**Decisions** (supervisor triage):
- Accept (in-step polish, no re-plan): Step 1 strict-sequencing assertion; Step 4 report-contract enforcement; Step 7 name `IssueManager`+`update_issue_labels` gating; Step 7 use a local reason→category map (no cross-workflow import).
- Skip: KISS divergences (a)/(b) — sound, no action. Step 7/8 horizontal split — noted, each lands green, not worth restructuring.
- Escalate to user (design/scope): rebase-conflict routing; `create_plan` finding home; plan-lane auto-edit of plan files.

**User decisions** (via `/discuss`, one at a time):
- **Rebase conflict → needs-human (`07:code-review`)**, never success. Automatic conflict-resolving rebase is issue **#1066**'s deliverable (not yet implemented); Step 8 gets a rebase-status check with a `NotYetImplemented` marker referencing #1066, and the needs-human (07) fallback until #1066 lands. A comment recording this consumer/integration point was posted to #1066.
- **`create_plan` finding home → leave it** (test docstring + `pr_info/` review log). User corrected the premise: `pr_info/` is deleted only at the very end, and the escalate→human handoff reads the review log, so the finding reaches a human. Non-gap; no plan change.
- **Plan lane auto-edits plan files → YES (Option A).** Faithful mirror of interactive `/plan_review_supervisor`, which already applies `/plan_update` for straightforward improvements and only escalates design/scope. `tasks` → reviewer edits `pr_info/steps/*` via MCP; `escalate` → `04`; `dismiss` → success (`05`).

**Changes** (applied via engineer, direct `edit_file` — `/plan_update` is `disable-model-invocation`):
- `step_1.md`: added the strict-sequential (never-concurrent) assertion + prompt.
- `step_4.md`: reviewer prompt must enforce `file:line` + severity report contract (finding lacking it is invalid).
- `step_7.md`: (a) named `IssueManager(project_dir)` + `update_issue_labels` gating on label updates; (b) local reason→category map, no `implement` import; (c) documented `review-plan` `tasks`-verdict editing `pr_info/steps/*` (mirror `/plan_update`), `escalate`→`04`, `dismiss`→`05`.
- `step_8.md`: rebase gate — unresolved conflict → needs-human (`07`), never success/never `17f-*`; `NotYetImplemented` marker referencing #1066 at the future auto-rebase slot. Flagged for the implementer: Step 7's loop must special-case the `"rebase"` reason like `escalate` (exit 0), not `_fail`.
- Posted comment on #1066 (integration point / needs-human fallback).

**Status**: plan changed → committed; loop continues with a fresh review round.

---

## Round 2 — 2026-07-22

**Findings** (from fresh `/plan_review` engineer, verifying Round 1 edits + re-scan):
- Verification: all 5 Round 1 edits landed cleanly and consistently — Step 1 strict-sequential assertion, Step 4 report contract, Step 7 (a) IssueManager+`update_issue_labels` gating / (b) local reason→category map / (c) `review-plan` plan-edit semantics, Step 8 rebase gate + #1066 marker.
- **F1 (CRITICAL, mechanical):** Step 7's ALGORITHM routed *any* non-None `_after_steps` reason to `_fail` (→ `handle_workflow_failure`, exit 1, `17f-*`), contradicting Step 8's mandate that a `"rebase"` reason is a needs-human handoff (`07:code-review`, exit 0, never a failure label). The Round 1 note landed in Step 8 prose but was never encoded into Step 7's ALGORITHM + LLM prompt.
- Coherence checks that PASS: escalate-label routing (`04`/`07`), label-id consistency (`code_review_ci`→`status-17f-ci`), IssueManager/gating vs the 3-way table, `_after_steps` signature. No other regressions; step granularity / TDD / label-adjacency / config-define-only scope all still conform.
- No new design/requirements questions.

**Decisions** (supervisor triage): F1 is a mechanical inconsistency, not a design question — the routing decision (rebase → needs-human `07`) was already settled in Round 1. Accepted and fixed autonomously; no user escalation.

**User decisions**: none this round.

**Changes** (applied via engineer, direct `edit_file`):
- `step_7.md`: special-case `reason == "rebase"` at BOTH `_after_steps` call sites (dismiss + tasks branches) — `write_round_log(escalate_reason="rebase")` + `update_workflow_label(from=busy, to=escalate)` = `07`, `return 0`, before the generic `if reason: return _fail(...)`. Updated the Step 7 LLM prompt to name the `"rebase"`→escalate special case. Non-`"rebase"` reasons still fall through to `_fail`.

**Status**: plan changed → committed; loop continues with a fresh review round.

---

## Round 3 — 2026-07-22

**Findings** (from fresh `/plan_review` engineer, verifying the F1 fix + whole-plan re-scan):
- F1 fix LANDED CLEANLY: Step 7 special-cases `reason == "rebase"` at both `_after_steps` call sites (dismiss + tasks), routing to the escalate lane (`07`, exit 0) before the generic `_fail`; the Step 7 LLM prompt names the special case.
- Non-`"rebase"` reasons (`ci`/`timeout`/`mcp`/`general`) still fall through to `_fail`/`handle_workflow_failure` — real CI/timeout/MCP failures are not swallowed.
- `write_round_log(escalate_reason="rebase")` matches the Step 6 signature and mirrors the `escalate`-verdict log path; coherent with the 3-way table and Step 8. No gap in the tasks-branch early-return (still writes an escalate log; backstop/`pending_ci_note` bookkeeping not bypassed).
- Whole-plan re-scan: no remaining inconsistency, coverage gap, or step-design issue. All #1072 scope items map to steps 1–9; conforms to `planning_principles.md`.

**Decisions** (supervisor triage): nothing to accept or escalate — zero findings.

**User decisions**: none.

**Changes**: none.

**Status**: no changes needed — review loop terminates.

---

## Final Status

**Result: plan is READY FOR APPROVAL.**

- Rounds run: **3** (Round 1 applied Round-1 edits + user decisions; Round 2 fixed the F1 Step7↔Step8 rebase-routing inconsistency; Round 3 verified, zero changes → convergence).
- Plan commits produced on branch `1072-automated-review-workflows-...`:
  - `0c0c2b2` — Round 1 plan edits (steps 1, 4, 7, 8).
  - `f2ca837` — Round 2 F1 fix (step 7 `"rebase"` → escalate lane).
  - (this log committed separately.)
- User design decisions (Round 1, via `/discuss`): rebase-conflict → needs-human `07` (auto conflict-resolving rebase deferred to #1066, marker + #1066 comment posted); `create_plan` finding stays in test docstring + `pr_info` log (no separate issue); `review-plan` auto-edits `pr_info/steps/*` (Option A, mirrors interactive `/plan_review_supervisor`).
- External: integration-point comment posted to issue **#1066**.
- Anchors: all issue `file:line` anchors spot-checked and hold. KISS divergences (shared review engine; failure-label config dict) reviewed and accepted as sound + reversible.

The plan is internally consistent, covers #1072's scope, and conforms to the planning principles. Ready for the user to `/plan_approve`.
