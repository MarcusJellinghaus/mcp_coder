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

**Status**: Committing...
