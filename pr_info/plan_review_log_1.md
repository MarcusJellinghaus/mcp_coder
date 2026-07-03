# Plan Review Log — Issue #695

**Issue:** refactor(vscodeclaude): replace bat/sh orchestration templates with thin launcher + Python session_setup
**Branch:** 695-refactor-vscodeclaude-replace-bat-sh-orchestration-templates-with-thin-launcher-python-session-setup
**Base:** main (branch up to date, no rebase needed)
**Plan status at start:** 6 step files + summary; TASK_TRACKER empty (nothing implemented yet — full plan review)

---

## Round 1 — 2026-07-03

**Findings** (from `/plan_review` engineer):
1. [BLOCKER] Step 5 omits `test_workspace.py` from its port/trim list — two content-asserting tests (`test_create_startup_script_windows`, `test_create_startup_script_intervention`) break under the thin launcher.
2. [design-verify] Shared env dict feeds `VIRTUAL_ENV` + not-yet-existent project bin into the `install.py` call — behavioral change from today.
3. [nit] Banner-title 58-char truncation + shell-escaping dropped.
4. [improvement] No test that UTF-8 stdout is forced before banner prints.
5. [nit] Middle-step `WARNING ... Continuing` message silently dropped.
6. [improvement] `ci.yml` drift-guard comment references a constant Step 6 deletes.
7. [info] Step 5 is largest/riskiest — correctly not splittable.
8. [improvement] No end-to-end round-trip test for `skip_github_install` through the on-disk spec.
9. [nit] summary.md mis-states call sites (both in `session_launch.py`, not `session_restart.py`).

**Overall assessment:** Fundamentally sound; no structural rework. Only #1 is a true blocker (mechanical).

**Decisions:** Accepted and applied #1, #3, #4, #5, #6, #7(note-only), #8, #9 autonomously. Escalated #2.

**User decisions:**
- #2 (install.py env): Verified against `tools/install.py` — it forwards env untouched; `uv pip install`/pip commands pin `--python <abs venv python>` (immune); only `uv sync` (our `--use-sync` path) is env-sensitive and targets `<cwd>/.venv`. Option A ("clean env") would leak the coordinator's `VIRTUAL_ENV` → uv mismatch warning. **Decision: Option B — single shared env with `VIRTUAL_ENV=<cwd>/.venv`** (correct for both uv and pip; invariant `VIRTUAL_ENV == <cwd>/.venv == target`). Add env test + rationale note.

**Changes:** step_2 (env rationale + banner-title note), step_3 (middle-step warning parity + UTF-8-before-banner test + install.py VIRTUAL_ENV env test), step_5 (`test_workspace.py` port + e2e `skip_github_install` round-trip test), step_6 (`ci.yml` drift-guard comment update), summary.md (call-site wording), Decisions.md (created).

**Status:** committed — 1fb56b4

---

## Round 2 — 2026-07-03

**Findings** (from `/plan_review` engineer; Round-1 fixes verified correctly integrated):
1. [improvement/parity] Intervention terminal WARNING banner is dropped, and step_5/Decisions.md rationale falsely claims it's "rendered at runtime by session_setup.py" — no step rendered it.
2. [nit] `commands` validation moved from conditional (non-intervention only) to unconditional — minor unflagged fail-fast behavior delta.
3. [nit] `render_banner` test list lacks an intervention-case assertion (subsumed by #1).

**Overall assessment:** Fundamentally sound; no structural rework. Approve conditional on resolving #1.

**Decisions:** Escalated #1 (parity + feature-scope). #2/#3 folded into #1 fix.

**User decisions:**
- Explained intervention mode (manual no-automation debug session forced open on a bot-busy issue via `--intervene --issue N`; warns human in-terminal that automation may run concurrently). Clarified two warning surfaces: coordinator-console banner + status-file `Mode: INTERVENTION` are NOT dropped by the refactor; only the in-terminal startup-script banner is.
- **Decision: RESTORE the in-terminal intervention warning** (behavior parity, cheap, collision-safety cue in the working terminal). Render at runtime via `session_setup.render_banner`, reusing a kept `INTERVENTION_WARNING` template constant.

**Changes:** step_2 (`render_banner` appends `INTERVENTION_WARNING` for intervention specs + test), step_3 (`run_session` prints it before bare claude + flow test asserts warning present/absent), step_4 (add `INTERVENTION_WARNING` constant, additive), step_5 (correct intervention rationale + Finding-2 unconditional-validation note), step_6 (keep `INTERVENTION_WARNING`, note deletion doesn't drop warning), summary.md (banner/flow-shapes/templates bullets), Decisions.md (corrected wording + 3 Round-2 entries).

**Status:** committed — 4d011ad

---

## Round 3 — 2026-07-03

**Findings** (from `/plan_review` engineer; all prior fixes verified integrated):
1. [BLOCKER, mechanical] Step-ordering defect introduced by Round 2: `INTERVENTION_WARNING` constant added in Step 4 but consumed by `render_banner` (Step 2) + `run_session` (Step 3) → Steps 2/3 would land red (ImportError), violating one-green-commit-per-step.

**Overall assessment:** Substantively complete and consistent; only the ordering defect blocks readiness. Purely mechanical, no human decision.

**Decisions:** Accepted and applied autonomously (option a): move `INTERVENTION_WARNING` to Step 2, its first consumer (kept in `templates.py`).

**Changes:** step_2 (introduce `INTERVENTION_WARNING` in templates.py + test; WHERE now includes templates.py/test_templates.py), step_4 (remove the constant; keeps launcher constants; note it's now in Step 2), step_6 (Keep-list annotation Step 4→Step 2), summary.md (step overview), Decisions.md (placement note + ordering-defect decision entry).

**Status:** committed — 435066f

---

## Round 4 — 2026-07-03

**Findings** (from `/plan_review` engineer):
- Round-3 ordering fix verified fully consistent across step_2/step_4/step_6/summary.md/Decisions.md — no contradictory reference remains. All 6 steps confirmed independently-green commits.
1. [nit, mechanical] summary.md prose said "delete the 12 orchestration constants" — actual is 14 (Step 6 enumerates 14; glob collapsed two `INTERACTIVE_*` families).

**Overall assessment:** Ready for approval — only a cosmetic count nit.

**Decisions:** Fixed the count nit autonomously (12 → 14) for doc accuracy.

**Changes:** summary.md (orchestration-constant count 12 → 14).

**Status:** committed — 7ee2434

---

## Round 5 — 2026-07-03 (final confirmation)

**Findings:** None. Verified against source: 14 orchestration constants match Step 6's deletion list; all "keep" constants exist; `INTERVENTION_WARNING` placement consistent (Step 2 first consumer); Step 5 pivot targets (`_escape_batch_title`, `session_folder_path`) present in `workspace.py`. All settled items coherent and not re-litigated.

**Overall assessment:** Ready for approval/implementation.

**Changes:** None — zero plan changes this round → review loop terminates.

**Status:** no changes needed.

---

## Final Status

- **Rounds run:** 5 (Rounds 1–4 produced plan changes; Round 5 clean → loop terminated).
- **Commits produced:** `1fb56b4` (R1), `4d011ad` (R2), `435066f` (R3), `7ee2434` (R4) + this log commit.
- **Blockers found & resolved:** 2 mechanical blockers (R1: `test_workspace.py` omitted from Step 5 test list; R3: `INTERVENTION_WARNING` consumed before created). Both fixed.
- **Design decisions escalated to user:** (1) install.py env → **Option B** (single shared env, `VIRTUAL_ENV=<cwd>/.venv`; verified safe for both uv & pip); (2) intervention in-terminal warning → **restore** for parity.
- **Verdict:** Plan is internally consistent, each step is an independently-green commit (additive → pivot → delete), and it faithfully honors the issue's constraints. **Ready for approval.**

