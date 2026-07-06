# Plan Review Log — Issue #1031

## Round 1 — 2026-07-06
**Findings**: (1) import-linter claim false + new modules would be unconstrained; (2) run_format_code wrongly credited with removing unused imports; (3) glob/os wrongly listed as unused after Step 2.
**Decisions**: (1) ask-user → APPROVED Option A (add sub-layer beneath prompt_manager); (2) accept — use run_ruff_fix F401; (3) accept — correct parenthetical.
**User decisions**: Q: how to govern the two new modules in import-linter? A: Option A — add a sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` beneath `prompt_manager`.
**Changes**: summary.md/step_1.md/step_2.md corrected per findings 1-3; `.importlinter` sub-layer edit added as a Step 2 implementation task; `.importlinter` added to Modified-files lists.
**Status**: committed

## Round 2 — 2026-07-06
**Findings**: NEW — plan updated `.importlinter` but ignored `tach.toml`; undeclared new modules fold into root `mcp_coder`, creating a circular dependency with prompt_manager → `tach check` fails in both steps. (Round-1 fixes all re-verified correct.)
**Decisions**: accept (autonomous) — mechanical fix consistent with the already-approved decision to enforce the new modules architecturally; no design change.
**User decisions**: none (handled autonomously).
**Changes**: Added `tach.toml` handling to the plan — declare `prompt_parsing` (Step 1) and `prompt_sources` (Step 2) as domain modules and add both to `prompt_manager`'s depends_on; added `tach.toml` to Modified-files lists; documented the per-step sequencing vs the once-in-Step-2 `.importlinter` edit.
**Status**: committed

## Final Status

**Rounds run:** 3
**Outcome:** Plan approved-ready. No open findings.

- **Round 1** — 3 findings: (1) false claim that `prompt_manager` isn't in any import-linter contract + unenforced new modules → corrected the claim and added an `.importlinter` sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` beneath `prompt_manager` (user-approved Option A; deferred to Step 2); (2) `run_format_code` wrongly credited with removing unused imports → switched to `run_ruff_fix` F401; (3) `glob`/`os` wrongly listed as unused after Step 2 → corrected. Committed `a0d73e2`.
- **Round 2** — 1 new finding: plan updated `.importlinter` but ignored `tach.toml`; undeclared new modules fold into the root `mcp_coder` module → circular/undeclared dependency failing `tach check` in both steps. Fixed autonomously (consistent with the approved architecture-enforcement decision): declare `prompt_parsing` (Step 1) and `prompt_sources` (Step 2) as `domain` modules and add both to `prompt_manager`'s `depends_on`. Committed `9e969d8`.
- **Round 3** — clean. Only a cosmetic wording nuance (tach failure is primarily an undeclared-dependency violation, with the cycle coincident); no implementation-step impact; declined — no plan change. Loop terminated.

**Verdict:** The plan is internally consistent and ready for approval. Scope is a faithful "Move, Don't Change" refactor; both boundary tools (`.importlinter`, `tach.toml`) and the file-size/allowlist gates are handled per step.
