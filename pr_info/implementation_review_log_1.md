# Implementation Review Log — Run 1

**Issue:** #527 — Configurable Default MCP Config Path + Verify MCP for All Providers
**Date:** 2026-03-25

## Round 1 — 2026-03-25

**Findings:**
- Double-evaluation of env var in `resolve_mcp_config_path()`: when `MCP_CODER_MCP_CONFIG` points to a non-existent file, `get_config_values` re-detects the same env var via `_get_standard_env_var`, producing two warnings instead of one.

**Decisions:**
- Accept: Real UX issue with confusing duplicate warnings. Fix by suppressing env var auto-detection in the `get_config_values` call.

**Changes:**
- Changed `get_config_values([("mcp", "default_config_path", None)])` to `get_config_values([("mcp", "default_config_path", "")])` in `src/mcp_coder/cli/utils.py`.

**Status:** Committed (e773e20) — but fix was incorrect (see Round 2).

## Round 2 — 2026-03-25

**Findings:**
- Round 1 fix didn't work: `""` is falsy in Python, so `"" or _get_standard_env_var(...)` still falls through to auto-detection. Double warning persists.
- Three tests in `TestVerifyMcpAllProviders` missing `_run_mcp_edit_smoke_test` mock, causing `PermissionError` on Windows.

**Decisions:**
- Accept: Use truthy sentinel `"_NO_ENV_VAR_"` instead of `""`.
- Accept: Add missing smoke test mock decorator to three tests.

**Changes:**
- Changed `""` to `"_NO_ENV_VAR_"` in `src/mcp_coder/cli/utils.py` line 140.
- Added `@patch(f"{_VERIFY}._run_mcp_edit_smoke_test", ...)` to `test_mcp_servers_checked_for_claude_provider`, `test_mcp_failure_informational_for_claude`, `test_mcp_import_error_shows_info_message`.

**Status:** Committed (3841f8e).

## Round 3 — 2026-03-25

**Findings:**
- No new issues found. Round 2 fixes verified correct.
- All code quality checks pass (pylint, mypy, ruff, pytest).
- 4 pre-existing `test_session_priority.py` failures — unrelated to this branch.

**Decisions:** No action needed.

**Changes:** None.

**Status:** No changes needed.

## Final Status

**Rounds:** 3
**Commits:** 2 (e773e20, 3841f8e)
**Result:** All review findings resolved. Implementation is correct and complete. Ready to merge.
