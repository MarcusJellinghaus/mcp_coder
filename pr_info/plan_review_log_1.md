# Plan Review Log — Issue #609

## Round 1 — 2026-03-27

**Findings**:
1. **(Critical) Step 1 — Existing tests will break**: `test_vscodeclaude_session_type_structure` asserts exact field set and `test_vscodeclaude_session_creation` creates a session dict without `from_github`. Both must be updated when adding the new field.
2. **(Critical) Step 1 — Required vs NotRequired TypedDict field**: Plan adds `from_github: bool` as required but also says "consumers must use `session.get("from_github", False)`". A required field contradicts `.get()` with default. Old session JSON files won't have this key. Must use `NotRequired[bool]` for backward compat.
3. **(Accept) Step 3 — Injection point clarity**: Plan's pseudocode for appending github install to `venv_section` is correct in principle but should reference the exact insertion point (after `VENV_SECTION_WINDOWS.format(...)`, before template `.format()` calls). Should confirm it applies to both normal and intervention scripts.
4. **(Accept) Step 6 — Missing TOML validation test**: Step 6 says "no tests needed" but a minimal test parsing `pyproject.toml` and asserting the `from-github` section structure would catch syntax errors.

**Decisions**:
- Finding 1: **Accept** — straightforward, add existing test updates to Step 1
- Finding 2: **Accept** — use `NotRequired[bool]` instead of `bool`, update Step 1 plan
- Finding 3: **Accept** — clarify injection point in Step 3, confirm both script types get github overrides
- Finding 4: **Accept** — add minimal TOML parse test to Step 6

**User decisions**: None needed — all findings are straightforward improvements.

**Changes**:
- `pr_info/steps/step_1.md`: Use `NotRequired[bool]`, add existing test updates, update LLM prompt
- `pr_info/steps/step_3.md`: Clarify injection point, confirm both script types get github overrides
- `pr_info/steps/step_6.md`: Add TOML validation test, update LLM prompt
- `pr_info/steps/summary.md`: Update type reference to `NotRequired[bool]`

**Status**: Committed

## Round 2 — 2026-03-27
**Findings**: None — second review pass confirmed all round-1 fixes are correctly applied and consistent.
**Decisions**: N/A
**User decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Round 3 — 2026-03-27 (user feedback)
**Findings**: User rejected `NotRequired[bool]` — wants clean code, no backward compat hacks.
**Decisions**: Revert to `from_github: bool` (required). Update all session dict creation sites instead.
**User decisions**: "No backward compatibility — focus on clean code."
**Changes**:
- `step_1.md`: Reverted to `bool`, added `session_restart.py` + 8 test files to update list
- `step_4.md`: Changed `session.get()` to direct `session["from_github"]` access
- `summary.md`: Updated type and session persistence description

**Status**: Committed

## Final Status
- **Rounds**: 3 (2 with changes, 1 verification)
- **Plan status**: Ready for approval
