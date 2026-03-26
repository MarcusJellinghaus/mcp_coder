# Plan Review Log — Issue #602

## Round 1 — 2026-03-26

**Findings**:

- **Critical #1**: Total call count wrong — plan says ~72, actual is 101. Multi-line `logger.log(\n    NOTICE, ...)` calls were missed by single-line grep.
- **Critical #2**: `coordinator/commands.py` has 6 calls, not 2.
- **Critical #3**: `coordinator/core.py` has 1 call, not 4.
- **Critical #4**: `create_plan.py` has 28 calls, not 18.
- **Critical #5**: `create_pr/core.py` has 11 calls, not 8.
- **Critical #6**: `implement/core.py` has 22 calls, not 18.
- **Critical #7**: `implement/task_processing.py` has 6 calls, not 4.
- **Critical #8**: 4 "import-only" files actually have NOTICE log calls — removing imports without converting calls would cause `NameError`:
  - `session_launch.py` — 1 call
  - `session_restart.py` — 1 call
  - `branch_manager.py` — 2 calls
  - `manager.py` — 1 call
- **Critical #9**: Two test files (`test_prerequisites.py`, `test_branch_management.py`) assert on `mock_logger.log.call_args_list` with NOTICE — review confirmed they're resilient (use combined `all_calls` pattern), so no changes needed.
- **Accept #10**: `tests/cli/test_main.py` confirmed correct — no changes needed (threshold resolution tests only).
- **Accept #11**: LLM prompt sections in step files have wrong counts — must be corrected alongside the main content.
- **Accept #12**: `summary.md` table repeats wrong counts — must be updated too.

**Decisions**:

- Critical #1–#8: **Accept** — factual corrections, must fix in plan. Root cause: single-line grep missed multi-line calls.
- Critical #9: **Skip** — tests are resilient, no plan change needed. Add note to summary.md acknowledging this.
- Accept #10: **Skip** — plan is already correct.
- Accept #11–#12: **Accept** — straightforward count corrections in plan text.

**User decisions**: None needed — all findings are factual corrections.

**Changes**: Updated call counts in summary.md, step_2.md, step_3.md. Moved 4 "import-only" files into main log-revert sections. Removed empty "unused import removal only" section.

**Status**: Committed

## Round 2 — 2026-03-26

**Findings**:

- Missing `llm_integration` marker in pytest exclusion patterns (all 3 steps) — would cause slow/failing integration tests during verification
- `log_utils.py` listed in both "Files Modified" and "Files NOT modified" tables in summary.md — contradictory

**Decisions**:

- Both: **Accept** — straightforward fixes, no design impact

**User decisions**: None needed.

**Changes**: Added `and not llm_integration` to pytest markers in step_1.md, step_2.md, step_3.md. Removed `log_utils.py` from "Files NOT modified" in summary.md.

**Status**: Committed

## Final Status

- **Rounds**: 2
- **Commits**: 2 (plan count corrections + marker/table fixes)
- **Plan status**: Ready for approval — all counts verified against source, step structure sound, no remaining issues.
