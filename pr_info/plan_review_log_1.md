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

**Status:** committed (see commit agent)

---
