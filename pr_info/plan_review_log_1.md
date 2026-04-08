# Plan Review Log — Issue #735

Branch: `735-icoder-token-per-line-streaming-bug-regression-tests`
Base: `main` (up to date, no rebase needed)
Plan files at start: `summary.md`, `step_1.md`, `step_2.md`, `step_3.md`
Knowledge base: `software_engineering_principles.md`, `planning_principles.md`, `refactoring_principles.md`

## Round 1 — 2026-04-08

**Findings**:
1. [blocker] Test assertions use plain `in` — won't catch per-token bug for single-word lines; no post-stream Static-empty check.
2. [blocker] Missing edge case: chunk ending exactly on `\n`.
3. [improvement] Undefined behavior for chunk containing only `\n`.
4. [improvement] Error path loses trailing blank line (spacing only via StreamDone handler).
5. [improvement] Step 2 escape hatch allows modifying `app.py` — blurs commit boundaries.
6. [improvement] Factory fixture manually juggles `EventLog.__enter__/__exit__` instead of reusing existing `event_log` fixture.
7. [nit] `output.write("")` for blank spacing — existing pattern, no change.
8. [improvement] Snapshot regeneration in step 3 lacks baseline-diff rigor.
9. [improvement] `height: auto` on empty Static may collapse — regeneration assumption unverified.
10. [improvement] No tests assert `Static#streaming-tail` content during/after streaming.
11. [nit] Commit message footers — OK.
12. [nit] Strict TDD framing impossible due to DOM-invalidating widget addition.

**Decisions**: All findings accepted as straightforward improvements — no user escalation needed (no scope/architecture impact). Default for empty-line handling: Option A (preserve blank lines, match LLM intent). Nits 7 and 11 skipped (no action). Nit 12 accepted (reword).

**User decisions**: None — none required this round.

**Changes**:
- `step_1.md`: relaxed TDD wording; `_append_blank_line` called on both success and error paths; documented Option-A blank-line preservation; simplified `make_icoder_app` factory to reuse `event_log` fixture + accept `llm_service` kwarg; tightened tests a–e with `.count()` / `.index()` / streaming-tail empty assertions; added edge cases e2 (chunk ends on `\n`), e3 (newline-only chunk), e4 (mid-stream Static tail assertion).
- `step_2.md`: removed production-edit escape hatch, marked strictly tests-only, updated prompt and WHERE table.
- `step_3.md`: added mandatory baseline-diff review step (only Static row should change); noted `height: auto` collapse behavior; instructed using `git diff --stat` to commit only genuinely changed baselines.

**Status**: Committed as `ad726fe`.

## Round 2 — 2026-04-08

**Findings**:
1. [nit] `summary.md` design-table row for `_append_blank_line` still said "Removed…" — contradicts step_1.md which keeps the helper on both paths.
2. [nit] Step 2 test g (and h) calls `make_icoder_app` positionally; Step 1 factory is keyword-only.
3. [nit] Step 3 snapshot snippet declared `list[list[StreamEvent]]` and imported `StreamEvent` — unnecessary; existing snapshot tests use plain literals.
4. [nit] Step 2 test h comment hard-coded `"> test"` as the user-input echo; format unverified.

**Decisions**: All nits accepted — trivial cleanups, no user escalation.

**User decisions**: None.

**Changes**:
- `summary.md`: updated `_append_blank_line` row to "Kept — called from `StreamDone` success path and `except` branch after flush."
- `step_2.md`: switched test g and h factory calls to `responses=` keyword; softened test h comment (no more `"> test"` literal, added note to verify echo format during implementation).
- `step_3.md`: dropped `StreamEvent` import + annotation in snapshot test snippet; added note to match existing `test_snapshots.py` literal style.

**Status**: Committed as `dabb59e`.

## Round 3 — 2026-04-08

**Findings**: None. Plan is internally consistent and ready for implementation.

**Decisions**: n/a.

**User decisions**: None.

**Changes**: None — zero-change round terminates the review loop.

**Status**: No plan changes needed.

## Final Status

Rounds run: **3**
Plan commits produced: **2** (`ad726fe`, `dabb59e`)
Round 3 produced zero plan changes — plan is **ready for approval**.
User escalations: **0** (all findings were straightforward improvements/nits).
