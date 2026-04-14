# Plan Review Log — Issue #808

## Overview
- **Issue**: iCoder: token usage + version in status line
- **Branch**: 808-icoder-token-usage-version-in-status-line
- **Steps reviewed**: step_1 through step_4 + summary

## Round 1 — 2026-04-14
**Findings**:
- [Critical] Race condition: `token_usage.update()` runs after for-loop in `stream_llm()`, but UI thread may read `token_usage` on `StreamDone` before post-loop code executes
- [Critical] `has_data` semantics vs decision #6/#11 initial display — zeroes shown in compose(), hidden on StreamDone when no data
- [Accept] Usage extraction path indirect (via assembler.result() instead of event dict)
- [Accept] Step 3 too large for single commit
- [Accept] Version string in snapshot tests — changes every release, fragile
- [Accept] Missing UI tests for `_update_token_display()`
- [Accept] `format_token_count` boundary at 9999 produces "10.0k" instead of "10k"
- [Skip] `__future__ annotations` compatibility — already correct
- [Skip] Documentation directory structure — organizational choice
- [Skip] `display_text()` returns text when no data — minor doc improvement

**Decisions**:
- Accept: Race condition fix — move usage extraction inside for-loop (subsumes indirect path fix)
- Skip: `has_data`/decision #6 vs #11 — plan handles both correctly (zeroes before LLM call, hide after StreamDone with no data)
- Skip: Step 3 size — changes are tightly coupled, splitting creates broken intermediate states
- Accept: Version in snapshots — add fixed version in test fixture
- Accept: Missing UI tests — add async test for status bar behavior
- Accept: format_token_count boundary — change threshold to k < 9.95

**User decisions**: None needed — all findings were straightforward improvements.

**Changes**:
- `step_1.md`: Updated algorithm threshold to `k < 9.95` / `m < 9.95`, updated DATA and test expectations for boundary cases
- `step_2.md`: Moved usage extraction inside for-loop (from event dict, not assembler.result()), added race condition rationale
- `step_3.md`: Added snapshot fixture version pinning requirement, added UI test requirements for `_update_token_display()`
- `summary.md`: Updated architecture and data flow to match in-loop extraction

**Status**: committed (pending)

## Round 2 — 2026-04-14
**Findings**:
- [Accept] ALGORITHM pseudocode uses `widget.show()`/`hide()` but WHAT section uses class-based `remove_class("hidden")`/`add_class("hidden")`
- [Accept] Snapshot fixture version pin — two alternatives offered without picking one or showing code
- [Skip] `_update_token_display` not called in error/cancel paths — edge case, usage recorded for next stream
- [Skip] Redundant `isinstance(usage, dict)` check — defensive coding, fine

**Decisions**:
- Accept: Fix ALGORITHM pseudocode to use class-based approach
- Accept: Pick RuntimeInfo approach for snapshot fixture, show explicit code snippet
- Skip: Error/cancel paths — keeping error paths simple is correct
- Skip: isinstance check — defensive coding is acceptable

**User decisions**: None needed.

**Changes**:
- `step_3.md`: Aligned ALGORITHM pseudocode with class-based visibility API; replaced ambiguous fixture guidance with explicit `RuntimeInfo(mcp_coder_version="0.0.0-test")` snippet

**Status**: committed (pending)

## Round 3 — 2026-04-14
**Findings**: None — round 2 fixes verified correct, no new inconsistencies.
**Status**: no changes needed

## Final Status
- **Rounds run**: 3
- **Plan files changed**: step_1.md, step_2.md, step_3.md, summary.md
- **Review result**: Plan is ready for approval. All 11 issue decisions covered. Key improvements: race condition fix, format boundary fix, snapshot stability, UI test coverage.
