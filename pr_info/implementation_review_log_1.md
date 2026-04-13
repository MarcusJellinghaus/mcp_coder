# Implementation Review Log — Run 1

**Issue:** #737 — refactor: consolidate formatters into mcp-tools-py
**Date:** 2026-04-13
**Reviewer:** Supervisor agent

## Round 1 — 2026-04-13
**Findings**:
- (Critical) `run_format_code` shim returns plain dicts but caller uses attribute access (`.success`, `.output`) — runtime `AttributeError` masked by MagicMock in tests
- (Accept) Unused mock parameter `mock_run_finalisation` in `test_core.py` — vulture finding
- (Accept) Stale comments in `.importlinter` referencing deleted formatter modules
- (Skip) Commented-out tach.toml reference — harmless

**Decisions**:
- Finding 1: Accept (Critical) — real runtime bug, must fix
- Finding 2: Accept — prefix with `_`, quick fix
- Finding 3: Accept — Boy Scout cleanup of stale comments
- Finding 4: Skip — commented-out code, harmless

**Changes**:
- Added `FormatterResult(NamedTuple)` to `src/mcp_coder/mcp_tools_py.py`, replaced dict literal with NamedTuple, updated return type annotation
- Prefixed unused mock `_mock_run_finalisation` in `tests/workflows/implement/test_core.py`
- Updated `.importlinter` comments for `black_isolation` and `isort_isolation` contracts

**Status**: Committed (c0fce44)

## Round 2 — 2026-04-13
**Findings**: None — branch is clean
**Decisions**: N/A
**Changes**: None
**Status**: No changes needed

## Final Status

Review complete after 2 rounds. 1 commit produced (c0fce44). All 6 quality checks pass (pylint, pytest, mypy, lint_imports, vulture, ruff). Zero stale references to `mcp_coder.formatters`, `get_formatter_config`, or `check_line_length_conflicts` remain.
