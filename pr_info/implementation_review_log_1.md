# Implementation Review Log — Run 1

**Issue:** #785 — config: harden type parsing with centralized schema and config validation
**Date:** 2026-04-13

## Round 1 — 2026-04-13
**Findings**:
- C1: `isinstance(True, int)` returns True in Python (bool is subclass of int), so boolean TOML values silently pass validation for int-typed fields (`cache_refresh_minutes`, `max_sessions`) in both `get_config_values()` and `_verify_section()`
- A1: Empty string env vars treated as "not set" — pre-existing behavior
- A2: Unknown sub-tables not flagged by verify — reasonable design choice
- A3: `_str_or_none` in langchain silently drops non-string values — schema catches it first
- A4: `cast()` usage in test fixtures — acceptable in test code
- A5: Redundant env var strings in mlflow_config_loader — harmless duplication

**Decisions**:
- C1: Accept — directly undermines PR's validation goal, bounded fix (2 locations + 2 tests)
- A1: Skip — pre-existing, not introduced by this PR
- A2: Skip — reasonable design choice for sub-tables
- A3: Skip — defense in depth, schema validates first
- A4: Skip — acceptable in test code
- A5: Skip — working correctly, harmless

**Changes**: Fixed bool/int gap in `user_config.py` (lines ~301 and ~468). Added tests in `test_user_config_schema.py` and `test_verify_config.py`.
**Status**: Committed as 1a9ec3b

## Round 2 — 2026-04-13
**Findings**: Fix verified correct at both locations. New tests pass. No new issues found.
**Decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Final Status

Review complete after 2 rounds, 1 commit produced. All quality checks pass (pylint, pytest, mypy — only pre-existing issues in unrelated `mcp_tools_py.py`). No remaining issues.
