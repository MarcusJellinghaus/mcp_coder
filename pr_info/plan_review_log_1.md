# Plan Review Log — Run 1

**Issue**: #553 — mcp-coder verify: show contextual install instructions for active provider
**Date**: 2026-03-24

## Round 1 — 2026-03-24
**Findings**:
- [CRITICAL] Step 3 doesn't list existing tests that need updating when `verify_claude()` is no longer called for langchain provider (`test_all_sections_printed`, `test_claude_informational_when_langchain_active`, `test_exit_1_when_active_provider_fails`)
- [CRITICAL] Step 3 missing exact import path for `find_claude_executable`
- [CRITICAL] Step 1 doesn't clarify that "no backend configured" case should NOT get an `install_hint`
- [IMPROVEMENT] Step 2/3 — Claude URL hint only appears inline, not in pip summary block; should be explicit
- [IMPROVEMENT] Step 3 — `_collect_install_hints` only tested indirectly; add direct unit tests
- [IMPROVEMENT] Step 3 — `test_no_install_hint_when_ok` tests impossible scenario (YAGNI)
- [SKIP] Parameterized tests suggestion — nice but not necessary, implementer can decide
- [SKIP] Summary `_LABEL_MAP` comment — already correct

**Decisions**:
- All critical and improvement findings: accepted and applied (straightforward, bounded effort)
- Parameterized tests: skipped (implementer discretion)

**User decisions**: None needed — all findings were straightforward improvements

**Changes**:
- `pr_info/steps/step_1.md` — added edge case note for `backend_pkg=None`
- `pr_info/steps/step_2.md` — added note that URL hint is inline-only
- `pr_info/steps/step_3.md` — added exact import path, existing tests to update section, `TestCollectInstallHints` class, removed YAGNI defensive test, added summary block filtering note

**Status**: Committed (d05a737)

## Round 2 — 2026-03-24
**Findings**: All Round 1 fixes verified. No remaining issues found.
- Edge case note in Step 1 matches actual code behavior for `backend_pkg=None`
- Import path in Step 3 is correct and follows existing conventions
- All 3 existing tests listed for update confirmed to exist and will need adjustment
- Summary.md remains consistent with individual steps

**Decisions**: No changes needed
**Changes**: None
**Status**: No changes needed

## Final Status
- **Rounds**: 2 (1 with changes, 1 verification)
- **Commits**: 1 (`d05a737` — plan fixes)
- **Plan status**: Ready for approval
