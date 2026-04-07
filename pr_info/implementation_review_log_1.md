# Implementation Review Log — Issue #712

Branch: 712-add-generic-faulthandler-crash-instrumentation-utility
Started: 2026-04-07

## Round 1 — 2026-04-07

**Findings**:
- [critical] `tests/utils/test_crash_logging.py` and `tests/cli/test_main.py` import `subprocess` directly, breaking the `Subprocess Library Isolation` import contract.
- [accept] `faulthandler.enable(file=sys.stderr, all_threads=True)` in `src/mcp_coder/cli/main.py` was placed AFTER the heavy `from .commands.* import ...` block. AC requires it before heavy imports so import-time crashes are captured.
- [skip] Vulture warning on autouse fixture `_isolate_crash_logging_state` — false positive; vulture doesn't recognise pytest autouse usage.
- [skip] `open()` with `# noqa: SIM115` in `crash_logging.py` — handle must outlive the function for faulthandler; documented in the issue body.
- [skip] Module-level `_state` dict — deliberate design choice (avoids `global` statements).
- [skip] No try/except around `enable_crash_logging` at call sites — function never raises by contract.

**Decisions**:
- Critical → fix by migrating both tests to `mcp_coder.utils.subprocess_runner.execute_subprocess`.
- Accept → reorder `faulthandler.enable(...)` above heavy imports; use `isort:skip_file` to keep the placement stable.
- All skip-suggestions → leave as-is.

**Changes**:
- `tests/utils/test_crash_logging.py`: replaced `subprocess.run` with `execute_subprocess`; removed `import subprocess`; updated assertion to `result.return_code != 0`.
- `tests/cli/test_main.py`: same migration for `TestFaulthandlerSafetyNet.test_faulthandler_enabled_on_import`.
- `src/mcp_coder/cli/main.py`: moved `faulthandler.enable(...)` to immediately follow the stdlib imports; added `isort:skip_file` to keep the placement stable through formatting.

**Status**: All five quality checks pass (pylint, pytest 3334 passed, mypy, lint_imports — Subprocess Library Isolation now KEPT, vulture only the documented false positive). Committed as 29cd8d9.

## Round 2 — 2026-04-07

**Findings**:
- Round 1 fixes verified: subprocess isolation contract KEPT in both test files; `faulthandler.enable` correctly placed before heavy imports in `cli/main.py`.
- `isort:skip_file` checked — manual inspection confirms remaining imports are still in canonical order. A more surgical `# isort: off / on` block would be a nicer alternative but not required.
- Vulture false positive on the `_isolate_crash_logging_state` autouse fixture persists — already triaged as skip in round 1.

**Decisions**: No code changes required.

**Changes**: None.

**Status**: All five quality checks pass + ruff. Loop terminates.

## Final Status

- 2 review rounds run (1 with fixes, 1 clean).
- 1 commit produced this run: `29cd8d9` (subprocess_runner migration + faulthandler reorder).
- All quality checks green. Branch ready for the next phase.
