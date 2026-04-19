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

**Status**: pending commit

