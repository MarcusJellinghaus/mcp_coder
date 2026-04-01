# Plan Review Log — Run 1

**Issue:** #672 — Replace Bash tool scripts with MCP equivalents in skills and settings
**Date:** 2026-04-01
**Reviewer:** Supervisor agent

## Round 1 — 2026-04-01
**Findings:**
- Steps 1+2 tightly coupled, should merge (settings + skills are intertwined)
- Tool mapping table: engineer suggested different placement for new tools
- `get_library_source` flagged as scope creep (but explicitly in issue scope)
- implement_direct missing allowed-tools is pre-existing
- ALLOWED list clarity — existing blanket MCP instruction suffices
- Step 5 test decoupling flagged as unnecessary (but explicitly in issue scope)
- Step 4 docs updates flagged for trimming (but issue explicitly lists all 4 files)

**Decisions:**
- Accept: Merge Steps 1+2 into single step
- Ask user: CLAUDE.md tool mapping table approach → User decided: no new rows in tool mapping table. Tools placed in natural sections (commit instructions, code quality, refactoring row). `get_library_source` is code analysis, goes in refactoring row.
- Ask user: Step 4 docs scope → User decided: keep all 4 files (option A)
- Skip: Findings 3-6 (in scope per issue or pre-existing)

**User decisions:**
- Q1: Tool mapping table → No new "NEVER USE" rows. Claude wouldn't naturally run these scripts. Place tools where they belong.
- Q2: Docs scope → Keep all 4 files as planned.

**Changes:** Merged steps 5→4, updated step 2 (CLAUDE.md) approach, updated summary.
**Status:** committed (pending)

## Round 2 — 2026-04-01
**Findings:**
- (Critical) Step 2 must update "ALL THREE" → "ALL FIVE" and add descriptive bullets for new quality tools
- Step 2: clarify "Before ANY commit" code block format (keep wrapper)
- Step 1: LLM prompt for implement_direct step 6 needs explicit bash→plain-text instruction
- Step 3: LLM prompt should note to adapt if section names differ
- Step 4: pytest exclusion missing `not textual_integration`
- Step 4: LLM prompt should say "don't rename test methods"

**Decisions:** All accept — straightforward improvements, no user escalation needed.
**Changes:** Applied all 6 fixes to steps 1, 2, 3, 4.
**Status:** committed (pending)

## Round 3 — 2026-04-01
**Findings:**
- Step 4 ALGORITHM missing `test_error_fallback_with_outside_output` method
- Step 4 verification too narrow — should also check plain `vulture` references

**Decisions:** Both accept — straightforward fixes.
**Changes:** Applied both fixes to step 4.
**Status:** committed (pending)

## Round 4 — 2026-04-01
**Findings:** None — all previous fixes verified correct.
**Status:** No changes needed.

## Round 5 — 2026-04-01 (post-rebase)
**Findings:**
- After rebase onto main, a prior PR already completed all of step 1 (settings + skills) and most of step 2 (CLAUDE.md tool mapping, commit sections, quick examples)
- Plan restructured from 4→3 steps to reflect current state

**Decisions:** Accept — plan updated to remove completed work, renumber steps.
**Changes:** Deleted old step 1, renumbered remaining steps, trimmed step 1 (CLAUDE.md) to only remaining work, updated summary with "Already Completed" section.
**Status:** committed (pending)

## Round 6 — 2026-04-01
**Findings:** None — updated plan verified accurate against current codebase.
**Status:** No changes needed.

## Final Status

**Rounds run:** 6 (4 with changes, 2 clean)
**Plan ready:** Yes — 3 steps, all consistent with post-rebase state, LLM prompts actionable, verification criteria testable.
**User decisions recorded:** 2 (tool mapping approach, docs scope)
