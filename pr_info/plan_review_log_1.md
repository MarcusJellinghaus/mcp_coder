# Plan Review Log — Issue #847

**Issue:** Support Copilot as second CLI LLM interface
**Branch:** 847-support-copilot-as-second-cli-llm-interface
**Reviewer:** Plan review supervisor

## Round 1 — 2026-04-19

**Findings** (11 total from engineer review):
- #1 (Low): Summary lists claude_executable_finder.py as modified but step 2 descoped it
- #2 (Medium): Cross-provider import — copilot importing sanitize_branch_identifier from claude log paths
- #3 (Medium): Cross-provider import — copilot importing logging_utils from claude package
- #4 (Low): CLI help text changes with sorted providers — no snapshot test warning
- #5 (Medium): Import linter contracts not mentioned — need lint-imports verification per step
- #6 (Low): `_read_settings_allow` in interface.py adds provider-specific logic
- #7 (Low): `Bash(*)` wildcard edge case not specified in tool converter
- #8 (Informational): No pyproject.toml dependency changes needed — positive
- #9 (Informational): Step granularity is appropriate — positive
- #10 (Low): 8KB limit check should measure full command line, not just prompt
- #11 (Informational): Subprocess isolation contract is respected — positive

**Decisions**:
- #1: Accept — remove from summary (straightforward fix)
- #2: Ask user — cross-provider import affects architecture
- #3: Ask user — same concern as #2
- #4: Accept — add note to step 1
- #5: Accept — lint-imports is already part of quality checks per CLAUDE.md
- #6: Accept — move settings reader into copilot module (simpler dispatcher)
- #7: Accept — add Bash(*) wildcard mapping clarification
- #8: Skip — informational
- #9: Skip — informational
- #10: Accept — clarify full command line measurement
- #11: Skip — informational

**User decisions**:
- #2 + #3: User chose "Extract to shared" — move sanitize_branch_identifier + DEFAULT_LOGS_DIR to `llm/log_utils.py`, move logging_utils to `llm/logging_utils.py`

**Changes**:
- `summary.md`: Removed claude_executable_finder.py row, added 5 new modified file entries for shared utility extraction
- `step_1.md`: Added CLI help text snapshot test warning note
- `step_3.md`: Added sub-step 3a to extract shared log_utils.py, updated imports to use `...log_utils`, added test file
- `step_4.md`: Added Bash(*) → shell(*) mapping and test case
- `step_5.md`: Added sub-step 5a to move logging_utils.py, clarified 8KB limit measurement, changed settings_allow → execution_dir parameter
- `step_7.md`: Moved _read_settings_allow into copilot_cli.py, interface just passes execution_dir

**Status**: committed (43780fc)

## Round 2 — 2026-04-19

**Findings** (8 actionable from engineer review):
- #1 (Medium): Step 5 missing `claude_code_api.py` from import update list after logging_utils move
- #2 (Medium): `.importlinter` `mlflow_logger_no_cycles` contract references old `logging_utils` path
- #3 (Medium): Step 6 `ask_copilot_cli_stream` still uses `settings_allow` parameter instead of `execution_dir`
- #5 (Low): `claude_code_cli.py` imports `sanitize_branch_identifier` — re-export strategy not specified
- #6 (Low): Existing tests for `sanitize_branch_identifier` in `test_claude_cli_stream_parsing.py` — dedup not addressed
- #7 (Low): Summary.md mixes new/moved files into "Files Modified" table
- #8 (Low): Summary.md missing `claude_code_api.py` in modified files
- #9 (Low): Summary.md missing `.importlinter` in modified files

**Decisions**:
- All findings accepted — all are straightforward consistency fixes, no design questions

**User decisions**: None needed

**Changes**:
- `step_5.md`: Added `claude_code_api.py` and `.importlinter` to modified files and sub-step 5a
- `step_6.md`: Changed `settings_allow` → `execution_dir` parameter, updated algorithm
- `step_3.md`: Added re-export strategy guidance and existing test dedup note
- `summary.md`: Moved `log_utils.py` to Files Created, added `claude_code_api.py` and `.importlinter` to Files Modified

**Status**: committed (8a7ce7d)

## Round 3 — 2026-04-19

**Findings** (5 actionable):
- #1 (Medium): `claude_code_cli_streaming.py` doesn't import `logging_utils` — phantom modification in step 5 and summary
- #2 (Medium): Summary missing 3 created test files (test_types.py, test_log_utils.py, test_copilot_cli_log_paths.py)
- #3 (Low): `test_logging_utils.py` move and caplog logger name change not in summary
- #4 (Low): `logging_utils.py` misclassified as "Modified" instead of "Created (moved)" in summary
- #5 (Low): `copilot_cli_integration` marker not in recommended exclusion patterns

**Decisions**: All accepted — straightforward consistency fixes

**User decisions**: None needed

**Changes**:
- `step_5.md`: Removed phantom `claude_code_cli_streaming.py` from modified files and sub-step 5a
- `step_1.md`: Added note about updating exclusion patterns for `copilot_cli_integration`
- `summary.md`: Removed phantom streaming file row, added 3 missing test files to Created, reclassified logging_utils.py as Created, added test_logging_utils.py move

**Status**: committed (282918b)

## Round 4 — 2026-04-19

**Findings** (4 actionable):
- A (Medium): `tests/llm/test_types.py` misclassified as "Created" in summary — file already exists (245 lines)
- B (Medium): `_read_settings_allow()` defined in step 7 but needed by step 5's `ask_copilot_cli()` — ordering issue
- C (Low): `.claude/CLAUDE.md` not listed in step 1's modified files despite needing exclusion pattern update
- D (Low): `__init__.py` export timing — step 5 tests should import directly from module, not package

**Decisions**: All accepted — straightforward consistency fixes

**User decisions**: None needed

**Changes**:
- `summary.md`: Moved test_types.py to Files Modified, added CLAUDE.md to Files Modified
- `step_5.md`: Added `_read_settings_allow()` specification and tests (moved from step 7), added __init__.py export timing note
- `step_7.md`: Replaced `_read_settings_allow` spec with reference to step 5
- `step_1.md`: Added CLAUDE.md to modified files

**Status**: committed (53dc191)

## Round 5 — 2026-04-19

**Findings**: None. All prior fixes verified against source code. Plan is internally consistent.

**Status**: PASS — no changes needed

## Final Status

- **Rounds run**: 5 (4 with changes, 1 clean verification)
- **Commits produced**: 4 (43780fc, 8a7ce7d, 282918b, 53dc191)
- **User decisions**: 1 (extract shared utilities vs duplicate vs leave cross-provider imports)
- **Key changes from review**:
  - Extracted shared `log_utils.py` and `logging_utils.py` out of claude provider package
  - Moved `_read_settings_allow()` into copilot module and reordered to step 5
  - Fixed parameter consistency (`settings_allow` → `execution_dir`) across steps 5/6/7
  - Added missing files to plan (claude_code_api.py, .importlinter, CLAUDE.md, test files)
  - Removed phantom modifications (claude_executable_finder.py, claude_code_cli_streaming.py)
  - Added Bash(*) wildcard mapping, 8KB limit clarification, CLI help text note
- **Plan status**: Ready for implementation approval
