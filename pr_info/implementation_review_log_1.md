# Implementation Review Log — #844 iCoder Branch Info Bar (Run 1)

**Branch:** `844-icoder-show-branch-issue-pr-info-area-below-status-bar`
**Started:** 2026-05-01
**Scope:** Review the implementation diff for #844 against the issue requirements,
`pr_info/steps/summary.md`, `pr_info/steps/Decisions.md`, and the knowledge-base
principles (`software_engineering_principles.md`, `python.md`).

The implementation lives in 5 commits on this branch (08f523e..52e780b).

## Round 1 — 2026-05-01

**Findings** (17 total from `/implementation_review`):

1. `_apply_branch_state` keeps stale `_last_pr_number` when a PR worker legitimately resolves to `None` (deleted/closed PR). `[Accept]`
2. `_launch_pr_worker` mutates `_branch_failed`/`_branch_loading` *before* the generation-token check, so a stale worker pollutes the newer generation's UI state. `[Accept]`
3. `on_branch_info_bar_toggle_pr` launches a PR worker without going through `begin_pr_fetch()`, breaking the in-flight invariant the refresh button enforces. `[Accept]`
4. `branch_changed()` performs read-modify-write on `_last_branch` from the worker thread (`_branch_quick_work`); two overlapping ticks can race. `[Accept]`
5. `_apply_branch_state(None)` flow on transient errors — confirmed correct. `[Skip]`
6. String-typed `loading`/`failed` sets (`Literal` would be safer). `[Skip]` — speculative.
7. Vulture flags Textual auto-routed `on_*` handlers — false positives. `[Skip]` — pre-existing pattern.
8. Bare `except Exception` in `_render_branch_state` during mount window — intentional, with pylint disable. `[Skip]`
9. `format_cache_age` behaviour for negative deltas — clock-skew edge case, not in spec. `[Skip]`
10. Cache-shim renames complete (4/4). `[Skip]` — confirmation only.
11. PR-fetch generation token correctly defends documented races. `[Skip]` — confirmation.
12. Tach + import-linter wiring correct. `[Skip]` — confirmation.
13. Widget remains render-only with no I/O imports. `[Skip]` — confirmation.
14. Widget label colour resolution + contrast text correct. `[Skip]` — confirmation.
15. Step-file documented test cases all present. `[Skip]` — confirmation.
16. Pre-existing `tests/test_module_integration.py` fixture fix on this branch — out of #844 scope. `[Skip]`
17. Cross-thread state-set pattern (`_branch_loading`/`_branch_failed` worker-mutated) — acceptable under GIL. `[Skip]`

**Decisions:** Accept findings 1–4 (real bugs, bounded fixes, all in `app.py` ± one helper rename). Skip the rest per `software_engineering_principles.md` (speculative / cosmetic / pre-existing / confirmation).

**Changes:**

- Added `_apply_pr_result(pr_number)` helper that unconditionally writes the PR number (including `None`) and re-renders. PR worker callback dispatches through it. (Fix 1)
- Restructured `_launch_pr_worker.work()` so the generation-token check runs FIRST after `fetch_pr` returns/raises; only currents workers call `end_pr_fetch()`, mutate `_branch_failed`/`_branch_loading`, and dispatch the result. Stale workers exit silently. (Fix 2)
- `on_branch_info_bar_toggle_pr` now wraps the toggle-on launch in `begin_pr_fetch()` + `_branch_loading.add("pr")` + `_render_branch_state()` so the in-flight guard is uniform across both launch paths. (Fix 3)
- Removed `branch_changed()` / auto-PR-kick block from worker thread `_branch_quick_work`; moved the equivalent logic into `_apply_branch_state` (which runs on the UI thread via `call_from_thread`). (Fix 4)

**Tests added** (`tests/icoder/ui/test_app.py`):

- `test_pr_result_none_clears_stale_pr_number` (Fix 1)
- `test_stale_pr_worker_exception_does_not_set_failed_flag` (Fix 2 — exception path)
- `test_stale_pr_worker_success_does_not_mutate_state` (Fix 2 — success path)
- `test_toggle_on_while_worker_in_flight_does_not_duplicate` (Fix 3)

**Files changed:** `src/mcp_coder/icoder/ui/app.py`, `tests/icoder/ui/test_app.py`.

**Quality checks:** pylint clean, mypy clean, ruff clean, pytest unit tests 272 passed, textual_integration tests for `test_app.py` 21/21 passed. (Pre-existing flaky tests in `test_app_pilot.py` / `test_busy_indicator.py` unrelated to this branch — pass under lower parallelism.)

**Status:** committed (round 2 will follow because code changed).
