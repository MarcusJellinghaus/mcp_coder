# Plan Review Log — Issue #950

Issue: icoder: tone down branch-info polling and prefix version label

## Round 1 — 2026-05-04

**Findings**:
- Step 3 test #5 phrased as numbered test rather than regression anchor for `test_branch_change_kicks_pr_fetch`
- Step 4: implicit narrowing of `except Exception` → `except NoMatches` not pinned
- `branch_info_service.py` module docstring still says "2-second ticks" (stale after cadence change)
- Step 3: `on_mount` initial-full-tick call path not pinned (`_tick_branch_full()` vs direct `run_worker(self._branch_full_work, …)`)
- Step 3: `_timed_fetch` placement (method vs free function) not noted
- Step 5: textual snapshot regen possibility not flagged

**Decisions**:
- Accept all findings as straightforward improvements.
- `on_mount` call path: keep `run_worker(self._branch_full_work, ...)` (minimize startup diff; `begin_full_tick()` guard inside `_branch_full_work` still applies if a periodic tick races the startup tick).
- `_timed_fetch`: keep as method on `ICoderApp` for cohesion with the workers that call it.

**User decisions**: None — all findings handled autonomously per skill guidance ("default to simpler plans rather than asking").

**Changes**: See plan files diff for round (Step 2, Step 3, Step 4, Step 5 updates).

**Status**: Plan files updated; ready for next review round.

## Round 2 — 2026-05-04

**Findings**:
- Step 3: `on_mount` startup text said `_branch_full_work` but actual code at `app.py:142` uses `_tick_branch_full` — Round 1 wording was wrong
- Step 4: `NoMatches` is not imported in `app.py` today — narrowing requires adding the import
- Step 3: doc-update wording at `icoder.md` was ambiguous ("if present"); both line 52 and line 60 need `2s` → `10s`

**Decisions**:
- All three findings are straightforward; auto-applied. Option (a) chosen for the on_mount text — match actual code (preserves minimize-startup-diff intent).

**User decisions**: None — handled autonomously.

**Changes**: step_3.md (on_mount symbol fix + doc-update wording tightened); step_4.md (NoMatches import note added).

**Status**: Plan files updated; ready for next review round.

## Round 3 — 2026-05-04

**Findings**:
- Step 3: stale docstrings in `app.py` (`_tick_branch_quick`, `_branch_quick_work`) say "2-second tick" / "2s branch tick" — parallel to Step 2's Boy Scout note for `branch_info_service.py`
- Step 3: `Callable` import wording was conditional ("or add it if absent") — sharpened to a definite instruction
- Step 3: `_apply_pr_result` mentioned in `merge_with_prior=False` preservation list, but it doesn't call `_apply_branch_state` — removed

**Decisions**:
- All three findings are straightforward and auto-applied. No user input needed.

**User decisions**: None.

**Changes**: step_3.md only — Boy Scout docstring bullet added, `Callable` import wording sharpened, `_apply_pr_result` dropped from preservation list.

**Status**: Plan files updated; ready for next review round.


## Round 4 — 2026-05-04

**Findings**:
- Step 3: three stale line-number references in `app.py` citations — `app.py:138` (actual: line 9), `_tick_branch_quick` "around line 432-433" (actual: 309-310), `_branch_quick_work` "around line 441" (actual: 317-318)

**Decisions**:
- All three are cosmetic line-number fixes; auto-applied. The quoted code strings stayed correct so the intent was never lost — just the line citations.

**User decisions**: None.

**Changes**: step_3.md only — three line-number corrections.

**Status**: Plan files updated; ready for next review round.
