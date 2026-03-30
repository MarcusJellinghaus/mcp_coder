# Implementation Review Log — Run 1

**Issue:** #617 — iCoder: Initial Setup Textual TUI with Three-Layer Architecture
**Date:** 2026-03-30
**Reviewer:** Automated supervisor

## Round 1 — 2026-03-30

**Findings:**
- 2.1 CI Failure: unused `type: ignore[import-not-found]` on ICoderApp import (mypy)
- 2.2 Private `_recorded` access across class boundary in app.py
- 2.3 Use of private Textual API `_replace_via_keyboard` in InputArea
- 2.4 Unused imports `Worker`, `WorkerState` in app.py
- 3.1 Snapshot tests create EventLog without context manager
- 3.2 `env_vars` type narrowing could be cleaner
- 3.3 Plan docs naming mismatch (`lines` vs `recorded_lines`)
- 3.4 Architecture docs not updated for icoder
- 3.5 `FakeLLMService.stream()` unused `question` param

**Decisions:**
- 2.1 **Accept** — CI failure, must fix
- 2.2 **Accept** — Encapsulation violation, bounded fix
- 2.3 **Skip** — Known fragility but not a bug; public API may not behave identically
- 2.4 **Accept** — Dead imports, quick cleanup
- 3.1 **Accept** — Contradicts Decision 2, bounded fix
- 3.2 **Skip** — Works correctly, mypy doesn't complain, cosmetic
- 3.3 **Skip** — Plan docs in pr_info/ get deleted, out of scope
- 3.4 **Skip** — Follow-up issue territory, not a blocker
- 3.5 **Skip** — Standard for fakes/mocks, pylint not complaining

**Changes:**
- Removed `# type: ignore[import-not-found]` from icoder.py import
- Added `clear_recorded()` public method to OutputLog, updated app.py to use it
- Removed unused `Worker, WorkerState` import from app.py
- Refactored test_snapshots.py to use a fixture with teardown for EventLog cleanup

**Status:** Committed (3d5fa4b)

## Round 2 — 2026-03-30

**Findings:**
- C2 `mcp_coder.icoder` missing from `.importlinter` layered architecture
- C3 `tests.icoder` missing from `.importlinter` test module independence
- C4 Missing Textual library isolation contract in `.importlinter`
- S1 `elif` chain in app.py may skip LLM when text+send_to_llm both set
- S2 `OutputLog.append_tool_use` is dead code — not used by `_handle_stream_event`
- S3 `tach.toml` not updated for icoder module
- S4 Architecture docs not updated
- S5 (Supervisor-added) Textual tests need integration marker for fast test exclusion

**Decisions:**
- C2 **Accept** — Architectural enforcement gap, must fix
- C3 **Accept** — Same reasoning
- C4 **Accept** — Follows established pattern for all external libraries
- S1 **Skip** — Speculative future concern, YAGNI
- S2 **Accept** — Wire existing method instead of inline formatting
- S3 **Accept** — `tach.toml` exists and needs icoder module entry
- S4 **Skip** — Follow-up issue, already skipped in round 1
- S5 **Accept** — Tests were causing ~1hr run time without exclusion marker

**Changes:**
- Added `mcp_coder.icoder` to `.importlinter` layered architecture (pipe with cli)
- Added `tests.icoder` to test module independence contract
- Added `textual_library_isolation` forbidden contract
- Wired `append_tool_use()` in `_handle_stream_event` instead of inline formatting
- Added `mcp_coder.icoder` module entry in `tach.toml` presentation layer
- Added `textual_integration` marker to pyproject.toml
- Marked test_app_pilot.py, test_widgets.py, test_snapshots.py with `textual_integration`
- Updated CLAUDE.md recommended exclusion pattern

**Status:** Committed (18d487e)

## Round 3 — 2026-03-30

**Findings:**
- S2 Snapshot test EventLog fixture uses close() instead of context manager

**Decisions:**
- S2 **Accept** — Consistency with conftest.py pattern, trivial fix

**Changes:**
- Refactored snapshot fixture to use `with EventLog(...) as event_log:` pattern

**Status:** Committed (edd656d)

## Round 4 — 2026-03-30

**Findings:** No new critical or accept-worthy issues.

**Status:** No changes needed

## Final Status

- **Rounds:** 4
- **Commits produced:** 3 (3d5fa4b, 18d487e, edd656d)
- **All checks pass:** pylint, mypy, pytest (3025 tests), ruff
- **Remaining notes:** `_replace_via_keyboard` private API usage is a known fragility (skipped — no public alternative). Architecture docs update deferred to follow-up issue.
