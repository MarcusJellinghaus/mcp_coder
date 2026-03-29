# Plan Review Log — Run 1

**Issue:** #618 — fix: launch_process() env inheritance + add env_remove to CommandOptions
**Date:** 2026-03-29
**Reviewer:** Supervisor agent

## Round 1 — 2026-03-29

**Findings**:
- F1 (critical): `_prepare_env` mutates env even when `launch_process` callers pass `env=None` — extra UTF-8 vars added to VSCode and other non-Python processes
- F2 (critical): Importing `_prepare_env` (private symbol) across module boundary will fail pylint
- F3 (critical): Step 2 should verify no tests depend on hardcoded CLAUDECODE removal
- F4 (improvement): Confirm removed imports are truly unused in streaming module
- F5 (improvement): Integration test in step 3 can't actually test `launch_process` output (DEVNULL)
- F6 (improvement): Utility function copy from p_tools confirmed identical
- F7 (question): `execute_command` convenience wrapper won't support `env_remove`
- F8 (improvement): Use parameterized tests to reduce boilerplate
- F9 (improvement): Steps 2+3 could merge but separate is acceptable
- F10 (improvement): Update `launch_process` docstring examples post-fix

**Decisions**:
- F1: Ask user → User chose option C (accept behavior change, UTF-8 vars are harmless)
- F2: Accept → Rename `_prepare_env` to `prepare_env` (no underscore, cross-module import)
- F3: Accept → Add safety note to step 2
- F4: Skip → Already verified safe
- F5: Accept → Move integration test to step 1, test `prepare_env` directly
- F6: Skip → Confirmed identical, no action
- F7: Accept → Add YAGNI note to step 1
- F8: Accept → Add parameterized test suggestions to steps 1 and 4
- F9: Skip → Separate commits for cleaner git history
- F10: Accept → Add docstring update to step 3

**User decisions**:
- F1: User chose option C — accept the behavior change. Extra UTF-8 environment variables are harmless for VSCode and other non-Python processes. Consistency across all subprocess functions is preferred.

**Changes**: Updated `summary.md`, `step_1.md`, `step_2.md`, `step_3.md`, `step_4.md` with all accepted findings.

**Status**: Ready to commit
