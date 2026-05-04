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
