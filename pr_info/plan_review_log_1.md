# Plan Review Log — Issue #885

## Overview
Reviewing the 5-step plan for removing `install_from_github` session state and switching to auto-detect from pyproject.toml.

## Round 1 — 2026-04-26
**Findings**:
- Plan overall: PASS — accurate, complete, well-ordered. All file paths match codebase, code snippets correspond to real code, step ordering respects dependencies.
- Step 5: Ambiguous test file path — references both `tests/cli/test_parsers.py` and `tests/cli/commands/coordinator/test_vscodeclaude_cli.py` with uncertain phrasing. Only the latter has tests (3 tests at lines 336-365).
- Step 3: Unnecessarily mentions `test_session_restart.py` in test changes section when no `install_from_github` references exist there.
- Step 5: Speculative `### Parser test (if needed)` section with sample code is unnecessary — the tests already exist.

**Decisions**:
- Step 5 test path ambiguity: **Accept** — straightforward clarity improvement
- Step 3 unnecessary test mention: **Accept** — remove to avoid implementation confusion
- Step 5 speculative parser test: **Accept** — remove, replace with definitive instructions

**User decisions**: None needed — all findings were straightforward improvements.

**Changes**:
- `pr_info/steps/step_5.md`: Made test file path definitive, removed speculative parser test sample, replaced with clear instructions for updating 3 existing tests.
- `pr_info/steps/step_3.md`: Removed `test_session_restart.py` subsection from test changes.

**Status**: Committed (7d45ac7)

## Round 2 — 2026-04-26
**Findings**:
- CRITICAL: 9 test files with `install_from_github` references (~130 occurrences) missing from the plan. When Step 1 removes the TypedDict field, these would all break with no guidance for the implementer.
- MINOR: Summary table has wrong test path (`tests/cli/test_parsers.py` instead of `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`).

**Decisions**:
- Missing test files: **Accept** — distributed across the appropriate steps:
  - Step 1: 7 files with mechanical session dict cleanup (~110 occurrences)
  - Step 4: `test_session_restart.py` (~11 occurrences)
  - Step 5: `test_commands.py` (~9 refs testing parameter threading)
- Summary table wrong path: **Accept** — straightforward fix

**User decisions**: None needed.

**Changes**:
- `pr_info/steps/step_1.md`: Added 7 test files to WHERE, added "Mechanical test cleanup" subsection
- `pr_info/steps/step_4.md`: Added `test_session_restart.py` to WHERE and test changes
- `pr_info/steps/step_5.md`: Added `test_commands.py` to WHERE and test changes
- `pr_info/steps/summary.md`: Fixed test path, added 8 new test files to table

**Status**: Committed (1bade7b)

## Round 3 — 2026-04-26
**Findings**:
- Step 1 removes `install_from_github` from `build_session()` but doesn't update the call site at `session_launch.py:227`. Tests would fail between Steps 1 and 3 with `TypeError: build_session() got an unexpected keyword argument`.
- Review artifact `review_round_3.md` created in steps folder — should be deleted.

**Decisions**:
- Call site fix: **Accept** — each step must leave checks green (planning principles). Add minimal `session_launch.py` change to Step 1.
- Review artifact: **Accept** — delete from steps folder.

**User decisions**: None needed.

**Changes**:
- `pr_info/steps/step_1.md`: Added `session_launch.py` to WHERE, added subsection for removing `build_session()` kwarg at line ~227 (scoped explicitly — full rework in Step 3).
- Deleted `pr_info/steps/review_round_3.md` (review artifact).

**Status**: Committing...
