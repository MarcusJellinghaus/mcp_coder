# Plan Review Log — Issue #712 (Add generic faulthandler crash instrumentation utility)

## Round 1 — 2026-04-07

**Findings:**
- I1 (HIGH): step_2 `test_faulthandler_enabled_on_import` is unreliable — `mcp_coder.cli.main` is likely already imported by other tests, so the assertion may pass without testing the import-time wiring.
- I2: step_3 wiring tests must patch `enable_crash_logging` at the *importing* module's binding (e.g. `mcp_coder.cli.commands.implement.enable_crash_logging`), not at `mcp_coder.utils.crash_logging`, due to `from ... import` semantics.
- I3: step_1 `test_enable_swallows_error` should pin failure injection to `os.makedirs` (matching `session_storage.py` pattern) so the test/impl can't drift apart.
- I4: step_1 `test_enable_idempotent` should explicitly assert `_state['handle']` is the same object across calls (no second open).
- I5: step_4 algorithm snippet uses `sys.argv[1]` but does not `import sys`.
- I6: step_1 should reaffirm the `_state` dict pattern (no `global` keyword) so the implementer doesn't trip the pylint disable noted in the issue.
- I7: summary.md cited `src/mcp_coder/utils/session_storage.py:62`; the actual file lives at `src/mcp_coder/llm/storage/session_storage.py`.
- D1: step_4 integration test calls `faulthandler._sigsegv()` and asserts traceback content in the crash log; on Windows there is theoretical risk of unflushed output before process termination.
- D2: `enable_crash_logging` accepts only `Path` for `project_dir` — confirmed all current callers pass `Path`, no action needed.
- D3: Location of `_reset_for_testing` fixture (in-file vs conftest) — implementer's choice, no plan change needed.

**Decisions:**
- I1–I7: accepted as straightforward improvements, applied to plan files.
- D1: escalated to user.
- D2, D3: skipped (no plan change required).

**User decisions:**
- D1: Windows is the development priority. Decision: keep the strong assertion (test traceback content), and add a documented fallback note to step_4 — if `_sigsegv()` proves flaky on Windows during implementation, soften the assertion to "crash log file exists and is non-empty". Rationale: faulthandler is designed for cross-platform crash capture; the strong assertion is the only meaningful end-to-end test.

**Changes:**
- `pr_info/steps/step_1.md`: pinned failure injection to `os.makedirs(..., exist_ok=True)`; corrected session_storage path; added explicit `_state['handle']` identity assertion to idempotency test; reaffirmed `_state` dict pattern (no `global`).
- `pr_info/steps/step_2.md`: replaced in-process `test_faulthandler_enabled_on_import` with a subprocess-based test that uses a clean interpreter.
- `pr_info/steps/step_3.md`: added explicit guidance to patch `enable_crash_logging` at the importing module's binding.
- `pr_info/steps/step_4.md`: added `import sys` to the script snippet; added Windows fallback note for `_sigsegv()` flakiness.
- `pr_info/steps/summary.md`: corrected `session_storage.py` path reference (dropped load-bearing line number).

**Status:** changes committed (see commit by commit agent).


## Round 2 — 2026-04-07

**Findings:** Verified all round-1 changes landed cleanly. No critical findings. A few micro-polish items noted (mirror step_3's mock-binding guidance into step_1, minor verbosity in step_2 note) but all safely left to the implementer.
**Decisions:** All findings are micro-polish; no plan changes warranted.
**User decisions:** None required.
**Changes:** None.
**Status:** No changes — plan is internally consistent and aligned with all issue #712 acceptance criteria.

## Final Status

- **Rounds run:** 2
- **Plan changes:** Round 1 (5 files updated for I1–I7 + D1 fallback note); Round 2 no changes.
- **Verdict:** Plan is ready for approval.
- **All acceptance criteria from issue #712 are mapped to steps; planning principles satisfied (one-commit steps, TDD, tests mirror src, no prep/rollback/verify steps); software engineering principles satisfied.**
