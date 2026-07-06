# Plan Review Log — Issue #1031

## Round 1 — 2026-07-06
**Findings**: (1) import-linter claim false + new modules would be unconstrained; (2) run_format_code wrongly credited with removing unused imports; (3) glob/os wrongly listed as unused after Step 2.
**Decisions**: (1) ask-user → APPROVED Option A (add sub-layer beneath prompt_manager); (2) accept — use run_ruff_fix F401; (3) accept — correct parenthetical.
**User decisions**: Q: how to govern the two new modules in import-linter? A: Option A — add a sub-layer `mcp_coder.prompt_sources | mcp_coder.prompt_parsing` beneath `prompt_manager`.
**Changes**: summary.md/step_1.md/step_2.md corrected per findings 1-3; `.importlinter` sub-layer edit added as a Step 2 implementation task; `.importlinter` added to Modified-files lists.
**Status**: committed
