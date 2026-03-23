# Plan Review Log — Run 1

**Issue:** #547 — VSCode session detection: PID check short-circuits reliable window title check
**Branch:** 547-vscode-session-detection-pid-check-short-circuits-reliable-window-title-check
**Date:** 2026-03-23

## Round 1 — 2026-03-23
**Findings**:
- Critical: `is_session_active` not imported in test file, but step_1.md claims it is
- Critical: `VSCodeClaudeSession` TypedDict has `repo: str` but Test 2 uses `repo=None` — mypy would fail
- Improvement: Test 3 (warning log) is identical setup to Test 1 — should merge
- Improvement: `issue_number=None` edge case not tested (parallel guard to `repo=None`)
- Minor: TASK_TRACKER has no checkboxes (populated by tooling)
- Minor: Step count (2) is appropriate

**Decisions**:
- Fix import claim in step_1.md (straightforward)
- Merge Test 1 + Test 3 into single test (straightforward)
- Parameterize Test 2 for both `repo=None` and `issue_number=None` (straightforward)
- Update TypedDict `repo: str` → `repo: str | None` (asked user — chose option A)
- Skip: mock assertion for `is_vscode_open_for_folder` not called (speculative)

**User decisions**:
- Q: How to handle `repo` type mismatch? A: Option A — update TypedDict to `str | None`
- Q: Merge Test 1 and Test 3? A: Option A — merge
- Q: Add `issue_number=None` test? A: Option B — parameterize Test 2

**Changes**:
- `pr_info/steps/step_1.md`: Fixed import note, merged Tests 1+3, parameterized Test 2, renumbered to 3 tests
- `pr_info/steps/step_2.md`: Added TypedDict update sub-step, updated LLM prompt
- `pr_info/steps/summary.md`: Added `types.py` to files table, updated test count

**Status**: committed

## Round 2 — 2026-03-23
**Findings**:
- Critical: Changing `repo: str` → `str | None` in TypedDict causes ripple effects in 10+ call sites (status.py, session_restart.py, cleanup.py, session_launch.py)
- Critical: `issue_number: int` in TypedDict also can't be set to `None` in tests without same problem

**Decisions**:
- Revert TypedDict change entirely — don't touch `types.py`
- Tests that need `None` for `repo`/`issue_number` omit the key from dict, use plain dict (`.get()` returns `None`)
- Production code already uses `.get()` so no changes needed there

**User decisions**:
- Q: Revert TypedDict change? A: Yes — go with simplest approach

**Changes**:
- `pr_info/steps/step_1.md`: Test 2 now omits keys instead of setting `None`, uses plain dict
- `pr_info/steps/step_2.md`: Removed TypedDict sub-step, renumbered
- `pr_info/steps/summary.md`: Removed `types.py` from files table

**Status**: committed

## Final Status

- **Rounds run**: 2
- **Commits**: 2 (round 1 plan updates + round 2 TypedDict revert)
- **Plan status**: Ready for approval — no remaining issues
