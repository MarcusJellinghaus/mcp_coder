# Implementation Review Log — Issue #905

**Issue:** icoder --continue-session: replay UI history and add session picker / /load
**Branch:** 905-icoder-continue-session-replay-ui-history-and-add-session-picker-load
**Started:** 2026-05-11

## Round 1 — 2026-05-11

**Findings:**
- Critical: import-linter Layered Architecture contract is BROKEN — new imports in `src/mcp_coder/cli/commands/icoder.py` (`mcp_coder.icoder.core.log_inventory`, `mcp_coder.icoder.ui.widgets.session_picker`) are not in the `[importlinter:contract:layered_architecture] ignore_imports` allowlist (`.importlinter:46-52`).
- Critical: resumed runs produce logs invisible to the next picker. `AppCore.prepare_for_resume` rotates the event log after `execute_icoder` already emitted `session_start` into file A; replay then writes events into file B without a `session_start.provider`, so per Decision #29 the picker hides file B. Same issue affects `/clear` rotation in `AppCore.handle_input` (Step 4).
- Critical: `EventLog.rotate()` filename collision — `_make_log_filename()` uses microsecond `strftime`, two rotations within the same microsecond produce identical paths. Two tests fail deterministically on Windows: `tests/icoder/test_event_log.py::test_rotate_changes_current_path` and `tests/icoder/test_app_core.py::test_clear_rotates_event_log`.
- Accept: `--session-id` is not in `add_mutually_exclusive_group()` in `src/mcp_coder/cli/parsers.py` and `execute_icoder` still has the silent priority-override logic — both contradict Decision #28.
- Skip: issue body's `metadata.log_file_path` legacy-resume prose is out of sync with the final picker-based design (Decisions #7, #9, #22). Documentation drift only.
- Skip: `replay.py` reaches into private `ICoderApp` methods (`_handle_stream_event`, `_flush_buffer`, etc.). Speculative future coupling, not a current bug.
- Skip: vulture false positives on registry/Textual event hooks.
- Skip: pre-existing unrelated pytest collection error in CLI smoke tests.

**Decisions:** Accept findings 1-4. Skip findings 5-8 with reasons above.

**Changes:**
- `.importlinter`: added `cli.commands.icoder -> icoder.core.log_inventory` and `cli.commands.icoder -> icoder.ui.widgets.session_picker` to the layered_architecture allowlist.
- `src/mcp_coder/icoder/core/event_log.py`: added module-level `emit_session_start(event_log, *, provider, runtime_info=None, session_id=None)` helper; added `_allocate_log_path(logs_dir)` collision-safe path allocator (appends `-<n>` suffix on same-tick rotations); used in `__init__` and `rotate()`; updated `_make_log_filename` docstring.
- `src/mcp_coder/cli/commands/icoder.py`: replaced inline `session_start` payload with `emit_session_start(...)` call; removed silent `--session-id` priority-override branch; cleaned the resume-resolution if/elif.
- `src/mcp_coder/icoder/core/app_core.py`: `prepare_for_resume` and `/clear` (`reset_session=True`) branch in `handle_input` now call `emit_session_start(...)` immediately after `event_log.rotate()` with current `provider`, `runtime_info`, and `session_id`.
- `src/mcp_coder/cli/parsers.py`: moved `--session-id` into the existing `add_mutually_exclusive_group()` with `--continue-session` / `--continue-session-from`.
- Tests added/updated: `test_rotate_handles_filename_collision`; post-rotate `session_start{provider}` visibility for both `prepare_for_resume` and `/clear`; parametrized parser test asserting all pairwise combinations of the three flags raise SystemExit; updated `test_multiple_inputs` and `test_do_resume_re_records_events_into_new_log` for the new "rotated log starts with session_start" invariant.

**Checks:** format clean (458 unchanged); pytest 1285 passed (fast subset) + 171 passed (textual_integration); pylint, mypy, ruff, lint-imports all PASSED (23 contracts kept).

**Status:** implementation complete — pending commit by commit agent.

## Round 2 — 2026-05-11

**Findings:**
- Skip-candidate (engineer): `emit_session_start` payload omits `mcp_coder_utils_version` (also `python_version`, `claude_code_version`) — replayed banner via `format_runtime_banner(session_start_event)` cannot render those lines while the live banner can.
- Skip-candidate (engineer): `_FILENAME_RE` in `log_inventory.py` doesn't match collision-suffixed names like `icoder_<ts>-2.jsonl`; falls through to mtime fallback, behaviorally correct.

Round-1 fixes verified: `emit_session_start` is wired into all three rotation sites (CLI startup, `/clear`, `prepare_for_resume`); `_allocate_log_path` collision regression test passes; mutually-exclusive flag group enforced via parametrized parser test; lint-imports clean.

**Decisions:**
- Accept finding 1 (upgrade Skip → Accept). The design intent in `summary.md §7` is "drift in env/versions is therefore visible" — that fails when fields are structurally absent from the persisted payload. Note: the issue body's Decision #2 says the old banner is NOT rendered, but `summary.md §7` overrides that with "old banner → divider → new banner" and the implementation followed summary.md. Aligning the payload with the chosen design is the right small fix.
- Skip finding 2. mtime fallback is correct; regex update would be larger and asserts no current behavior.

**Changes:**
- `src/mcp_coder/icoder/core/event_log.py`: `emit_session_start()` now spreads `mcp_coder_utils_version`, `python_version`, and `claude_code_version` from `runtime_info` into the persisted `session_start` payload, alongside the previously-persisted fields. Live and replayed banners are now field-for-field equivalent.
- `tests/icoder/test_event_log.py`: extended `test_emit_session_start_includes_runtime_info_fields` to assert the three new fields; added `test_emit_session_start_payload_covers_live_banner_keys` asserting every key `format_runtime_banner` consults is present in the persisted payload.

**Checks:** format clean; pytest 3832 passed (unit) + 171 passed (textual_integration); pylint, mypy, ruff, lint-imports all PASSED.

**Status:** committed (`2df42af`).

## Round 3 — 2026-05-11

**Findings:** none.

**Round 2 verification:** the new fields (`mcp_coder_utils_version`, `python_version`, `claude_code_version`) are persisted via `emit_session_start` and consumed by `format_runtime_banner` in `do_resume`. `test_emit_session_start_payload_covers_live_banner_keys` pins the contract. All quality gates (pylint, mypy, ruff, lint-imports 23/23, pytest unit + textual_integration) green.

**Decisions:** exit the loop — zero code changes this round.

**Status:** loop closed.

## Final Status

**Rounds run:** 3 (1 review + fix, 2 review + fix, 3 verification only).

**Commits produced on this branch:**
- `f5af48f` — `icoder: ensure rotated event logs stay picker-visible and tighten resume flags` (round 1: import-linter allowlist, `emit_session_start` helper, collision-safe log paths, mutually-exclusive resume flags).
- `2df42af` — `icoder: persist full version set in session_start payload` (round 2: `mcp_coder_utils_version`, `python_version`, `claude_code_version` added to payload).
- `8c2a265` — `Whitelist new icoder TUI false positives (handle_load, session_picker hooks)` (vulture whitelist).

**Vulture:** clean after whitelist update.
**Lint-imports:** PASSED, 23 contracts kept, 0 broken.
**Pytest:** unit subset + `textual_integration` all green.
**Other static checks:** pylint, mypy, ruff all clean.

**Open issues:** none. The branch is ready for PR review by a human.

**Skipped findings (with reasons recorded above):** issue-prose vs picker-design drift around `metadata.log_file_path` (documentation drift only); `replay.py` reaches into private `ICoderApp` methods (speculative future-coupling, no current bug); `_FILENAME_RE` doesn't match collision-suffixed filenames (mtime fallback covers it).

