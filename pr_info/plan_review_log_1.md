# Plan Review Log — Run 1

**Issue:** #527 — feat: configurable default mcp-config file path + verify MCP for all providers
**Date:** 2025-03-25

## Round 1 — 2025-03-25

**Findings:**
- **Critical C1:** Step 3 pseudocode omits that `mcp_config_resolved` is passed to `verify_langchain()` as kwarg
- **Critical C2:** Step 3 ImportError handling — need to verify if `langchain-mcp-adapters` is imported eagerly or lazily; plan should instruct lazy import if needed
- **Critical C3:** Step 2 calls `_get_source_annotation()` for MCP env var, but step 1 says "no new mapping in `_get_standard_env_var()`" — these are inconsistent
- **Improvement I4:** Existing tests need `monkeypatch.delenv("MCP_CODER_MCP_CONFIG")` to prevent pollution
- **Improvement I5:** Parameterized tests for fallback chain (suggestion, not mandatory)
- **Improvement I6:** `verify_config()` early return for invalid TOML won't show `[mcp]` — acceptable
- **Improvement I7:** Existing claude-provider tests will now call real `resolve_mcp_config_path` — need mock updates
- **Improvement I8:** `_run_mcp_edit_smoke_test()` will run for claude provider too — desirable, needs explicit mention
- **Improvement I9:** Docs step trivially passes code checks — cosmetic, skip

**Decisions:**
- C1: Accept — fix pseudocode in step 3
- C2: Accept — add lazy import guidance to step 3
- C3: Accept — add env var mapping to `_get_standard_env_var()` in step 1 (resolves inconsistency)
- I4: Accept — add note to step 1
- I5: Skip — suggestion only, not required
- I6: Skip — acceptable behavior, no change needed
- I7: Accept — add note to step 3
- I8: Accept — add note and test to step 3
- I9: Skip — cosmetic

**User decisions:** None needed — all findings were straightforward improvements.

**Changes:**
- `step_1.md`: Added env var mapping to `_get_standard_env_var()`, added test for it, added note about clearing env var in existing tests
- `step_2.md`: Added dependency note on step 1's env var mapping
- `step_3.md`: Fixed pseudocode, added lazy import guidance, added test mock note, added smoke test note + test

**Status:** Committed
