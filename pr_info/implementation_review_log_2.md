# Implementation Review Log — Run 2

Issue #629 — iCoder: tiered tool display with click-to-toggle, detail modal, and Response typed-action refactor

Supervisor: technical lead (delegating all implementation to engineer subagents).

Note: Run 1 (`implementation_review_log_1.md`) completed 3 rounds and reached a clean final status. This run re-verifies the branch state and reviews any remaining concerns.

---

## Round 1 — 2026-06-25 (re-review)

**Scope:** Fresh `/implementation_review` (skill instructions followed manually — `disable-model-invocation`). Confirmed a real, substantial implementation diff (not just plan/docs): ~24 source files under `src/`, plus tests and 3 new snapshot baselines. Run 1's two outstanding items are resolved (3 snapshot `.svg` baselines now committed in `b5f6b44`; lint-imports whitelist for `/display` present).

**Gate status observed:**
- pytest (fast unit subset): 4061 passed / 2 skipped / 0 failed
- mypy: PASS (no type errors)
- lint-imports: PASSED — 23 contracts kept, 0 broken
- vulture: 2 NEW findings in `tests/icoder/test_snapshots.py` (not present at Run 1's "clean" close)
- CI (check_branch_status): PASSED

**Findings:**
1. *(Skip-cosmetic)* `tests/icoder/test_snapshots.py:90` — new pytest fixture `_frozen_clocks` is flagged by vulture (60%) as unused; it is a fixture injected by name into 3 snapshot tests (false positive). Run 1 closed with vulture clean, so this is a whitelist-coverage regression. Fix: add `_.​_frozen_clocks` under the "Pytest Fixtures" section of `vulture_whitelist.py` (mirrors `_._no_store_session`). Vulture is not a hard CI gate per CLAUDE.md but Run 1 treated it as a tracked gate.
2. *(Skip-cosmetic)* `tests/icoder/test_snapshots.py:68` — `tz` param of `_FixedDatetime.now()` flagged unused (100%). Required to match `datetime.now()`'s signature for the monkeypatch; genuine false positive. Same fix path (whitelist) or rename to `_tz`.

**Re-confirmed correct (no new bug):**
- tier-1 oneline omits the `N lines` count from the issue's example — this is an explicit documented plan decision (`step_3.md` line 52: line counts live in compressed/modal tiers only). Not a deviation.
- `unit_at_line` "first containing range wins" is sound: `rebuild()` produces strictly disjoint, monotonically-advancing buffer ranges, so the multi-range assistant_turn vs tool "smallest range wins" requirement is satisfied.
- `is_error` propagation present in all three providers; FIFO pairing + `cleanup_pending` orphan handling intact; `/display` hard-reset + `RebuildOutput` wiring correct; replay uses the same `append_unit`/`_handle_stream_event` path (interactive replay).

**Decisions:** No code changes required. Both findings are cosmetic lint-gate false positives; per KB scope rules they are skip-worthy. Optional Boy-Scout: add the two whitelist entries to restore the Run-1 "vulture clean" state. No correctness/regression/contract/spec issues found.

**Status:** clean — re-review terminates with zero accepted code changes.

---

## Step 8 — Lint gates (supervisor-run)

Ran `run_vulture_check` and `run_lint_imports_check` directly:
- lint-imports: **PASSED** — 23 contracts kept, 0 broken.
- vulture: 2 findings (the two false-positives above). Decided to apply the Boy-Scout whitelist fix to restore Run-1's clean state (trivial, zero-risk lint-tooling config; not an architectural escalation).

**Change applied** (engineer subagent): `vulture_whitelist.py` — added two entries in the iCoder pytest-fixtures section:
- `_._frozen_clocks` (fixture injected by name into the snapshot tests)
- `_.tz` (unused param required to mirror `datetime.now(tz=...)` for monkeypatching)

Post-fix gates: vulture **ZERO findings**; pylint PASS; mypy PASS; format clean.

## Final Status

**Rounds run:** 1 review round (re-review). The review found zero correctness/regression/contract/spec issues; the only items were two vulture whitelist false-positives, fixed in step 8.

**Commits produced by this run:**
- (pending) — `vulture_whitelist.py`: whitelist `_frozen_clocks` fixture + `tz` param (restore vulture-clean).
- (pending) — this review log.

**Final gate status:**
- pylint: PASS
- mypy: PASS
- pytest: 4061 passed / 2 skipped / 0 failed (fast unit subset)
- `run_lint_imports_check`: PASSED — 23 contracts kept, 0 broken
- `run_vulture_check`: clean (no findings after whitelist additions)

**Outstanding:** none introduced by this run. The pre-existing 9 win32-only/`textual_integration` snapshot baselines noted in Run 1 remain out of scope (env/Textual-version drift, excluded from CI).

---

## Round 2 — 2026-06-25 (user-directed: startup info / snapshot baselines)

User redirected to the "9 pre-existing snapshot baselines" item and asked: *is there a problem showing the startup information?* Investigation found a **real, significant regression** (not env drift, as Run 1 had assumed).

**Finding 1 (Critical — fixed): `rebuild()` permanently wiped all non-unit content.**
`OutputLog.rebuild()` re-rendered the buffer by walking `_script`, which only contains registered content units. Content written via `append_text()` — the startup runtime-info banner (`on_mount`: `append_text("\n".join(lines), style="dim")`), `Resumed …`/`— Cancelled —` markers, dim dividers, blank spacers, error lines — was never in `_script`, so every `rebuild()` (`super().clear()` + replay-units) erased it. `rebuild()` fires on the first-paint `on_resize`, on **every** `tool_result` (`update_unit_and_rerender`), on tier toggle, and on `/display`. Net effect: the startup runtime-info block vanished as soon as the layout settled or the first tool ran. The issue spec had *assumed* "rebuild-on-resize heals the startup banner"; the implementation destroyed it instead. Proven via the pre-#629 `test_snapshot_initial_state.svg` (shows `Tool env:` / `Project dir:`) vs current render (omitted).

Fix (`src/mcp_coder/icoder/ui/widgets/output_log.py`): introduced `_ScriptEntry(unit_id, line, style)` so the replay script can carry non-unit literal lines. `append_text()` now records the line in `_script`/`_screen_lines`; `rebuild()` replays literal lines with their style but assigns NO range (banners stay on screen yet non-clickable). Added regression test `test_append_text_banner_survives_rebuild`; updated `test_recorded_lines_independent_of_units` and `test_app_pilot.py::test_resumed_divider_is_not_a_unit` which had encoded the buggy behavior.

**Finding 2 (Accept — fixed): snapshot suite was nondeterministic (the real reason the 9 baselines never stabilized).**
`ICoderApp.on_mount` kicks background git/gh polling for `BranchInfoBar` (`_tick_branch_full`/`_tick_branch_quick` worker + intervals); snapshots with `pilot.pause(delay=0.5)` captured the bar at a nondeterministic point (failing-test set even changed between `-n 0` and `-n auto`). A second source — the `InputArea` blinking text cursor — was also found. `_frozen_clocks` addressed neither.

Fix (`tests/icoder/test_snapshots.py`): autouse `_freeze_dynamic_ui` fixture no-ops the branch tick/worker/render paths and sets `InputArea.cursor_blink = False`, freezing the bar at its `update_state(None)` placeholder. All 12 baselines regenerated.

**Verification (all via `mcp__mcp-tools-py__run_pytest_check`):**
- Snapshot suite 12/12 PASSED across repeated runs — `-n auto` ×2 and `-n 0` ×1 (plus engineer's 5 runs) — deterministic.
- Fast unit subset: 4061 passed / 2 skipped / 0 failed.
- pylint PASS, mypy PASS.
- `test_snapshot_initial_state.svg` confirmed to contain `Tool env:` / `Project dir:` again.

**Note on tooling:** the pytest MCP tool works correctly; the earlier red was genuine test flakiness, not a tool fault. Baseline *regeneration* used `--snapshot-update` (the MCP check tool is pass/fail oriented); all verification runs went through the MCP tool.
