# Plan Review Log — Issue #1066 (Automated `mcp-coder rebase` command)

Supervisor-driven plan review. Base branch: `main` (branch up to date, no rebase needed).
Plan under review: `pr_info/steps/` (7 steps + summary).

---

## Round 1 — 2026-07-23

**Findings** (from engineer `/plan_review`):
- **C1 (Critical)** — Settings resource at `src/mcp_coder/resources/claude/settings/rebase_settings.json` is gitignored AND build-wiped (`setup.py` rmtree+copy of `resources/claude/`) → file never committed, destroyed at install, `find_data_file` raises at runtime. Summary's package-data claim is wrong for a hand-authored file.
- **C2 (Accept)** — Step 6 no-op short-circuit calls `needs_rebase(project_dir)` (auto-detects default) instead of the base resolved in Step 5 → wrong-branch check when default != resolved base.
- **D1 (Accept)** — Step 2 doesn't state the `## Automated Rebase` prompt body must be inside a fenced code block; `get_prompt` raises otherwise.
- **D2 (Accept)** — Step 6 `except (LLMTimeoutError, Exception)` redundant (LLMTimeoutError ⊂ Exception); pylint may warn.
- **R1 (Accept)** — Step 2 drift test reads the build-copied SKILL; note canonical SKILL is `.claude/skills/rebase/SKILL.md`, and reconcile the drift test against the (now-changed) lockfile row.
- **C3 / D3 / D4 (Skip)** — redundant idempotent fetch; step granularity sound; git_integration marker use correct.
- **Q3 (Skip)** — `pr_info/`-on-base → exit `2` accepted as consistent with the issue's pre-flight/"bad repo-state" category.
- Reuse/precedent audit: all claimed primitives and precedent files verified to exist as described.

**Decisions**:
- C2, D1, D2, R1 → **accept** (straightforward), apply via `/plan_update`.
- C3, D3, D4, Q3 → **skip** (per rationale above).
- C1 + the `uv lock` scope → **escalate to user** (architecture + requirements).

**User decisions**:
- **Topic 1 (settings location, resolves C1) → Option C**: settings become an in-code constant `REBASE_LLM_PERMISSIONS` in a new module `src/mcp_coder/workflows/rebase_permissions.py`, written to a temp settings file at runtime; no shipped resource. Comment references EPIC #1038 / sub-issue #1054 as the future refactor seam.
- **Topic 2 (lockfile / `uv lock` scope) → Option A (drop entirely)**: repo has NO tracked lockfile (`uv.lock` is gitignored, `git ls-files` for `*.lock` empty) → a rebase can never produce a lockfile conflict here, so `uv lock` regeneration + its permission grant are YAGNI. Remove them; lockfile conflicts fall under the general "unfamiliar conflict → abort with reason" rule. This is a deliberate, flagged deviation from the issue's approved lockfile Decision (premise invalid for this repo).

**Changes** (applied via `/plan_update`):
- `step_1.md` — settings resource → `REBASE_LLM_PERMISSIONS` constant in `src/mcp_coder/workflows/rebase_permissions.py`; unit test asserts git-write ops present, `push`+`uv lock` absent; comment links EPIC #1038/#1054.
- `step_2.md` — removed lockfile/`uv lock` regen from the prompt; drift-test reconciliation note; prompt body must be a fenced code block; canonical-vs-packaged SKILL-path note.
- `step_6.md` — `needs_rebase(project_dir, base)`; `except (LLMTimeoutError, Exception)` → `except Exception`.
- `step_7.md` — settings resolution materializes a runtime temp JSON file from the constant (via `tempfile`) instead of `find_data_file`; `--settings` override preserved.
- `summary.md` — Created list updated (constant+test in, JSON resource+test out); removed wrong package-data note; narrowed least-privilege to git-write ops; dropped lockfile from exit table + LLM-owns; added "Deviations from the issue" (Python-push, lockfile-dropped-YAGNI).
- `Decisions.md` — created; logs the six discussed decisions.

**Status**: committed (see commit for round 1)

---

## Round 2 — 2026-07-23

**Findings**: Re-review of the round-1 edits for internal consistency and new problems.
- Step 1 — `REBASE_LLM_PERMISSIONS` git-write ops present; `push` + `uv lock` asserted absent. ✔
- Step 7 — temp settings file materialized from the constant via `tempfile.NamedTemporaryFile(delete=False)`; no `find_data_file` for settings; `--settings` override preserved. Temp-file lifecycle correct (persists for the subprocess lifetime; `delete=False` is deliberate — a context-managed file would be deleted before `prompt_llm` reads it). ✔
- Step 2 — no `uv lock`/lockfile-regen; plain lockfile `--theirs` row kept so the drift test's `issubset` holds against SKILL.md's single lockfile row. ✔
- Step 6 — `needs_rebase(project_dir, base)` + `except Exception`. ✔
- summary.md — Created/Modified/Reused + Step-overview all agree; "Deviations from the issue" note present and accurate. ✔
- Reuse re-verified for edit-touched claims (`prompt_llm(settings_file=)`, `needs_rebase(project_dir, base)`, `fetch_remote`, `git_push`, `tempfile`, `resolve_claude_settings_path`) — all exist.

**Decisions**: No findings to act on. Redundant fetch (C3) unchanged — Skip, as in round 1.

**User decisions**: none needed.

**Changes**: none.

**Status**: no changes needed — plan is clean.

---

## Final Status

- **Rounds run**: 2.
- **Round 1**: 1 Critical (settings resource build-wiped) + 4 Accept fixes; 2 items escalated and decided by the user (settings → in-code constant; lockfile/`uv lock` scope dropped as YAGNI). Applied via `/plan_update`, committed `7f80e75`.
- **Round 2**: clean — no plan changes.
- **Outcome**: Plan is internally consistent, faithful to the (updated) Decisions, and **ready for approval**. Two deliberate, documented deviations from the issue: Python executes the force-push; lockfile/`uv lock` handling dropped (repo has no tracked lockfile).
