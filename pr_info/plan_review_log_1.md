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

## Round 2 — 2025-03-25

**Findings:**
- **Improvement I1:** Lazy import of `verify_mcp_servers` must be an explicit requirement, not conditional guidance; `verify_langchain` should also be lazy for environments without langchain
- **Improvement I2:** ~12 existing claude-provider tests need `resolve_mcp_config_path` mocked — recommend class-level autouse fixture instead of updating individually
- **Improvement I3:** Top-level `verify_langchain` import addressed by I1
- **Note N1:** `get_config_values` will also check env var via `_get_standard_env_var` — explicit check is fine for clarity
- **Note N2:** `_get_source_annotation` correctly shows env var source after step 1 mapping
- **Note N3:** Docs files should be verified to exist before implementation

**Decisions:**
- I1: Accept — make lazy imports a definitive requirement in step 3
- I2: Accept — recommend autouse fixture in step 3
- I3: Covered by I1
- N1-N3: No action needed

**User decisions:** None needed.

**Changes:**
- `step_3.md`: Replaced conditional import guidance with definitive lazy import requirement for both functions; replaced individual test mock note with autouse fixture recommendation

**Status:** Committed

## Round 3 — 2025-03-25

Verification pass. All round 1 and round 2 fixes confirmed correctly applied. No remaining issues.

**Status:** No changes needed

## Final Status

- **Rounds:** 3 (2 with changes, 1 verification)
- **Commits:** 2 (`6e43165`, `82a2a44`)
- **Plan status:** Ready for approval
- **Outstanding questions:** None
