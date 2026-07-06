# Plan Review Log — Issue #90 (run 1)

**Issue:** CLI help: single-source from parsers (centralized categories) + DRY shared flags
**Branch:** 90-cli-help-single-source-from-parsers-centralized-categories-dry-shared-flags
**Base:** main
**Plan state at start:** 3 steps (step_1..3) + summary.md; TASK_TRACKER empty (nothing implemented yet).

**Supervisor note:** The plan's `summary.md` intentionally departs from two settled
Decisions in the issue (register-time capture wrapper; relocate `create_parser()` to
`cli/parser_factory.py`), substituting a shared `COMMAND_DESCRIPTIONS` dict design that
it argues meets the same requirements with less machinery. Flagged for review + user
confirmation.

---

## Round 1 — 2026-07-06
**Findings** (from `/plan_review`):
- Design deviation from 2 settled issue Decisions (shared dict vs register-time capture; keep `create_parser()` in main.py vs relocate). Reviewer verified no import cycle and all requirements preserved; endorsed but recommended owner sign-off.
- F1 (blocker-for-Step-3): Step 3's claim that `help=SUPPRESS` subparsers are absent from `choices`/`_choices_actions` is empirically false; the suppressed `help` leaf would be collected and break the anti-drift test.
- F2 (design/quality): module-level `parsers.py → commands.help` import couples the lightweight parser layer to the heavy `commands` package. Recommended the plan's own fallback: a dependency-free `cli/command_catalog.py`.
- F3 (nit): "mirrors set_status precedent" overstated (function-local vs module-level import).
- F4 (nit/straightforward): `test_help.py` rewrite must cover four NamedTuple-referencing tests, not two.
- F5 (nit): anti-drift render check is substring-based; optional exact-row hardening.
- F6: step granularity/sequencing good — no action.

**Decisions**:
- Design deviation → **escalated to user**.
- F2 → **escalated to user** (tightly coupled to design).
- F1 → accept (straightforward fix).
- F4 → accept (clarify scope).
- F3 → accept (fold into F2 fix).
- F5 → skip (optional hardening, not required).

**User decisions**:
- Q1 "Design mechanism" → **Approve simpler design** (keep shared dict + `create_parser()` in main.py).
- Q2 "Catalog location" → **New dependency-free `cli/command_catalog.py`** (F2 recommendation).

**Changes** (applied via engineer / plan edits):
1. Relocated `COMMAND_DESCRIPTIONS` + `COMMAND_CATEGORIES` to new dependency-free `src/mcp_coder/cli/command_catalog.py`; `help.py` + both parser modules import from it. Updated summary.md (Files created, Dependency-direction note rewritten, set_status precedent argument dropped) and step_2.md.
2. Fixed Step 3: `collect_leaves` must explicitly skip `help=SUPPRESS` leaves; corrected the false rationale.
3. Step 2 now enumerates all four `test_help.py` rewrites (`test_command_categories_contains_all_commands`, `test_help_text_has_all_commands`, `test_help_text_no_category_descriptions`, `test_help_text_command_column_alignment`).
4. Removed the obsolete "mirrors set_status precedent" justification.
- Files changed: `pr_info/steps/summary.md`, `pr_info/steps/step_2.md`, `pr_info/steps/step_3.md` (step_1.md unchanged — shared-flags only).

**Status**: plan changed → committing; a fresh review round follows.

---

## Round 2 — 2026-07-06
**Findings** (fresh `/plan_review` of the revised plan):
- All three Round-1 changes confirmed landed correctly and consistently:
  1. Catalog constants in dependency-free `command_catalog.py`; `help.py` + both parsers import from it; no leftover "constants live in help.py" text; `set_status` precedent argument gone; module named consistently; in summary's Files-created.
  2. Step 3 anti-drift test explicitly skips `help=SUPPRESS` leaves with corrected rationale (verified against CPython argparse source: `_ChoicesPseudoAction.dest = name`, suppressed leaf appears as `"==SUPPRESS=="`).
  3. Step 2 enumerates all four `test_help.py` rewrites — matches the four NamedTuple-referencing tests actually in the file.
- Cross-checks: all 19 canonical descriptions + `*(changed)*` markers match current source; `COMMAND_CATEGORIES` totals 19; Step 1 `--llm-method` guard lists the correct 8 parsers.
- Two nits, no action required: latent edge case if a future leaf lacks `help=` (caught by existing assertion); `str | None` return type is fine given the SUPPRESS/`help=`-present invariant.

**Decisions**: nits skipped (no action). No design/requirements questions.
**User decisions**: none this round.
**Changes**: none — plan is clean.
**Status**: no changes needed → loop terminates.

---

## Final Status
- **Rounds run:** 2.
- **Round 1:** one design escalation (2 settled-Decision overrides) + F1 blocker + F2/F4 — all resolved. User approved the simpler shared-dict design and the dependency-free `command_catalog.py`. Plan updated and committed (`1e5a985`).
- **Round 2:** zero plan changes; revisions verified clean and consistent with the current code.
- **Commits produced:** `1e5a985` (plan updates + this log).
- **Verdict:** Plan is internally consistent, matches the current codebase, preserves all issue #90 requirements, and is **ready for approval / implementation**. Nothing implemented yet (TASK_TRACKER empty) — this was plan review only.
