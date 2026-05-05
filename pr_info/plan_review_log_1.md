# Plan Review Log — Run 1

**Issue**: #946
**Date**: 2026-05-05
**Branch**: 946-verify-render-per-permission-probe-results-from-upstream-verify-github


## Round 1 — 2026-05-05

**Findings**:
- Plan deviates from issue body item 3 (helpers `_github_ok()`/`_github_fail()` not extended) — undocumented in plan
- Test plan missing label-width test (issue body item 4) for the longest label `"Actions: Read"` at `_LABEL_WIDTH=22`
- Test `test_header_appears_once_and_after_auto_delete_branches` only checks header position, not probe-row position
- Definition of done has truncated `not <integration>` exclusion list and three `mcp__tools-py__*` → `mcp__mcp-tools-py__*` typos
- TASK_TRACKER.md unpopulated (expected — gets populated as step 0 of implementation; no action)
- CI failing on upstream `mcp-coder-utils` URL-dep resolution issue (pre-existing infrastructure issue, NOT a plan defect — no action)

**Decisions**: All findings auto-accepted by supervisor (straightforward improvements, no design questions). No user escalation needed.

**User decisions**: None — no questions required user input.

**Changes**:
- `pr_info/steps/step_1.md`: added "Decisions / Notes" section explaining helper deviation; strengthened `TestPermissionProbes` from 2 to 3 tests (added probe-row ordering assertion + new `test_perm_workflows_read_label_aligns_at_label_width`); replaced truncated marker exclusion list with full 10-marker list from CLAUDE.md; fixed `mcp__tools-py__*` typos
- `pr_info/steps/summary.md`: bumped `TestPermissionProbes` test count from "~2 tests" to "3 tests" for consistency

**Status**: Plan changes committed. Looping to Round 2 (fresh review).


## Round 2 — 2026-05-05

**Findings**: None. All Round 1 fixes verified to have landed correctly:
- Decisions/Notes section in `step_1.md` documents the deliberate helper deviation
- `TestPermissionProbes` strengthened to 3 tests (parametrized rendering + ordering + label-width alignment)
- Definition of done uses full 10-marker exclusion list and correct `mcp__mcp-tools-py__*` prefix
- `summary.md` test count consistent at "3 tests"
- All cited source line numbers (`_LABEL_MAP` 217–247, `_format_section` 254–295, `_GITHUB_KEYS` 184–196) verified against current source

**Decisions**: No actions needed.

**User decisions**: None.

**Changes**: None — plan unchanged this round.

**Status**: No changes needed. Loop terminates.

## Final Status

**Rounds run**: 2
**Plan commits**: 1 (`d8ef869` — docs(plan): clarify deviation, strengthen test specs, fix DoD exclusion list)
**Outcome**: Plan approved. Ready for implementation.

**Plan satisfies issue #946 end-to-end:**
- 6 new `perm_*` entries in `_LABEL_MAP` with correct labels (incl. `"Actions: Read"` for `perm_workflows_read`)
- One-shot `[Permissions]` header inside `_format_section` (TOML-style, indent=2 header, indent=4 rows)
- `[ERR]` symbol for placeholder/`ok=False` (no `[WARN]`)
- No exit-code change (probes are `severity="warning"`)
- Test invariant `_GITHUB_KEYS` grown 11 → 17
- Single atomic commit (purely additive, ~10 LOC + tests)

**Pre-existing infrastructure note** (not a plan defect): CI is currently red because upstream `mcp-coder-utils` is declared as a URL dependency in `mcp-workspace`, which `uv` rejects unless re-declared in `mcp-coder`'s own `pyproject.toml`. This blocks CI for any branch and is out of scope for #946. Worth raising separately to the user.
